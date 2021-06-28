# MSC2787: Portable Identities

## Background

This is an evolution of [MSC1228](https://github.com/matrix-org/matrix-doc/pull/1228) 
which aims to make it simpler to implement portable identities and decentralised
accounts.

It is still a work-in-progress—some things that need attention include:

- How to handle multiple homeservers joining the same room, since they will have
  their own membership events, and clients may wish to disambiguate these;
- How to handle invites, given that you won't know a UDK until after the user has
  joined the room;
- How to adequately disconnect UDKs from UPKs as a part of a data removal request
  for GDPR compliance;
- Whether UPKs should really be a "one true identity" for a user or whether a user
  may actually have multiple UPKs if they want;
- How to handle device list syncing and send-to-device messages;
- The extent to which users should be involved in attesting MXID-to-UPK mappings.

## Goals

The goals of this proposal are:

- To enable account portability by breaking the link between a user identity and a
  specific homeserver;
- To allow breaking the link between delegated and permanent user identities at a
  later date, e.g. as a part of a data deletion request;
- To allow a user to grant permission to one or more homeservers to act on behalf of
  the user in a given room, e.g. allowing them to creating and sign events from a
  user;
- To remove the need for servers to have a single static signing key, as they do
  today.

## Proposal

This proposal includes specifications to:

- To give a user a single cryptographic User Permanent Key (herein referred to as
  a "UPK"), which they will use as part of a cryptographic challenge login;
- To give a server a set of User Delegated Keys (herein referred to as a "UDK"),
  which will represent servers acting on behalf of users within rooms;
- To allow users to attest one or more UDKs using their UPK;
- To remove Matrix IDs (MXIDs) and server names from events, similar to MSC1228;
- To allow a user to receive one or more server-provided MXIDs mapped to a UPK.

### User Permanent Key (UPK)

The UPK is an ed25519 public key which represents a user entity. The initial
intention is that a user will use this UPK to perform a challenge-response login
to a homeserver and that it will become their "one true identity".

Central to this design is that the UPKs are user-owned and therefore the private
key portion to each UPK is held by the user, although they could be protected with
a passphrase and backed up to key storage on one or more homeservers if needed.

The UPK private portion must not be decrypted nor used serverside.

#### UPK Format

The UDK is prefixed with a version byte, then URL-safe base64-encoded, and then
prefixed with the `~` sigil. The version byte for ed25519 is `0x01`.

### User Delegated Key (UDK)

Homeservers create a new UDK, which is an ed25519 key, on behalf of each user in
each room. These keys are generated and stored by the server when a user joins a
room:

1. The user requests to join a room;
2. The server generates a UDK and sends the public key to the client;
3. The client signs a UDK attestation using a UPK - this forms the link between
   the UDK and the UPK;
4. The server generates the membership event, including the attestation, and sends
   it into the room/to federated servers, signed using the new UDK.

The homeserver should store all active UPK-UDK links.

#### UDK Format

The UDK is prefixed with a version byte, then URL-safe base64-encoded, and then
prefixed with the `^` sigil. The version byte for ed25519 is `0x01`.

### Membership UDK Attestation

An attestation will include the UDK that is being attested to, and an expiry time. The
attestation will be valid for events up until the expiry time, at which point a new
attestation will be required.

The attestation `"content"` is built by the client, and then is signed with the UPK
before being sent to the server. The attested server will then add its own signature
using the UDK.

The completed attestation will take a format similar to this:

```
"attestation": {
    "content": {
        "identity": ~upk_that_is_attesting",
        "delegate": "^udk_that_is_being_attested",
        "server_name": "example.com",
        "expires": 15895491111111
    },
    "signatures": {
        "~upk_that_is_attesting": {
            "ed25519": "upk_signature"
        },
        "~udk_that_is_being_attested": {
            "ed25519": "udk_signature"
        }
    }
}
```

The attestation contains a `"server_name"` field which contains the name of the server
that manages the UDK. This is necessary as, without this, other servers in the room
will not be able to work out where to route messages for this UDK.

The attestation `"content"` key will then be canonicalised and signed, once by the UPK
and then once by the homeserver that issued the UDK.

#### Validity

The attestation will be valid from the point that it is sent (in effect, from the
`"origin_server_ts"` timestamp) up until the `"expires"` timestamp.

Since there may be multiple membership state events with renewals over time, event
validity is based on the attestation in the room state at (before) the event. If the attestation has expired in the room state at (before) the event, the attestation is
considered invalid - newer attestations must not be considered when determining the
validity period.

#### Authorisation rules

Events will continue to refer to the membership event as an auth event, with the
main difference being that the referred-to membership event will now contain one or
more attestations.

Authorisation rules will be updated to include extra clauses, that events should
only be accepted for a specific UDK as long as there is:

1. A valid attestation for the UDK in the referred membership event;
2. The event falls inclusive of the `"origin_server_ts"` and the `"expires"` of
   the attestation;
3. An `m.room.member` event with an `"attestation"` section must contain a signature
   from the UPK.

To cover the possibility of an attestation not being renewed, soft-fail rules will
be updated to include extra clauses, that events should be soft-failed when received as
new events unless there is:

1. A valid attestation for the UDK in the current room state;
2. The event falls before the `"expires"` timestamp of the attestation.

This prevents servers from continuing to impersonate the user with new events after
the attestation has expired - necessary as the server owns and maintains the UDK
keypair.

Some thought needs to be given on how to ban a UPK so that generating new UDKs is not
an effective measure for evading bans.

### Membership event format

A membership event including an attestation may look something like this:

```
{
    "auth_events": [ ... ],
    "prev_events": [ ... ],
    "content": {
        "avatar_url": "mxc://here/is/neilalexander.png",
        "displayname": "neilalexander",
        "membership": "join",
        "attestation": {
            "content": {
                "identity": ~upk_that_is_attesting",
                "delegate": "^udk_that_is_being_attested",
                "server_name": "example.com",
                "expires": 15895491111111
            },
            "signatures": {
                "~upk_that_is_attesting": {
                    "ed25519": "upk_signature"
                },
                "~udk_that_is_being_attested": {
                    "ed25519": "udk_signature"
                }
            }
        }
    },
    "origin_server_ts": 1589549295296,
    "sender": "^udk_that_is_being_attested",
    "signatures": {
        "^udk_that_is_being_attested": ...
    },
    "hashes": {
        "sha256": ...,
    }
    "state_key": "^udk_that_is_being_attested",
    "type": "m.room.member",
    "unsigned": {
        "age": 25,
    },
    "event_id": "$eventid",
    "room_id": "!roomid"
}
```

Note that there is no MXID in the `"sender"` and `"state_key"` fields, nor in the
`"signatures"` field of the event itself - these are now referencing the UPKs.

Multiple servers wanting to join on behalf of the same user should send their own
membership events, each with an attestation as created and signed by the user.
There may be a need for clients to disambiguate users.

### Timeline event format

Otherwise, the event format remains unchanged, with only one exception: that the
`"signatures"` contains the signature from the UDK, rather than from the server
itself as today:

```
{
    "auth_events": [ ... ],
    "prev_events": [ ... ],
    "content": {
        "body": "Hi!",
        "msgtype": "m.text"
    },
    "origin_server_ts": 1589549295384,
    "sender": "^udk_that_is_being_attested",
    "signatures": {
        "^udk_that_is_being_attested": ...
    },
    "hashes": {
        "sha256": ...,
    }
    "type": "m.room.message",
    "unsigned": {
        "age": 26,
    },
    "event_id": "$eventid",
    "room_id": "!roomid"
}
```

#### Renewing an attestation

At any time, the UPK holder can issue new attestations by sending updated membership
state events with a new attestation. This can be done either before or after the
validity of the previous attestation has expired.

The previous membership event with the previous attestation must appear in the
`auth_events` of the new membership event with the new attestation.

#### Removing an attestation

To remove an attestation, the membership event should be replaced with a new
membership event that no longer includes an attestation.

Assuming there is no need to remove evidence of the attestations ever existing,
then this will be sufficient. The previously attested servers will no longer be able
to send events into the room on behalf of the user.

#### Redacting an attestation

To satisfy data deletion requests, or where it may be important to fully remove links
between UDKs and UPKs for legal compliance, it should be possible to redact the
membership events to remove the `"attestation"` section from them.

This may need to be done recursively, following the `"auth_events"`, to remove all
historical attestations too.

TODO: Doing this may mean that other servers that try to backfill may not be able to
verify that the events were allowed to be sent?

As the redaction algorithms already have rules for `m.room.member` events which will
preserve the `"membership"` key, it should be possible to redact any other personally
identifiable information such as the `"attestation"`, the `"display_name"` or the
`"avatar_url"` without issue.

The UDK signature will remain in the event, but without the attestation, it will not
be possible to link it to a UPK.

### Matrix ID to UPK mapping

Public keys as identifiers may enable some portability but they aren't user-friendly
and somewhat difficult to put on a business card. For this, it is necessary to be
able to allow users to maintain MXID mappings much as they have today.

However, a homeserver returning a UPK for an MXID should ideally imply that the server
actually has some kind of association with the user and that the user is resident,
rather than third-party servers gratuitously providing MXID mappings for users that
they may not otherwise be aware of.

### User signalling

For things like invites, direct messages etc, it is not possible to know what the UDK
will be before a homeserver generates one to join the room. Therefore these endpoints
should be updated to use either:

- A UPK in combination with a previously-known resident server name;
- A MXID, from which a response will contain the UPK and a resident server name.

In these instances, you are addressing "the user" rather than a UDK.

### Invites

TODO.

### Device list syncing

TODO.

### Send-to-device

TODO.
