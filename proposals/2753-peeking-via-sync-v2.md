# MSC2753: Peeking via Sync (Take 2)

## Problem

[Room previews](https://matrix.org/docs/spec/client_server/r0.6.1#id116), more
commonly known as "peeking", has a number of usecases, such as:

 * Look at a room before joining it, to preview it.
 * Look at a user's profile room (see
   [MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769)).
 * Browse the metadata or membership of a space (see
   [MSC1772](https://github.com/matrix-org/matrix-doc/issues/1772)).
 * Monitor [moderation policy lists](https://matrix.org/docs/spec/client_server/r0.6.1#moderation-policy-lists).

Currently, peeking relies on the deprecated v1 `/initialSync` and `/events`
APIs.

This poses the following issues:

 * Servers and clients must implement two separate sets of event-syncing logic,
   doubling complexity.
 * Peeking a room involves setting a stream of long-lived `/events` requests
   going. Having multiple streams is racey, competes for resources with the
   `/sync` stream, and doesn't scale given each room requires a new `/events`
   stream.
 * `/initialSync` and `/events` are deprecated and not implemented on new
   servers.

This proposal suggests a new API in which events in peeked rooms would be
returned over `/sync`.

## Proposal

Peeking into a room remains per-device: if the user has multiple devices, each
of which wants to peek into a given room, then each device must make a separate
request.

To help avoid situations where clients create peek requests and forget about
them, each peek request is given a lifetime by the server. The client must
*renew* the peek request before this lifetime expires. The server is free to
pick any lifetime.

### Starting a peek

We add an CS API called `/peek`, which starts peeking into a given
room. This is similar to
[`/join/{roomIdOrAlias}`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-join-roomidoralias)
but has a slightly different API shape.

For example:

```
POST /_matrix/client/r0/peek/{roomIdOrAlias} HTTP/1.1

{
    "servers": [
        "server1", "server2"
    ]
}
```

A successful response has the following format:

```
{
    "room_id": "<resolved room id>",
    "peek_expiry_ts": 1605534210000
}
```

The `servers` parameter is optional and, if present, gives a list of servers to
try to peek through.

XXX: should we limit this API to room IDs, and require clients to do a `GET
/_matrix/client/r0/directory/room/{roomAlias}` request if they have a room
alias? (In which case, `/_matrix/client/r0/room/{room_id}/peek` might be a
better name for it.)  On the one hand: cleaner, simpler API. On the other: more
requests needed for each operation.

Both `room_id` and `peek_expiry_ts` are required in the
response. `peek_expiry_ts` gives a timestamp (milliseconds since the unix
epoch) when the server will *expire* the peek if the client does not renew it.

The server ratelimit requests to `/peek` and returns a 429 error with
`M_LIMIT_EXCEEDED` if the limit is exceeded.

Otherwise, the server first resolves the given room alias to a room ID, if
needed.

If there is already an active peek for the room in question, it is renewed and
a successful response is returned with the updated `peek_expiry_ts`.

If the user is already *joined* to the room in question, the server returns a
400 error with `M_BAD_STATE`.

If the room in question does not exist, the server returns a 404 error with
`M_NOT_FOUND`.

If the room does not allow peeking (ie, it does not have `history_visibility`
of `world_readable` <sup id="a1">[1](#f1)</sup>), the server returns a 403
error with `M_FORBIDDEN`.

Otherwise, the server starts a peek for the calling device into the given room,
and returns a 200 response as above.

When a peek first starts, the current state of the room is returned in the
`peek` section of the next `/sync` response.

### Stopping a peek

To stop peeking, the client calls `rooms/<id>/unpeek`:

```
POST /_matrix/client/r0/rooms/{room_id}/unpeek HTTP/1.1

{}
```

The body must be a JSON dictionary, but no parameters are specified.

A successful response has an empty body.

If the room is unknown or was not previously being peeked the server returns a
400 error with `M_BAD_STATE`.

### `/sync` response

We add a new `peek` section to the `rooms` field of the `/sync`
response. `peek` has the same shape as `join`.

While a peek into a given room is active, any new events in the room cause that
room to be included in the `peek` section (but only for the device with the
active peek). When a peek first starts, the entire state of the room is
included in the same way as when a room is first joined.

If the client requests lazy-loading via `lazy_load_members`, then redundant
membership events are excluded in the same way as they are for joined rooms.

If a user subsequently `/join`s a room they are peeking, the room will
thenceforth appear in the `join` section instead of `peek`. For devices which
were already peeking into the room, the server should *not* include the entire
room state for the room in the `/sync` response, allowing the client to build
on the state and history it has already received without re-sending it down
`/sync`.

When a room stops being peeked (either because the client called `/unpeek` or
because the server timed out the peek), the room will be included in the
`leave` section of the `/sync` response, including any events that occured
between the previous `/sync` and the the peek ending. If there are no such
events, the room's entry in the `leave` section will be empty.

For example:

```js
{
  "rooms": {
    "join": { /* ... */ },
    "leave": {
      "!unpeeked:example.org": {
        "timeline": {
          "events": [
            { "type": "m.room.message", "content": {"body": "just one more thing"}}
          ]
        }
      },
      "!alsounpeeked:example.com": {}
    }
  }
}
```

## Encrypted rooms

(this para taken from MSC #2444):

It is considered a feature that you cannot peek into encrypted rooms, given
the act of peeking would leak the identity of the peeker to the joined users
in the room (as they'd need to encrypt for the peeker). This also feels
acceptable given there is little point in encrypting something intended to be
world-readable.

## Future extensions

 * "snapshot" API, for a one-time peek operation which returns the current
   state of the room without adding the room to future `/sync` responses. Might
   be useful for certain usecases (eg, looking at a user's public profile)?

 * "bulk peek" API, for peeking into many rooms at once. Might be useful for
   flair (which requires peeking into lots of users' profile rooms), though
   realistically that usecase will need server-side support.

 * "cross-device" peeks could be useful for microblogging etc?

## Potential issues

 * Expiring peeks might be hard for clients to manage?

## Alternatives

### Keep /peek closer to /join

Given that peeking has parallels to joining, it might be preferable to keep the
API closer to `/join`. On the other hand, they probabably aren't actually
similar enough to make it worth propagating the oddities of `/join` (in
particular, the use of query-parameters
([matrix-doc#2864](https://github.com/matrix-org/matrix-doc/issues/2864)).

### Filter-based API

[MSC1776](https://github.com/matrix-org/matrix-doc/pull/1776) defined an
alternative approach, where you could use filters to add peeked rooms into a
given `/sync` response as needed.  This however had some issues:

 * You can't specify what servers to peek remote rooms via.
 * You can't identify rooms via alias, only ID
 * It feels hacky to bodge peeked rooms into the `join` block of a given
   `/sync` response
 * Fiddling around with custom filters feels clunky relative to just calling a
   `/peek` endpoint similar to `/join`.

### Use the `join` block

It could be seen as controversial to add another new block to the `/sync`
response.  We could use the existing `join` block, but:

 * it's a misnomer (given the user hasn't joined the rooms)
 * `join` refers to rooms which the *user* is in, rather than that they are
   peeking into using a given *device*
 * we risk breaking clients who aren't aware of the new style of peeking.
 * there's already a precedent for per-device blocks in the sync response (for
   to-device messages)

### Per-account peeks

It could be seen as controversial to make peeking a per-device rather than
per-user feature.  When thinking through use cases for peeking, however:

 1. Peeking a chatroom before joining it is the common case, and is definitely
    per-device - you would not expect peeked rooms to randomly pop up on other
    devices, or consume their bandwidth.
 2. [MSC1769](https://github.com/matrix-org/matrix-doc/pull/1769) (Profiles as
    rooms) is also per device: if a given client wants to look at the Member
    Info for a given user in a room, it shouldn't pollute the others with that
    data.
 3. [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) (Groups as
    rooms) uses room joins to indicate your own membership, and peeks to query
    the group membership of other users.  Similarly to profiles, it's not clear
    that this should be per-user rather than per-device (and worse case, it's a
    matter of effectively opting in rather than trying to filter out peeks you
    don't care about).

### Alternatives to expiring peeks

Having servers expire peek requests could be fiddly, so we considered a number
of alternatives:

 * Allow peeks to stack up without limit and trust that clients will not forget
   about them: after all, it is in clients' best interest not to leak
   resources, to reduce the amount of data to be handled, and it is not obvious
   that leaking peeks is easier than leaking joins.

   Ultimately this does not align with our experience of administering
   `matrix.org`: it seems that where a resource *can* be leaked, it ultimately
   will be, and it is better to design the API to prevent it.

 * Limit the number of peeks that can be active at once, to force clients to be
   fastidious in their peek cleanups. However, it is hard to see what a good
   limit would be. Furthermore: peeks could be lost through no fault of the
   client (for example: when a `/peek` request succeeds but the client
   does not receive the response), and these leaked peaks could stack up until
   peeking becomes inoperative.

 * Automatically clear active peeks when a `/sync` request is made without a
   `since` parameter. However, this feels like magic at a distance, and also
   means that if you initial-sync separately (e.g. you stole an access token
   from the DB to manually debug something) then existing clients will be
   broken.

 * Have the client resubmit the list of active peeks every time it wants to add
   or remove one. This could amount to a sigificant quantity of data.

## Security considerations

Servers should ratelimit calls to `/peek` to stop someone DoSing the
server.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during
development:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`/_matrix/client/r0/peek` | API endpoint | `/_matrix/client/unstable/org.matrix.msc2753/peek`
`/_matrix/client/r0/rooms/{roomId}/unpeek` | API endpoint | `/_matrix/client/unstable/org.matrix.msc2753/rooms/{roomId}/unpeek`

## Footnotes

<a id="f1"/>[1]: `join_rules` do not affect peekability - it's
possible to have an invite-only room which joe public can still peek into, if
`history_visibility` has been set to `world_readable`.[↩](#a1)
