# MSC3217: Clientside hints for a soft kick

Presently in Matrix you can kick a user from a room, where (in a public room setting) clients 
usually prompt the user to rejoin if they wish. However kicks can be used for different 
reasons and the
current state doesn't allow the client to accurately reflect that. Most clients present a kick
as a "hard" action where you can no longer see the history of the room and the language 
describes it as a forced removal.

Some kicks are however "soft", e.g. if an IRC bridge wishes to preserve history privacy in a 
room, it needs to temporarily kick users who could not connect to the IRC channel to avoid 
Matrix users reading conversations while not being visible on IRC (in the absence of per-message ACLs).

These kicks are often met with confusion and irritation however from the Matrix user who can 
no longer read the history in the room.

Instead, it would be useful if the Matrix spec could distinguish between:

- The existing type of kick, where kicking should be considered as anti-abuse or deliberately
  ejecting someone who should not be there.
- A new type of kick where the action is "soft" and the room should continue to be
  visible in the client with all history, and provide an easy way back into the room.


## Proposal

A new key in the `m.room.member` state event will be added to kick events, `m.softkick`. The 
key is a hint to clients and should not be treated differently at the server level. The key 
should be ignored if seen in membership types other than `leave` or if the `state_key`
matches the `sender`.

```json5
{
    "type": "m.room.member",
    "room_id": "!ircfun:half-shot.uk",
    "event_id": "$oops:half-shot.uk",
    "content": {
        "m.softkick": true,
        "reason": "Your IRC connection has been lost.",
        "membership": "leave",
    },
    "sender": "@irc:half-shot.uk",
    "state_key": "@alice:half-shot.uk"
}
```

Since this is a hint, the spec will not prescribe exact behaviour for clients however clients 
SHOULD:
- Warn the user that they are no longer participating in the room due to the reason specified.
- Preserve the room in the room list.
- Keep the room and its history accessible, with any actions (other than forgetting the room) 
  greyed out.
- Give the user the ability to try to rejoin the room
- The service can also invite you back to the room when it is safe to rejoin. Users may click 
  the rejoin button ahead of receiving the invite to automatically join back when ready.
  - If the client receives an invite from the user who soft-kicked them, it should autojoin 
    the room without prompting.
  - Invites should be sent for both public and private rooms to signal when it is safe to join.

`m.softkick` SHOULD only be used by services that intend to use the kick as a temporary action 
such as losing connection to the remote side of a bridge. Clients SHOULD not expose the 
feature themselves.

If a client does not support this key, the fallback behaviour will simply be to display the 
reason to the user and the user will still be able to rejoin as they do today.


## Potential issues

Some clients and servers may strip unexpected fields from the state event, meaning that it may 
not be possible to always see this key. Given that Matrix events are extensible by design, we 
would consider these clients non-spec compliant and therefore a non-issue for this MSC.

## Alternatives

Bridges could avoid using the kick events altogether to bridge the disconnection state of a 
user from a service/channel.  However several IRC networks have raised concerns that keeping a 
Matrix user in a room without them being present on the IRC side does not respect the privacy 
of the IRC users and would forfeit our ability to bridge to those networks.

Given Matrix is designed to be as bridge / remote network friendly as possible while also 
being privacy preserving, it's imperative that we support this use case.

## Security considerations

None. This MSC just includes a new key on the member state event and shouldn't change the security of the protocol.

## Unstable prefix

Implementations should use `org.matrix.msc3217.softkick` as a key name until this lands in a 
released version of the specification.
