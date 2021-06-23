# MSC2716: Incrementally importing history into existing rooms

## Problem

Matrix has historically been unable to easily import existing history into a
room that already exists. This is a major problem when bridging existing
conversations into Matrix, particularly if the scrollback is being
incrementally or lazily imported.

For instance, an NNTP bridge might work by letting a user join a room that
maps to a given newsgroup, first showing an empty room, and then importing the
most recent 1000 newsgroup posts for that room to flesh out some history.  The
bridge might then choose to slowly import additional posts for that newsgroup
in the background, until however many decades of backfill were complete.
Finally, as more archives surface, they might also need to be manually
gradually added into the history of the room - slowly building up the complete
history of the conversations over time.

This is currently not supported because:
 * There is no way to set historical room state in a room via the CS or AS API -
   you can only edit current room state.
 * There is no way to create messages in the context of historical room state in
   a room via CS or AS API - you can only create events relative to current room
   state.
 * There is currently no way to override the timestamp on an event via the AS API.
   (We used to have the concept of [timestamp
   massaging](https://matrix.org/docs/spec/application_service/r0.1.2#timestamp-massaging),
   but it never got properly specified)

## Proposal

 1. We let the AS API override the prev_event(s) of an event when injecting it into
    the room, thus letting bridges consciously specify the topological ordering of
    the room DAG.  We do this by adding a `prev_event` querystring parameter on the
    `PUT /_matrix/client/r0/rooms/{roomId}/send/{eventType}/{txnId}` and
    `PUT /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}` endpoints.
    The `prev_event` parameter can be repeated multiple times to specify multiple parent
    event IDs of the event being submitted.  An event must not have more than 20 prev_events.
    If a `prev_event` parameter is not presented, the server assumes the event is being
    appended to the current timeline and calculates the prev_events as normal.  If an
    unrecognised event ID is specified as a `prev_event`, the request fails with a 404.

 2. We also let the AS API override ('massage') the `origin_server_ts` timestamp applied
    to sent events.  We do this by adding a `ts` querystring parameter on the
    `PUT /_matrix/client/r0/rooms/{roomId}/send/{eventType}/{txnId}` and
    `PUT /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}`endpoints, specifying
    the value to apply to `origin_server_ts` on the event (UNIX epoch milliseconds).

 3. Finally, we can add a optional `"m.historical": true` field to events to
    indicate that they are historical at the point of being added to a room, and
    as such servers should not serve them to clients via the CS `/sync` API -
    instead preferring clients to discover them by paginating scrollback via
    `/messages`.

This lets history be injected at the right place topologically in the room.  For instance, different eras of the room could
end up as branches off the original `m.room.create` event, each first setting up the contextual room state for that era before
the block of imported history.  So, you could end up with something like this:

```
m.room.create
     |\
     | \___________________________________
     |            \                        \
     |             \                        \
live timeline    previous 1000 messages   another block of ancient history
```

We consciously don't support the new `parent` and `ts` parameters on the
various helper syntactic-sugar APIs like `/kick` and `/ban`.  If a bridge/bot is
smart enough to be faking history, it is already in the business of dealing
with raw events, and should not be using the syntactic sugar APIs.

## Potential issues

There are a bunch of security considerations here - see below.

This doesn't provide a way for a HS to tell an AS that a client has tried to call
/messages beyond the beginning of a room, and that the AS should try to
lazy-insert some more messages (as per https://github.com/matrix-org/matrix-doc/issues/698).
For this MSC to be properly useful, we might want to flesh that out.

## Alternatives

We could insist that we use the SS API to import history history in this manner rather than
extending the AS API.  However, it seems unnecessarily burdensome to make bridge authors
understand the SS API, especially when we already have so many AS API bridges.  Hence these
minor extensions to the existing AS API.

Another way of doing this might be to store the different eras of the room as
different versions of the room, using `m.room.tombstone` events to form a
linked list of the eras. This has the advantage of isolating room state
between different eras of the room, simplifying state resolution calculations
and avoiding risk of any cross-talk.  It's also easier to reason about, and
avoids exposing the DAG to bridge developers.  However, it would require
better presentation of room versions in clients, and it would require support
for retrospectively specifying the `predecessor` of the current room when you
retrospectively import history.  Currently `predecessor` is in the immutable
`m.room.create` event of a room, so cannot be changed retrospectively - and
doing so in a safe and race-free manner sounds Hard.

Another way could be to let the server who issued the m.room.create also go
and retrospectively insert events into the room outside the context of the DAG
(i.e. without parent prev_events or signatures).  To quote the original
[bug](https://github.com/matrix-org/matrix-doc/issues/698#issuecomment-259478116):

> You could just create synthetic events which look like normal DAG events but
  exist before the m.room.create event. Their signatures and prev-events would
  all be missing, but they would be blindly trusted based on the HS who is
  allowed to serve them (based on metadata in the m.room.create event). Thus
  you'd have a perimeter in the DAG beyond which events are no longer
  decentralised or signed, but are blindly trusted to let HSes insert ancient
  history provided by ASes.

However, this feels needlessly complicated if the DAG approach is sufficient.

## Security considerations

This allows an AS to tie the room DAG in knots by specifying inappropriate
event IDs as parents, potentially DoSing the state resolution algorithm, or
triggering undesired state resolution results. This is already possible by the
SS API today however, and given AS API requires the homeserver admin to
explicitly authorise the AS in question, this doesn't feel too bad.

This also makes it much easier for an AS to maliciously spoof history.  This
is a bit unavoidable given the nature of the feature, and is also possible
today via SS API.

If the state changes from under us due to importing history, we have no way to
tell the client about it.  This is an [existing
bug](https://github.com/matrix-org/synapse/issues/4508) that can be triggered
today by SS API traffic, so is orthogonal to this proposal.

## Unstable prefix

Feels unnecessary.
