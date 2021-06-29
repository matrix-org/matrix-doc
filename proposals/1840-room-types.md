- **Author**: Jonathan Frederickson
- **Created**: 2019-02-03

# Room Types

## Problem

The Matrix protocol currently has no mechanism to differentiate rooms
from each other based on their intended use case. There have been
proposals such as
[MSC1769](https://github.com/matrix-org/matrix-doc/pull/1769) and
[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) that use
rooms for purposes other than the traditional messaging
use-case. Without a mechanism to differentiate them from messaging
rooms, clients will display them as they do any other room unless they
work around this limitation on a case-by-case basis.

## Solution

The proposal is to add a new state event, `m.room.type`, to define the
intended usage of the room. Some example use cases for this:

- A long-form email-style client wants to provide a UI for sending
  longer (possibly threaded) messages, but doesn't want those threads
  to be overwhelmed by users sending short IM-style messages
  (`m.messaging.mail` perhaps?)
- A blogging app built on Matrix wants to define and use custom "blog
  post" and "comment" message types, but doesn't want Element users to
  join with a client that doesn't understand any of the messages
- A project wants to use Matrix to allow a user to interact with an
  IoT lightbulb, but doesn't want the rooms and control messages used
  for this to clutter up the user's Element room list
  (`com.example.manufacturer.iot.light`)

The list of possible values of `type` is user-extensible; this
proposal defines `m.messaging`, but other types may be used by
client developers as desired. Grammar of values must conform to
[MSC2758](https://github.com/matrix-org/matrix-doc/blob/master/proposals/2758-textual-id-grammar.md)
rules for textual identifiers.

This proposal defines `m.messaging` as the (thus far) traditional
instant-messaging style room found in Element and most other Matrix
clients today. Client developers may handle rooms without a type in a
way that makes sense for each client; for example, it is expected that
an IM client would list both untyped rooms (for backwards
compatibility) and rooms of type `m.messaging` in the room
list. However, clients that are aware of room types should add the
relevant room type state event when creating new rooms.

This by itself could be used by a client to properly display rooms
based on their intended usage. However, to optimize the use of
bandwidth for an account used for varying purposes, the filter API
could then be extended to allow for filtering the rooms that are
returned from a sync based on room type. (A client meant for receiving
IoT device data, for example, has no need to receive messages destined
for that account, nor to be aware at all that messaging rooms exist.)

N.B. There's an opportunity here to additionally scope access tokens
to specific room types, but that feels like it's beyond the scope of
this proposal at this point.

## Examples

### m.room.type

```json
{
    "content": {
        "type": "m.messaging"
    },
    "event_id": "$143273582443PhrSn:example.com",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.com",
    "sender": "@user:example.com",
    "state_key": "",
    "type": "m.room.type",
    "unsigned": {
        "age": 1234
    }
}
```

### Filter API Changes

```
POST /_matrix/client/r0/user/%40alice%3Aexample.com/filter HTTP/1.1
Content-Type: application/json

{
  "room": {
    "state": {
      "types": [
        "m.room.*"
      ],
      "not_rooms": [
        "!726s6s6q:example.com"
      ],
      "room_types": [
        "m.room_type.messaging"
      ],
      "not_room_types": [
        "m.room_type.iot.*"
      ],
    },
  "event_format": "client",
  "event_fields": [
    "type",
    "content",
    "sender"
  ]
}
```
