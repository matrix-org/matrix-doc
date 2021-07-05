# MSC2675: Serverside aggregations of message relationships

It's common to want to send events in Matrix which relate to existing events -
for instance, reactions, edits and even replies/threads.

Clients typically need to track the related events alongside the original
event they relate to, in order to correctly display them.  For instance,
reaction events need to be aggregated together by summing and be shown next to
the event they react to; edits need to be aggregated together by replacing the
original event and subsequent edits; replies need to be indented after the
message they respond to, etc.

It is possible to treat relations as normal events and aggregate them
clientside, but to do so comprehensively could be very resource intensive, as
the client would need to spider all possible events in a room to find
relationships and maintain an correct view.

Instead, this proposal seeks to solve this problem by defining APIs to let the
server calculate the aggregations on behalf of the client, and so bundle the
related events with the original event where appropriate.

This proposal is one in a series of proposals that defines a mechanism for
events to relate to each other.  Together, these proposals replace
[MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849).

* [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) defines a
  standard shape for indicating events which relate to other events.
* This proposal defines APIs to let the server calculate the aggregations on
  behalf of the client, and so bundle the related events with the original
  event where appropriate.
* [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676) defines how
  users can edit messages using this mechanism.
* [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) defines how
  users can annotate events, such as reacting to events with emoji, using this
  mechanism.

## Proposal

### Receiving relations

#### Unbundled relation events

Relations are received during non-gappy incremental syncs (that is, syncs
called with a `since` token, and that have `limited: false` in the portion of
response for the given room) as normal discrete Matrix events.  These are
called "unbundled relation events".

#### Bundled relations

Other than during non-gappy incremental syncs, an aggregate view of relation
events should be bundled into the unsigned data of the event they relate to,
rather than sending un-bundled individual relation events.  This is called a
bundled relation (or bundled aggregation), and by sending a summary of the
aggregations, avoids us having to always send lots of individual unbundled
relation events individually to the client.

Any API which receives events should bundle relations (apart from non-gappy
incremental syncs), for instance: initial sync, gappy incremental sync,
/messages and /context.

The bundled relations are grouped according to their `rel_type`, and then
paginated within each group using Matrix's defined pagination idiom of `count`,
`limited` and `chunk` fields - respectively giving the total number of
elements in the list, whether that list has been truncated, and an array of
elements in the list.

The format of the aggregated value in the bundle depends on the relation type.

`m.reference` list the `event_id` and event `type` of the events which
reference that event.

The formats for other relation types may be defined in the proposals that
define the relation types.

For instance, the below example shows an event with five bundled relations:
three thumbsup reaction annotations, one replace, and one reference.

```json
{
    ...,
    "unsigned": {
        "m.relations": {
            "m.annotation": {
                "chunk": [
                  {
                      "type": "m.reaction",
                      "key": "👍",
                      "origin_server_ts": 1562763768320,
                      "count": 3
                  }
                ],
                "limited": false,
                "count": 1
            },
            "m.reference": {
                "chunk": [
                    {
                        "type": "m.room.message",
                        "event_id": "$some_event_id"
                    }
                ],
                "limited": false,
                "count": 1
            },
            "m.replace": {
                "event_id": "$edit_event_id",
                "origin_server_ts": 1562763768320,
                "sender": "@bruno1:localhost"
            }
        }
    }
}
```

#### Handling limited (gappy) syncs

For the special case of a gappy incremental sync, many relations (particularly
reactions) may have occurred during the gap.  It would be inefficient to send
each one individually to the client, but it would also be inefficient to send
all possible bundled aggregations to the client.

The simplest thing a client can do is to just throw away its history for a
room on seeing a gappy incremental sync, and then re-paginate the history of
the room using /messages in order to get a consistent view of the relations
which may have changed during the gap.  However, this is quite inefficient,
and prohibits the client from persisting multiple sections of timeline for a
given room.

Alternatively, the server tells the client the event IDs of events which
predate the gap which received relations during the gap.  This means that the
client can invalidate its copy of those events (if any) and then requery them
(including their bundled relations) from the server if/when needed.

The server does this with the new `stale_events` field of each room object
in the sync response.  The `stale_events` field lists all the event IDs
prior to the gap which had updated relations during the gap.  The event IDs
are grouped by relation type, and limited to N entries for efficiency.  N
should be 100.  If the number of events with stale relations exceeds N, the
list is marked as `limited` as per the normal Matrix pagination model.  We do
not include events referenced by `m.reference` as stale, in favour of more
sophisticated pagination techniques in future. For instance:

```json
"!roomid:matrix.org": {
  "account_data": {},
  "ephemeral": {},
  "state": {},
  "summary": {},
  "timeline": {},
  "unread_notifications": {},
  "stale_events": {
    "m.annotations": {
      "chunk": [
        "$12345676321:matrix.org",
        "$12345321432:matrix.org"
      ],
      "limited": false
    }
  }
}
```

This shows that in the gappy sync response, a given room has two events prior
to the gap which received new annotations during the gap. Therefore if the
client has cached a local copy of those events, it should invalidate them, and
subsequently refresh them as needed.

To refresh events, we need an API to load arbitrary events from the room in
bulk, which the CS API doesn't currently provide.  We propose extending GET
`{roomId}/event/{eventId}` to accept a list of event IDs on the URL, e.g:

`POST /_matrix/client/r0/rooms/{roomId}/event`
```json
{
    "event_ids": [
        "$12345676321:matrix.org",
        "$12345321432:matrix.org"
    ]
}
```

...which returns an array of events with the given IDs.

  XXX: Is this implemented in Synapse yet?

#### Paginating relations and aggregations

A single event can have lots of associated relations, and we do not want to
overload the client by including them all in a bundle. Instead, we provide two
new APIs in order to paginate over the relations, which behave in a similar
way to `/messages`, except using `next_batch` and `prev_batch` names (in line
with `/sync` API). Clients can start paginating either from the earliest or
latest events using the `dir` param.

The `/relations` API lets you iterate over all the **unbundled** relations
associated with an event in standard topological order.  You can optionally
filter by a given type of relation and event type:

```
GET /_matrix/client/r0/rooms/{roomID}/relations/{eventID}[/{relationType}[/{eventType}]]
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "sender": "...",
      "content": { }
    }
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

The endpoint does not have any trailing slashes.

  FIXME: we need to spell out that this API should return the original message
  when paginating over `m.replace` relations for a given message.  Synapse
  currently looks to include this as an `original_event` field alongside
  `chunk` on all relations, which feels very redundant when we only need it for
  edits.  Either we specialcase it for edits, or we just have the client go
  call /event to grab the contents of the original?

The `/aggregations` API lets you iterate over **bundled** relations, and within them.

To iterate over the bundled relations for an event (optionally filtering by
relation type and target event type):

```
GET /_matrix/client/r0/rooms/{roomID}/aggregations/{eventID}[/{relationType}][/{eventType}][?filter=id]
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "key": "👍",
      "origin_server_ts": 1562763768320,
      "count": 5,
    }
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

The endpoint does not have any trailing slashes.

Trying to iterate over an relation type which does not use an aggregation key
(i.e. `m.replace` and `m.reference`) should fail with 400 and error
M_INVALID_REL_TYPE.

To iterate over the unbundled relations within a specific bundled relation, you
use the following API form, identifying the bundle based on its `key`
(therefore this only applies to `m.annotation`, as it is the only current
`rel_type` which groups relations via `key`).

```
GET /_matrix/client/r0/rooms/{roomID}/aggregations/{eventID}/${relationType}/{eventType}/{key}
```

e.g.

```
GET /_matrix/client/r0/rooms/!asd:matrix.org/aggregations/$1cd23476/m.annotation/m.reaction/👍
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "sender": "...",
      "content": { }
    },
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```


### End to end encryption

Since the server has to be able to bundle related events, structural
information about relations must be visible to the server, and so the
`m.relates_to` field must be included in the plaintext.

A future MSC may define a method for encrypting certain parts of the
`m.relates_to` field that may contain sensitive information.

### Redactions

Trying to call `/relations` or `/aggregations` on a redacted message must return
a 404.

### Local echo

As clients only receive unbundled events through /sync, they need to locally
aggregate these unbundled events for their parent event, on top of any
server-side aggregation that might have already happened, to get a complete
picture of the aggregated relations for a given parent event, as a client
might not be aware of all relations for an event. Local aggregation should
thus also take the `m.relation` data in the `unsigned` of the parent event
into account if it has been sent already. The aggregation algorithm is the
same as the one described here for the server.

For the best possible user experience, clients should also include unsent
relations into the local aggregation. When adding a relation to the send
queue, clients should locally aggregate it into the relations of the parent
event, ideally regardless of the parent event having an `event_id` already or
still being pending. If the client gives up on sending the relation for some
reason, the relation should be de-aggregated from the relations of the parent
event. If the client offers the user a possibility of manually retrying to
send the relation, it should be re-aggregated when the user does so.

De-aggregating a relation refers to rerunning the aggregation for a given
parent event while not considering the de-aggregated event any more.

Upon receiving the remote echo for any relations, a client is likely to remove
the pending event from the send queue. Here, it should also de-aggregate the
pending event from the parent event's relations, and re-aggregate the received
remote event from `/sync` to make sure the local aggregation happens with the
same event data as on the server.

When adding a redaction for a relation to the send queue, the relation
referred to should be de-aggregated from the relations of the target of the
relation.  Similar to a relation, when the sending of the redaction fails or
is cancelled, the relation should be aggregated again.

To support creating relations for pending events, clients will need a way for
events to relate to one another before the `event_id` of the parent event is
known. When the parent event receives its remote echo, the target event id
(`m.relates_to`.`event_id`) of any relations in the send queue will need to be
set the newly received `event_id`.

Particularly, please remember to let users edit unsent messages (as this is a
common case for rapidly fixing a typo in a msg which is still in flight!)

## Edge cases

How do you handle ignored users?
 * Information about relations sent from ignored users must never be sent to
   the client, either in bundled or unbundled form.  This is to let you block
   someone from harassing you with emoji reactions (or using edits as a
   side-channel to harass you).

What does it mean to call /context on a relation?
 * We should probably just return the root event for now, and then refine it in
   future for threading?
 * XXX: what does synapse do here?
