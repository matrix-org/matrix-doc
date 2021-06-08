# MSC 2375: Proposal to add invite states to invites sent to Application Services
Application Services are a great way to extend the homeservers functionality, e.g. by bridging matrix
to other networks.

When receiving an invite you might want to get additional information about the room you are invited
to, such as the room name and icon to e.g. bridge them nicely to the remote network. Currently
Application Services do not offer this, unlike clients.

This could also be of help if an application service wants to somehow verify invites before joining
rooms, e.g. if a token is present and valid in the invite state.

## Proposal
This proposal is about adding `invite_room_state` to the `unsigned` block of invite events when sending
them out to Application Services.

As content of `invite_room_state` an array of `StrippedState` (defined [here](https://matrix.org/docs/spec/server_server/r0.1.3#put-matrix-federation-v2-invite-roomid-eventid))
objects would be used. This way it would
be in line with the Server-Server API to send invites.

### Example
An invite event of `@alice:example.com` inviting `@bob:example.com` could look as follows:

```json
{
  "content": {
    "avatar_url": "mxc://example.com/some_avatar",
    "displayname": "New Person",
    "membership": "invite"
  },
  "event_id": "$some_event_id",
  "origin_server_ts": 1575368937985,
  "room_id": "!some_room:example.com",
  "sender": "@alice:example.com",
  "state_key": "@bob:example.com",
  "type": "m.room.member",
  "unsigned": {
    "age": 1167,
    "invite_room_state": [
      {
        "type": "m.room.name",
        "sender": "@alice:example.com",
        "state_key": "",
        "content": {
          "name": "Example Room"
        }
      },
      {
        "type": "m.room.join_rules",
        "sender": "@alice:example.com",
        "state_key": "",
        "content": {
          "join_rule": "invite"
        }
      }
    ]
  }
}
```

# Potential issues
Depending on server implementation this could be a heavy operation. Additionally more data is sent
down the line to the Application Service. As this is already done for normal clients it shouldn't be
too bad, though.

# Alternatives
Instead of aligning with S-S API `/invite` it could be aligned with C-S API `/sync` and putting the
invite states into a separate `rooms.invite[roomId].invite_state.events` array. This, however, makes
it more complicated for application services to parse as the invite state isn't directly attached to
the invite itself.

# Security considerations
As the invite states are presented to the invitee via other API endpoints (C-S API) this shouldn't
give any new security considerations.
