# MSC2943: Return an event ID for membership endpoints

This proposal considers the following as "membership endpoints":

* [3PID /invite](https://matrix.org/docs/spec/client_server/r0.6.1#id101)
* [MXID /invite](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-invite)
* [/join](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-join)
* [/join/:alias](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-join-roomidoralias)
* [/leave](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-leave)
* [/kick](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-kick)
* [/ban](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-ban)
* [/unban](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-rooms-roomid-unban)

Despite being APIs which generate a single event, none of these endpoints return the event ID for that
event. This can lead to issues in some use cases where the client needs to know the event ID for future
consideration, such as linking up a third party invite with an internal record so it can associate the
user ID which claims it in the future with the email/3pid. The remaining APIs do not have a strong use
case at this time, though they do not appear to have a strong reason to be excluded from this proposal.

## Proposal

All the membership endpoints listed above must return the event ID for the event they generated. For
all except the 3PID `/invite` endpoint this will be the associated `m.room.member` event - the 3PID
invite endpoint would return the ID of the `m.room.third_party_invite` event. The event ID is returned
as `event_id`, just like it is for [/send](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-send-eventtype-txnid)
and [/state](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-state-eventtype-statekey).

This should allow client implementations, such as bots, have better context as to what occurred in the
room. This will also allow those client implementations to use these sugar APIs instead of `/state`
manually, for the implementations which prefer to use sugar APIs.

## Potential issues

None forseen.

## Alternatives

None relevant. Arguments regarding the 3PID system itself potentially needing changes and thus this
proposal should not consider them are dismissed - irrespective of improvements to how 3PID invites work
it is anticipated that this sort of change will move quicker through the spec and get more immediate
value.

## Security considerations

None relevant - the endpoints already have security considerations in place and none are modified here.
This proposal simply provides information which the client could obtain through other methods if it
wanted to (such as using `/state` to send the event, or querying the room state manually, or using `/sync`).

## Unstable prefix

While this MSC is not in a released version of the specification, implementations should use
`org.matrix.msc2943.event_id` in place of `event_id`.
