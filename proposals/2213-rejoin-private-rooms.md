# Rejoinability of private rooms

Similar to a house, users in a private room should have the option of joining and
leaving a room provided they have a key to get in. This process shouldn't involve
another user to send an invite once the user has joined at least once. This proposal
has little meaning in a public room as users are welcome to come and go as they
please already.

An example use case for this would be a direct chat where for de-cluttering one
of the users leaves all direct chats after they become irrelevant. This does
already happen in practice, and often results in the user who left creating multiple
DMs with the other user. [MSC2199](https://github.com/matrix-org/matrix-doc/pull/2199)
covers new DM semantics which benefit from this proposal where users can re-use
DMs even after they've left.

Another use case, not solved by this proposal, would be to support a group-wide
join rule where members of a given group are able to join the room. This use case
is better solved by [MSC2214](https://github.com/matrix-org/matrix-doc/pull/2214)
however.

## Proposal

In a future room version...

`m.room.join_rules` is expanded to have a new `rejoin_rule` field under `content`,
preserved by the redaction algorithm. The `rejoin_rule` must be one of:

* `invite`: Members which were previously invited or joined to the room can rejoin,
  provided they are now not banned.

* `join`: Members which were previously joined to the room can rejoin, provided they
  are now not banned.

* `forbidden`: This event cannot be used to authorize a rejoin (members must be
  explicitly invited back into the room). This is the default.

The `rejoin_rule` only takes effect if the `join_rule` for the room is `invite`,
given users can already rejoin the room if the room is public. When the `join_rule`
is any other value, the `rejoin_rule` does not affect the auth for an event.

When a join or invite is being processed, the server must first determine if that
user has a prior membership event. If the user does not have a prior membership event,
the `rejoin_rule` does not apply. If the user does have a prior membership event,
the following conditions do apply:

1. If the previous membership is not explicitly `leave`, `rejoin_rule` does not apply.
   For example, bans still ban, invites still invite, and never having been in the room
   does not let you use `rejoin_rule` to get in.
2. If the `rejoin_rule` is `forbidden`, or implied to be `forbidden`, reject.
3. If the previous membership is explicitly `leave`, the server must look at the membership
   previous to that membership to make a decision:
   1. If the `rejoin_rule` is `join` and the membership previous to `leave` is not `join`
      then reject. Else accept.
   2. If the `rejoin_rule` is `invite` and the membership previous to `leave` is not
      `join` or `invite`, reject. Else accept.

In short: the member must `leave` before they can have a `rejoin_rule` allow them in
again.

**Known limitation**: If the user were to be kicked twice they would not be allowed
back into the room despite a reasonable `rejoin_rule`. This is an intentional limitation
of the proposal to prevent servers from having to traverse the entire room state history
to find a previous membership event. For example, if a server had to traverse the state
history for Matrix HQ (if it were private) every time someone wanted to join the server
could end up exhausting resources. For simplicity, the server is only expected to look
at the most recent 2 memberships maximum, as per above. This limitation can be resolved
with a regular invite.


## Security considerations

Room operators are expected to be aware of the room access controls available to them,
much like they are expected to understand the ones currently available. This join rule
alteration may not be applicable to their room, or could open them up to an attack they
are not comfortable with. For this reason, the default behaviour of the proposal is to
maintain existing expectations for join rules.


## Alternative solutions

Instead of re-using the join rules event we could introduce a new state event. Although
possible, and would likely have the same semantics, it is not immediately obvious what
the benefit of more state events would bring to Matrix. It is often preferred to reuse
existing constructs where possible, such as the aptly named "join rules" event.

Further, this proposal could be done in the form of introducing new `join_rule`s instead
of a new field. Given the `rejoin_rule` only takes effect when `join_rule == "invite"`,
we could redefine the `join_rule` to be `[public, invite, rejoin_invite, rejoin_join]`
or similar. This would simplify the definition, however it does conflate two concerns
and behaviours.
