# MSC2749: Per-user E2EE on/off setting

Currently, there is no way for a server administrator to force disable end-to-end encryption for their
server. This can lead to poor user experience and leave the server admin unable to monitor conversations
on a server in a business or education environment, as pointed out in
[issue #2528](https://github.com/matrix-org/matrix-doc/issues/2528). Current methods, such as using a
reverse proxy to block E2EE, again lead to poor user experience and make it difficult to implement more
fine per-user controls on E2EE.

## Proposal

### Add a field to `/_matrix/client/r0/capabilities`

This would add an additonal field, `m.encryption`, to the `capabilities` object. The `m.encryption` object
would have two additional fields: `preference` and `force`, both of which are boolean values. The
`preference` field would be used to specify whether E2EE should be on or off by default. The `force` field
would indicate that the server is enforcing that preference. The default value for `preference` would be
`true` and the default value for `force` would be false.
```json
{
  "capabilities": {
    ...
    "m.encryption": {
      "preference": true,
      "force": false
    }
  }
}
```
The value of this endpoint could be returned on a *per-user* basis, similar to `m.change_password`. Future
MSCs could include a set of allowed algorithms.

### Client Behavior

When `preference` is `true` and `force` is `false`, client behavior would not change from what it is now:
Clients can prompt the user to set up E2EE and will enable E2EE by default in DMs. When `preference` is
`false` and `force` is still `false`, the client should not display prompts to set up E2EE and should not
enable E2EE by default. The user should manually go into the client's settings to set up E2EE.

When `force` is `true` and `preference` is `true`, the user should be prompted to set up E2EE when they
start their client. When creating rooms, the client should enforce creation with E2EE and display this to the
user. If the user joins or is a member of any rooms with E2EE disabled, the client should prohibit the user
from sending any events (with the exception of unencrypted state events) and, if the user is able to change
encryption settings in the room, may prompt the user to turn on encryption.

When `force` is `true` and `preference` is `false`, the user should never be prompted to set up E2EE. The
encryption section in the client's settings should indicate that the user cannot set up E2EE. When creating
rooms, the client should enforce creation with E2EE off and display this to the user. If the user joins or is
a member of any rooms with E2EE enabled, the client should prohibit the user from sending or reading messages
in the room, though they may send unencrypted state events. If the user is able to change encryption settings
in the room, the client may prompt the user to do so.

**TODO:** What should the client do about existing keys?

### Server Behavior

An new error type would be added: `M_ENCRYPTION_PREFERENCE`. This would be returned when access to an
endpoint is denied due to encryption preferences (see below).

#### when `force=true` and `preference=true`:

The server should deny any attempts to send `m.room.message` events. (**TODO:** Should other events be
blocked?) The server should also deny any attempts to `POST /_matrix/client/r0/createRoom` without the
`initial_state` containing `m.room.encryption`. The user should still be allowed to *join* unencrypted
rooms since behavior cannot be made consistent across local rooms and federation without peeking over
federation.

#### when `force=true` and `preference=false`:

The server should deny any attempts to send `m.room.encryption`, `m.room.encrypted`, `m.room_key`,
`m.room_key_request`, `m.forwarded_room_key`, or `m.key.verification.*` events as well as any room creation
with the `initial_state` containing any of those events. As with the above, the user should still be allowed
to *join* encrypted rooms. The server should also deny any requests to `/_matrix/client/r0/keys/*` as well as
any supported `unstable` encryption endpoints. The server should continue to store the keys for this user,
but should hide them from any other users and from federation.

## Potential issues

* What happens when a user on an encrypted server creates a DM with a user on an unencrypted server?
  * Could be fixed by adding user profile information, but this may be best implemeneted after extensible
    profiles land.
* What happens when a user with E2EE on has E2EE disabled?
  * Poor UX of rooms suddenly becoming unusable
  * What happens to keys already on device?

## Alternatives

The other alternative considered was actively removing non-E2EE users from rooms by having the server send a
kick on the user's behalf and denying access to rooms with encryption enabled. This was not done because it
was considered to be poor UX, both for the users in the existing room and the user attempting to join. Over
federation, this would look like the user joined the room and immediately kicked themself. Furthermore, when
a user's E2EE settings would get changed by a server admin, they would notice rooms disappearing from their
room list instead of displaying a warning.

## Security considerations

* A malicious homeserver could enforce E2EE-off on it's users possibly without them knowing it if they're
  first-time users that don't know about encryption prompts. Clients should warn the user that they're
  signing in with E2EE force-disabled.
* Users *could* in theory use modified clients to send encrypted data, however this would be difficult since
  the key endpoints are blocked and would require custom clients on both ends. Likewise, nothing stops a
  client from leaking unencrypted data when E2EE is force-enabled, but the latter is an issue with E2EE
  regardless. It should be made clear to server owners that E2EE-off enforcing may not catch custom clients.
* **TODO:** Anything else?

## Unstable prefix

The `m.encryption` field in the `capabilities` endpoint should have an unstable key of `org.matrix.msc2749`.

