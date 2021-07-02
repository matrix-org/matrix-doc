# MSC 1716: Open-on-device API

Matrix.to is now the defacto way to link to your Matrix room from a project site, or inside a client. However, there is no
immediate process to open the link in your *active* client. Users often click on the link, and open the client inside the
browser leading to wasted time and resources, or copying and pasting the link between clients (or even devices!). The expectation
is that this feature should function similarly to Firefox's and Chrome's "Send Tab to Device" feature.

This proposal aims to address this problem by adding a simple event schema to notify a client to display a room, event or user.

(It should be noted that https://matrix.to is used as an example Matrix linker web app, but any Matrix web app could do the following things.
It would also be expected for a browser extension to offer this functionality eventually)

## Proposal

When an application wants to offer a user the ability to open a room, event or user on a device, they should first store the user's access
token (either direct entry or via login) and preferred device.

When the user clicks on a link, the app should send a request using the 
[Send-to-Device messaging API](https://matrix.org/docs/spec/client_server/r0.4.0.html#put-matrix-client-r0-sendtodevice-eventtype-txnid). 

### Schema

The event type should be `m.openondevice` and the `EventContent` should be:

#### `room`

```json
{
  "type": "room",
  "via": "half-shot.uk",
  "id": "!someneatlookingroom:matrix.org",
}
```

#### `event`

```json
{
  "type": "event",
  "room_id": "!someneatlookingroom:matrix.org",
  "via": "half-shot.uk",
  "id":   "$andthiseventtoo:half-shot.uk",
}
```

#### `user`

```json
{
  "type": "user",
  "id":   "@purpledog:half-shot.uk",
}
```

#### `group`

```json
{
  "type": "group",
  "id":   "+silly.bot.committee:t2bot.io",
}
```

| key     | type     | value                                          | Default      |
|---------|----------|------------------------------------------------|--------------|
| type    | string   | One of "room", "event", "user" or "group"      | Non-optional |
| room_id | string   | A room ID when the type is "event"             |              |
| via [1] | string[] | A set of servers needed for "room" and "event" | []           |
| id      | string   | A room ID, event ID, user ID                   | Non-optional |

* [1] This is explained further in [MSC1704](https://github.com/matrix-org/matrix-doc/pull/1704). 
  We will not address the usage of `via` in this proposal but make the assumption that it will be
  part of the spec by the point MSC1716 is considered.

The recipient user ID for `/sendToDevice` should always be the authenticated user. *Clients* who receive this event from another sender MUST ignore it.

The recipient device ID should be the stored preference stated previously.

When the message arrives on the recipient device, the device must immediately change the current view to show the type in the contents. It is not
required, but the client could state somewhere why the switch happened. E.g. on mobile applications it may show a Toast to say that a remote device
has opened a room. 

## Tradeoffs

* An alternative to using the device API would be to use a room with the proposed event schema, but this would persist the event in history
which is unnecessary, and more expensive than a direct device message.

* A room could also be used as a blunt transport for matrix.to links, where clicking on a link would automatically send it to the room and the
user could then click on that message from their preferred device. However, this has the efficiency issues of Tradeoff #1, and also requires extra user actions.


## Potential issues

* Attackers gaining access to the users account may try to spam the owner's device(s) with bogus open links, which may break clients. This proposal
doesn't introduce any rate limiting for this feature. This proposal also assumes the user is in control of their account.

* If there is a delay in the message arriving or being processed, users may find themselves using the client
  and then finding that it has unexpectedly switched views. The proposal doesn't specify a timeout to combat this.

## Conclusion

Using the event schema proposed, it should be easy for applications on both the sending and receiving end to incorporate this feature. Future
proposals could extend the feature to support viewing other artefacts on Matrix, like devices. However, this seems like the most efficient way
to support cross-device linking without adding extra dependencies on Matrix.
