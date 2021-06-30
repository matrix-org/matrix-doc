# MSC3061: Sharing room keys for past messages

In Matrix, rooms can be configured via the `m.room.history_visibility` state
event such that historical messages can be visible to all Matrix users
(`world_readable`), all room members (`shared`), room members from the time
that they are invited to a room (`invited`), or room members from the time that
they join a room (`joined`).  However, currently in encrypted rooms, rooms with
the history visibility set to `world_readable` or `shared` are effectively
set to `invited` since other members generally do not send new members the keys
to decrypt messages sent before they were invited or joined a room.

We define a "shared-history" flag that identifies keys for messages that were
sent when the room's visibility setting was set to `world_readable` or
`shared`.  This allows clients to know which keys are "safe" to share with new
members so that they can decrypt historical messages.  We also give examples of
ways in which this flag can be used.


## Proposal

A room key (such as a megolm session) is flagged as having been used for shared
history when it was used to encrypt a message while the room's history
visibility setting was set to `world_readable` or `shared`.  Internally, a
client may use any mechanism it wants to keep track of this flag.  When a room
key is marked as such:

- `m.room_key` and `m.forwarded_room_key` messages used to share this key have
  a `shared_history` property set to `true`,
- the `session_data` field in key backups of this key has a `shared_history`
  property set to `true` in the decrypted JSON structure, and
- the `SessionData` type used in key exports has a `shared_history` property
  that is set to `true` for this key.

When a client obtains a key that has the `shared_history` property set to
`true`, then it flags the key internally as having been used for shared
history.  Otherwise, the key should not be flagged as such.

When the room's history visibility setting changes to `world_readable` or
`shared` from `invited` or `joined`, or changes to `invited` or `joined` from
`world_readable` or `shared`, senders that support this flag must rotate their
megolm sessions.

Clients may use this flag to modify their behaviour with respect to sharing
keys.  For example:

- when the user invites someone to the room, they may preemptively share keys
  that have this flag with the invited user.
- when the user receives a key share request, they may share the key with the
  requester if the user is a current member of the room.  The key may be shared
  from the first available ratchet index, not just the requested index.
- when sending a message after a new user has joined the room, a sender may
  share the megolm session from the first available index, rather than from the
  current ratchet index.

## Potential issues

Room keys from clients that do not support this proposal will not be eligible
for the modified client behaviour.

## Alternatives

Rather than having the sender flagging keys, a client can paginate through the
room's history to determine the room's history visibility settings when the
room key was used.  This would not require any changes, but has performance
problems.  In addition, the server could lie about the room history while the
user is paginating through the history.  By having the sender flag keys, this
ensures that the key is treated in a manner consistent with the sender's view
of the room.

## Security considerations

Clients should still ensure that keys are only shared with authorized users and
devices.

## Unstable prefix

Until this feature lands in the spec, the property name to be used is
`org.matrix.msc3061.shared_history` rather than `shared_history`.
