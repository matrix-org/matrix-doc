# MSC2285: Hidden read receipts

Currently users must send read receipts in order to affect their notification counts, which
alerts to other people that the user has read their message. For primarily privacy reasons,
it may be desirable to users to not advertise to others that they've read a message.

## Proposal

When sending a `m.read` receipt, a `m.hidden: true` flag can be included (optional) to tell
the server to not send it to anyone else. This allows the user to affect their notification
counts without advertising that they've read the message. `m.hidden` defaults to `false`.

For example:
```
POST /_matrix/client/r0/rooms/!a:example.org/receipt/m.read/$123
{
    "m.hidden": true
}
```

The same applies to read markers (which allow you to update your read receipt):
```
POST /_matrix/client/r0/rooms/!a:example.org/read_markers
{
    "m.fully_read": "$123",
    "m.read": "$123",
    "m.hidden": true
}
```

Note that fully read markers are not sent to other users and are local to the user sending them.
Therefore, no changes are required or implied by `m.hidden` for `m.fully_read` - just `m.read`.

Servers processing read receipts MUST NOT send hidden receipts to any other user than the sender.
Servers MUST NOT send hidden receipts over federation to any server.

## Tradeoffs

Clients which support read receipts would end up rendering the user's receipt as jumping down
when they send a message. This is no different from how IRC and similarly bridged users are
perceived today.

## Security considerations

Servers could ignore the flag without telling the user. The user must already trust the homeserver
to a degree however, and the methods of notifying the user to the problem are difficult to
implement. Users can always run their own homeservers to ensure it behaves correctly.

## Why not X kind of EDUs?

In short: don't send those EDUs. Typing notifications, device messages, etc can all be mitigated
by simply not calling the endpoints. Read receipts have a side effect of causing stuck
notifications for users however, which is why they are solved here.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc2285` as a namespace
for identifiers. `m.hidden` becomes `org.matrix.msc2885.hidden` for example.

To detect server support, clients can either rely on the spec version (when stable) or the presence of
a `org.matrix.msc2285` flag in `unstable_features` on `/versions`. Clients are recommended to check for
server support to ensure they are not misleading the user about "hidden read receipts".
