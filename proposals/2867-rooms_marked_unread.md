# MSC2867: Marking rooms as unread

There is currently no way to mark a room for later attention. A common use-case is receiving a 
notification on the go and opening the corresponding room but then deciding to deal with it at a later time.

This MSC introduces an option to manually mark an room as *Unread*.

In the above use-case the user would just mark the room as unread and when later opening a matrix
client on their desktop PC that room would appear prominently in their room list waiting for attention.

A related use-case solved by this proposal is wanting to mute a room's notifications while there's an
ongoing discussion but still flag it for catching up later.

Both WhatsApp and Telegram offer this functionality.

## Proposal

We add a [room account data](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-user-userid-rooms-roomid-account-data-type) 
field `m.marked_unread` which just stores the following:

```json
{
  "unread": true | false
}
```

When this is true a client should show the room with an indeterminate unread marker. This marker should
be of similar visual importance to a notification badge without the notification count. For example if 
you have a red circle with small numbers inside for counting notifications next to a room, then a room 
without notifications but marked as unread should have just the red circle. If a client gets new 
notifications after marking a room as unread the notification count should be displayed instead as normal.

The `m.fully_read` marker should not be touched when marking a room as unread to keep the users read position 
in the room.

Marking a room as read, if a client implements such a functionality, now involves sending a read receipt for the last 
event, as well as setting `m.marked_unread` to false.

The unread flag should be cleared when opening the room again.

## Potential issues

Client not aware of this feature will not clear the unread flag, when reading the room. In addition they'll obviously 
not show the room with a special badge. This seems preferable to the alternative of clearing the unread flag of a room
without intending to because it didn't actually show up as unread.

## Alternatives

There are multiple possible alternatives here;

* Marking individual messages as unread as discussed [here](https://github.com/matrix-org/matrix-doc/issues/2506):
  This is a far more complex feature that has possible interactions with server-side implementations and notification
  counts. This proposal aims to be a far more lightweight alternative. Looking at other messengers marking a room as 
  unread is a more common operation than marking messages as unread, so it could be argued that others already found 
  this to strike a good balance of complexity and use-cases covered.
* Modifying the `m.fully_read` marker instead of introducing a new `m.marked_unread` field:
  Another idea was setting the `m.fully_read` marker to some earlier event which would then cause clients to show 
  unread messages again. This has two problems:
    * It makes it harder to distinguish between rooms which happen to have unread messages that you don't necessarily 
      care about and rooms which were manually marked as such and thus should be shown much more prominently.
    * When trying to work around this, by setting the marker at a special location like the room creation event, we completely
      lose the user's actual read position in a room whenever they use this feature.

## Security considerations

None.

## Unstable prefix

While this feature is not yet fully specced, implementers can use the `com.famedly.marked_unread` room 
account data type.

Implementations using this unstable prefix in a released version should automatically migrate 
a users unread rooms to `m.marked_unread` when this is released as stable.
This ensures the users unread rooms are not lost.
