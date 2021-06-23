# Proposal for implementing peeking over federation (peek API)

## Problem

Currently you can't peek over federation, as it was never designed or
implemented due to time constraints when peeking was originally added to Matrix
in 2016.

As well as stopping users from previewing rooms before joining, the fact that
servers can't participate in remote rooms without joining them first is
inconvenient in other ways:

 * You can't use rooms as generic pubsub mechanisms for synchronising data like
   profiles, groups, reputation lists, device-lists etc if you can't peek into
   them remotely.
 * Matrix-speaking search engines can't work if they can't peek remote rooms.

A related problem (not solved by this MSC) is that servers can't participate
in E2E encryption when peeking into a room, given the other users in the
room do not know to encrypt for the peeking device.

Another related problem (not solved by this MSC) is that invited users can't
reliably participate in E2E encryption before joining a room, given the invited
server doesn't currently have a way to know about new users/devices in the room
without peeking, and so doesn't tell them if the invited user's devices changes.
(https://github.com/vector-im/element-web/issues/2713#issuecomment-691480736
outlines a fix to this, not covered by this MSC).

## Solution

We let servers participate in peekable rooms (i.e. those with `world_readable`
`m.room.history_visibility`) without having actually joined them.

Firstly, this means that a number of federation endpoints should be updated to
allow inspection of `world_readable` rooms. This includes:

 * [`GET /_matrix/federation/v1/event_auth/{roomId}/{eventId}`](https://matrix.org/docs/spec/server_server/r0.1.4#get-matrix-federation-v1-event-auth-roomid-eventid)
 * [`GET /_matrix/federation/v1/backfill/{roomId}`](https://matrix.org/docs/spec/server_server/r0.1.4#get-matrix-federation-v1-backfill-roomid)
 * [`POST /_matrix/federation/v1/get_missing_events/{roomId}`](https://matrix.org/docs/spec/server_server/r0.1.4#post-matrix-federation-v1-get-missing-events-roomid)
 * [`GET /_matrix/federation/v1/state/{roomId}`](https://matrix.org/docs/spec/server_server/r0.1.4#get-matrix-federation-v1-state-roomid)
 * [`GET /_matrix/federation/v1/state_ids/{roomId}`](https://matrix.org/docs/spec/server_server/r0.1.4#get-matrix-federation-v1-state-ids-roomid)
 * [`GET /_matrix/federation/v1/event/{eventId}`](https://matrix.org/docs/spec/server_server/r0.1.4#get-matrix-federation-v1-event-eventid)

(Of course, these apis should only allow access to `world_readable` parts of
the history.)

Secondly, we introduce a new API allowing servers to subscribe to new events.

### Initiating a peek

To start peeking, firstly the peeking server must pick server(s) to peek
via. It can do this based on the `servers` parameter of the CS API `/peek`
command (from [MSC2753](https://github.com/matrix-org/matrix-doc/pull/2753)),
or failing that the domain of the room alias being peeked.

The peeking server then makes a `/peek` request to the target server. An
example request and response might look like:

```
PUT /_matrix/federation/v1/peek/{roomId}/{peekId}?ver=5&ver=6 HTTP/1.1
{}

200 OK
{
  "latest_event_state_ids": {
    "$fwd_extremity_1": [
        "$state_event_3",
        "$state_event_4"
    ],
    "$fwd_extremity_2": [
        "$state_event_5",
        "$state_event_6"
    ]
  },
  "common_state_ids": [
     "$state_event_1",
     "$state_event_2",
  ],
  "events": [
    {
      "type": "m.room.member",
      "room_id": "!somewhere:example.org",
      "content": { /* ... */ }
    }
  ],
  "renewal_interval": 3600000
}
```

The request takes an empty object as a body as a placeholder for future
extension.

The peeking server selects an ID for the peeking subscription for the purposes
of idempotency. The ID must be unique for a given `{ peeking_server, room_id,
target_server }` tuple, and should be a string consisting of the characters
`[0-9a-zA-Z.=_-]`. Its length must not exceed 8 characters and it should not be
empty.

The request takes `?ver=` querystring parameters with the same behaviour as
`/make_join` to advertise the room versions the peeking server supports.

If the request is successful, the target server retuns a 200 response with the
following fields:
 * `latest_event_state_ids`: a map whose keys are the IDs of the events forming
   the target server's current forward extremities in the room. The values are
   lists of the IDs of the events forming the room state after the event in
   question, excluding any events in `common_state_ids`.

   TBD: would the state *before* the extremity event be more useful?

 * `common_state_ids`: A list of the IDs of any events which are common to the room
   states after *all* of the forward extremities in the room.

 * `events`: The bodies of any events whose IDs are:
   * listed in the keys of `latest_event_state_ids`, or:
   * listed in the values of `latest_event_state_ids`, or:
   * listed in the values of `common_state_ids`, or:
   * listed in the `auth_events` field of any of the above events, or:
   * listed in the `auth_events` of the `auth_events`, recursively.

 * `renewal_interval`: a duration in milliseconds after which the target server
   will expire the peek. The peeking server must renew the peek before that
   time to be sure of continuing to receive events.

If the room is not peekable, the target server should return a 403 error with
 `M_FORBIDDEN`.

If the room is not known to the target server, it should return a 404 error
with `M_NOT_FOUND`.

If the peek ID is not valid, the target server responds with 400 and `M_UNRECOGNIZED`.

If the room version of the room being peeked isn't supported by the peeking
server, the target server responds with 400 and `M_INCOMPATIBLE_ROOM_VERSION`.

If the target server doesn't wish to honour the peek request due to server load
or rate-limiting, it may respond with 429 and `M_LIMIT_EXCEEDED`, including a
`retry_after_ms` value indicating when the request could be retried.

The room states returned by `/peek` should be validated just as the one
returned by the `/send_join` API. If the peeking server finds the response
unacceptable, it should cancel the peek with a `DELETE` request (see below).

XXX: it might be better to split this into two operations: first fetch the
state data, then begin the peek operation by sending your idea of the forward
extremities, to bring you up to date with anything you missed. This would
reduce the chance of having to immediately cancel a peek, and would be more
efficient in the case of rapid `peek-unpeek-peek` switches.

While a peek subscription is active, the target server must relay any events
received in that room over the [`PUT
/_matrix/federation/v1/send/{txnId}`](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v1-send-txnid)
API. If a peeking server has multiple peeks active for a given room and target
server, the target server should still only send one copy of each event, rather
than duplicating the event for each peek.

### Renewing a peek

The target server will eventually expire a peek if it is not renewed. The
peeking server can renew a peek by calling `POST
/_matrix/federation/v1/peek/{roomId}/{peekId}/renew`:

```
POST /_matrix/federation/v1/peek/{roomId}/{peekId}/renew HTTP/1.1
{}

200 OK
{
  "renewal_interval": 3600000
}
```

The target server simply returns the new `renewal_interval`.

If the peek ID is not known for the `{ peeking_server, room_id, target_server }`
tuple, the target server returns a 404 error with `M_NOT_FOUND`.

### Deleting a peek

The peeking server may terminate a peek by calling `DELETE
/_matrix/federation/v1/peek/{roomId}/{peekId}`:

```
DELETE /_matrix/federation/v1/peek/{roomId}/{peekId} HTTP/1.1
Content-Length: 0

200 OK
{}
```

The request has no body <sup id="a1">[1](#f1)</sup>. On success, the target
server returns a 200 with an empty json object.

If the peek ID is not known for the `{ peeking_server, room_id, target_server }`
tuple, the target server returns a 404 error with `M_NOT_FOUND`.

### Expiring a peek

The target server should expire any peek which is not renewed before the
`renewal_interval` elapses.

It should indicate the expiry to the peeking server via `PUT
/_matrix/federation/v1/send/`, via a new `expired_peeks` key:

```
PUT /_matrix/federation/v1/send/S0meTransacti0nId HTTP/1.1

{
  "expired_peeks": [
    {
      "room_id": "{roomId}",
      "peek_id": "{peekId}"
    }
  ]
}
```

### Joining a room

When the user joins the peeked room, the peeking server should just emit the
right membership event rather than calling `/make_join` or `/send_join`, to
avoid the unnecessary burden of a full room join, given the server is already
participating in the room.  It should also send a `DELETE` request to cancel
any active peeks.

### Encrypted rooms

It is considered a feature that you cannot peek into encrypted rooms, given
the act of peeking would leak the identity of the peeker to the joined users
in the room (as they'd need to encrypt for the peeker).  This also feels
acceptable given there is little point in encrypting something intended to be
world-readable.

## Alternatives

 * simply use `room_id` for idempotency rather than requiring a separate
   `peek_id`. One reason not to do this is to allow a future extension where
   there are multiple subscriptions active, each filtering out different event
   types. Another reason that `peek_id` is useful is to improve idempotency
   with rapid peek/unpeek/peek cycles, to ensure we aren't `DELETE`ing the
   wrong peek.

 * An earlier rejected solution is
   [MSC1777](https://github.com/matrix-org/matrix-doc/pull/1777), which
   proposed joining a pseudouser (`@:server`) to a room in order to peek into
   it. However:

   * being forced to write to a room DAG (by joining such a user) in order to
     perform a read-only operation (peeking) is somewhat inefficient.

   * it also constitutes a privacy violation - tantamount to a tracking
     pixel. If I'm on a smallish server and I happen to briefly peek into
     `#nsfw:matrix.org`, I don't want every random server in that room to know
     that I did so. It's even worse than sending read-receipts.

   * In the interests of empowering the user, it's actually quite nice to
     (theoretically at least) have some control over which servers you trust to
     peek via.

   * That said, a P2P world is going to need a totally different approach,
     which might be back towards MSC1777 but using
     [MSC1228](https://github.com/matrix-org/matrix-doc/pull/1228)-style IDs to
     protect privacy. We need to solve scalability of "which nodes are
     participating in the room" irrespectively of whether those nodes are
     active or passive. So it's worth noting this solution (MSC2444) is very
     much for today's federated architecture.

   * MSC1777 offers a solution for EDU transmission which this MSC does not,
     given we don't currently have any data flows for mirroring other servers'
     EDUs.

 * Rather than attempting to maintain a local replica of peeked traffic, have
   the peeking server proxy any peek requests from the client-server API onto
   the target server, somehow.  This couples room availability to the peeked
   server and means we don't have a local replica we can index or serve
   independently etc - and also means you could have problems deduplicating
   peeks between local clients.

## Future extensions

These features are explicitly descoped for the purposes of this MSC.

 * It may be useful to allow peeking servers to "filter" the events to be
   returned - for example, if you only care about particular events, or
   particular servers - e.g. if load-balancing peeking via multiple servers.

   It's worth noting that this would make it very hard for peeking servers to
   reliably track state changes and detect missing events.

## Security considerations

 * A malicious server could set up multiple peeks to multiple target servers by
   way of attempting a denial-of-service attack. Server implementations should
   rate-limit requests to establish peeks, as well as limiting the absolute
   number of active peeks each server may have, to mitigate this.

 * The peeked server becomes a centralisation point which could conspire
   against the peeking server to withhold events.  This is not that dissimilar
   to trying to join a room via a malicious server, however, and can be
   mitigated somewhat if the peeking server tries to query missing events from
   other servers.  The peeking server could also peek to multiple servers for
   resilience against this sort of attack.

 * The peeked server will be able to track the metadata surrounding which
   servers are peeking into which of its rooms, and when.  This could be
   particularly sensitive for single-person servers peeking at profile rooms.

## Design considerations

This doesn't solve the problem that rooms wink out of existence when all
participants leave (https://github.com/matrix-org/matrix-doc/issues/534),
unlike other approaches to peeking (e.g. MSC1777).

How do we handle backpressure or rate limiting on the event stream (if at
all?)

## Dependencies

This unblocks [MSC1769](https://github.com/matrix-org/matrix-doc/pull/1769)
(profiles as rooms) and
[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) (Matrix Spaces),
and is required for
[MSC2753](https://github.com/matrix-org/matrix-doc/pull/2753) (peeking via
/sync) to be of any use.

This would close https://github.com/matrix-org/matrix-doc/issues/913.

## Footnotes

<a id="f1"/>[1]: per
https://www.ietf.org/archive/id/draft-ietf-httpbis-semantics-12.html#name-delete:
"A client SHOULD NOT generate a body in a DELETE request."  [↩](#a1)
