# Proposal for a federation capabilities API

Although there's no server-side need for a capabilities at this time (even in this
proposal), it is desirable for clients to know the room version(s) that other servers
in a given room support prior to performing an upgrade. This proposal lays a foundation
for future capabilities work at the federation level while also giving clients a bit
more information for their room ugprade experience.

Users are already eager to upgrade their rooms despite the Matrix specification and
reference homeserver not advertising an upgrade being required. A common question
raised by room administrators/moderators is "does everyone in the room support version
X rooms?". Answering that question involves running a script to get all the room members,
splitting out the server name, then querying the federation `/version` endpoint to
get the server version. From there, runners of the script would have to know or look
up what versions of what software supports the room version they want to upgrade to.
Instead, clients could just present this information directly in the form of "42% of
users in this room are on servers supporting room version X".


## Proposal

This proposal has two parts: a federation capabilities API, and a way for clients to
query it.

#### Federation capabilities API

Endpoint: `GET /_matrix/federation/v1/capabilities`

This endpoint has the exact same semantics, structure, and restrictions as the
[client-server capabilities](https://matrix.org/docs/spec/client_server/r0.5.0#capabilities-negotiation)
specification. The only capability proposed for this federation endpoint is an
exact copy of the client-server's `m.room_versions` capability.

As with most federation endpoints, servers MUST authenticate their request by signing
it for this endpoint.

Example response:
```json
{
    "m.room_versions": {
        "default": "4",
        "available": {
            "1": "stable",
            "2": "stable",
            "3": "stable",
            "4": "stable",
            "5": "stable",
            "com.example.test": "unstable"
        }
    }
}
```

Servers SHOULD cache the results for up to 24 hours or the `max-age` of the
`Cache-Control` response header (if present), whichever is lesser. Servers SHOULD
rate limit this endpoint.


#### Client-server endpoints for querying federation capabilities

New endpoints:
* `GET /_matrix/client/r0/rooms/<room_id>/capabilities`
* `GET /_matrix/client/r0/rooms/<room_id>/capabilities/<federation_capability>`

`<room_id>` is the room ID to query servers in and `<federation_capability>` is the
capability to query for all servers in the room. As per above, the only capability
supported by this proposal would be `m.room_versions`.

Both endpoints query the capabilties of joined servers in the room (including the
requesting user's own server), returning an object which maps server hostname to
an object.

Example `/capabilities` response:
```json
{
    "one.example.org": {
        "m.room_versions": {
            "default": "4",
            "available": {
                "1": "stable",
                "2": "stable",
                "3": "stable",
                "4": "stable",
                "5": "stable",
                "com.example.test": "unstable"
            }
        }
    },
    "two.example.org": {
        "m.room_versions": {
            "default": "1",
            "available": {
                "1": "stable",
                "5": "stable"
            }
        },
        "com.example.test_capability": {
            "hello": "world"
        }
    }
}
```

Example `/capabilities/<federation_capability>` response:
```json
{
    "one.example.org": {
        "default": "4",
        "available": {
            "1": "stable",
            "2": "stable",
            "3": "stable",
            "4": "stable",
            "5": "stable",
            "com.example.test": "unstable"
        }
    },
    "two.example.org": {
        "default": "1",
        "available": {
            "1": "stable",
            "5": "stable"
        }
    }
}
```

Note how the more specific endpoint does not include the redundant capability type
in its response.

Clients are responsible for matching up users to hostnames, if needed.

The rationale for scoping these endpoints to a room rather than using parameters
to list servers to query is that in a lazy-loaded world the client may not be fully
aware of all the servers in the room. The homeserver on the other hand would be aware
of all the servers in the room, and have a high-performance cache for that information,
therefore putting the responsibility on the homeserver seems wise.

Servers SHOULD rate limit these endpoints aggressively, particularly if they are not
caching the responses.

Servers which fail to respond or do not list the requested capability should be recorded
as empty objects in the responses. Clients MUST interpret this however the capability
asks to be interpretted. In the case of `m.room_versions`, lack of the capability being
advertised means the server should be assumed to support room version 1 as the only
default and stable version.


## Potential issues

Querying a room with lots of servers in it could result in a large number of outbound
requests. As per above, servers are expected to employ rate limiting and caching to
avoid the impact being significant. Additionally, clients should not expect the endpoints
to be quick as remote servers may take some time to respond.
