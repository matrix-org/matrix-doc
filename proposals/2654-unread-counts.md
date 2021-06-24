# MSC2654: Unread counts

Homeservers currently send clients counts for missed notifications (and
highlights) in responses to `/sync` requests, which allows them to display that
information to clients. However, no count is provided for unread messages. This
means clients have no way of telling users how many messages they've missed
since they last read a given room.

This MSC is an alternative to
[MSC2625](https://github.com/matrix-org/matrix-doc/pull/2625), which doesn't use
push rules to calculate unread counts, allowing for simpler implementations.


## Proposal


### Extended response to `/sync`

This MSC proposes the addition of an `unread_count` parameter in the `Joined
Room` section of
[`/sync`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-sync)
responses.

The value of this parameter is a count of every unread event (see below for a
list of criteria an event needs to match to be marked unread) since the latest
read receipt (i.e. the latest `m.read` read marker) for the given user in the
given room. If no read receipt exists for this user in this room, then the value
of the parameter is a count of every unread event since that user joined it.

In case of a mismatch between this count and the value of `notification_count`
in the `Unread Notification Counts` section, clients should use the
`unread_count`.


### Unread events

An event should be counted in the unread count only if it matches at least one
of the following criteria:

* include a non-empty `body` field of type string, in its content
* be a state event which type is one of:
    * `m.room.name`
    * `m.room.topic`
    * `m.room.avatar`
    * `m.room.tombstone`
* be an encrypted message (i.e. have the `m.room.encrypted` type)

Additionally, an event should _not_ be counted in the unread count if it matches
at least one of the following criteria, even if it is otherwise eligible to be
included in the count:

* include a `m.relates_to` parameter in its content that includes a `rel_type`
  parameter, which value is `m.replace`. This matches the definition of an edit
  in [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676).
* have the type `m.room.message`, no `state_key`, and include a `msgtype`
  parameter in its content which value is `m.notice`.

Finally, a redaction to an event that was marked as unread should exclude that
event from the unread count.

When calculating the unread count for a given user in a given room, events sent
by the requesting user in the room should be ignored.

If the event is an encrypted message, clients should decrypt it and apply the
rules above to make adjustments to the unread count sent by the homeserver.


## Potential issues

This MSC mentions edits, which are specified in
[MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676). Therefore, it is
unclear whether this MSC can be merged before MSC2676.

Unlike notifications, it is not possible to not have the homeserver provide an
unread count for a given room. A way to do this will be described in a separate
MSC.


## Alternatives

As mentioned in the introduction of this proposal,
[MSC2625](https://github.com/matrix-org/matrix-doc/pull/2625) proposes an
alternative implementation of this feature using push rules. However, given the
complexity of push rules and that MSC2625 requires to implement a new behaviour
for the `mark_unread` action, using push rules for this feature doesn't seem to
be adding much values, and seems to add unnecessary complexity to its
implementation.


## Unstable prefix

While this feature is in development, the following names will be in use:

| Proposed final name | Name while in development |
| --- | --- |
| `unread_count` | `org.matrix.msc2654.unread_count` |
