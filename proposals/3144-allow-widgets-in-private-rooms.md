# MSC3144: Allow Widgets By Default in Private Rooms

As it stands, the default power levels of matrix rooms only allow the room creator and those
granted sufficient power level the ability to add widgets to the room. This includes starting
group calls. This is desirable in a public room, but in a private room where participants are
generally trusted, it hinders users trying to make group calls.

## Proposal

This MSC proposes allowing all users to edit room widgets, including placing and ending group calls,
in the default room configuration.

It proposes to accomplish this by changing the `private_chat` preset on `createRoom` to send the
`m.room.power_levels` event with the `im.vector.modular.widgets` event at the `users_default` level
(ie. normally 0).

There are a couple of stubling blocks in doing so, listed below. This MSC hopes to elicit discussion
on whether any other solutions exist to these issues or whether they are acceptable tradeoffs.

## Potential issues

1. This change would happen on server implementation without clients or users knowing anything had
   changed, so it could surprise users who are used to the current configuration, leaving them with
   a private room where others can add widgets unexpectedly.

1. Room admins might later change the room to be a public room without realising that anyone can
   edit widgets, resulting in an insecure configuration.

## Alternatives

We could instead make a separate preset that did this and migrate clients over to using it. This would
require all clients to make changes though. We could instead make this behaviour dependent on the version
in the API URL.

Another option would be to have clients change this power level after creating a room, so the client
could warn the user that this setting was being applied, or give the user a choice. However, this would
mean that the behaviour of rooms would diverge depending on what client they were created with, which is
probably far more confusing.

Changing a room from private to public is harder to work around. Clients can add a warning for this case
but even if this MSC made such a warning mandatory, older clients will still exist.

## Security considerations

None forseen other than those detailed in 'potential issues'.

## Unstable prefix

N/A
