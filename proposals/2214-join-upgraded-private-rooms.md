# Joining upgraded private rooms

Although most rooms which require an upgrade will be public, there are already
cases where private (invite-only) rooms are upgraded. There is also the lingering
possibility of a bug being found in the various algorithms which run a room that
require private rooms to be upgraded as well.

Currently when a room is upgraded all members need to rejoin manually. This is
fine for public rooms because the users can click a button and it takes them over
to the new room to join. For private rooms however, the members of the old room
need to be manually invited.

This limitation in upgrades has caused some grief for those who have tried to
upgrade private rooms already. While migrating membership transparently (auto-joining)
would be ideal, this proposal is meant to fill the gap for private rooms while
the harder problem of migrating membership is thought out more thoroughly. This
proposal does not aim to solve transparent migration of membership.

This proposal is also an idea for how to solve this based largely on the author's
work on [MSC2213](https://github.com/matrix-org/matrix-doc/pull/2213). It could
be completely flawed.


## Proposal

In a future room version, a new state event is introduced to track the previous
membership events for a given room. This new state event acts like a "soft invite"
where a user can be allowed into the room without getting hit with an explicit
invite.

The new state event, `m.room.previous_member`, mirrors the existing `m.room.member`
event. The `state_key` is the affected user and the `content` has the same definition
as the `m.room.member` event.

When a room is upgraded to a version which supports this proposal, the server is
expected to clone the `state_key` and `content` of the old room's `m.room.member`
events into `m.room.previous_member` events. The `sender` of the old `m.room.member`
event is specified as `previous_sender` under `content`, overwriting the key if
it was present in the `m.room.member` event's `content`. Servers can skip membership
events which won't result in the user being able to join the new room, such as
kicks, bans, and plain leaves. It is instead recommended that the server copy bans
over to the new room as regular `m.room.member` events.

`m.room.previous_member` carries its own set of auth rules for acceptance:

1. If there is no `state_key` key, no `membership` in `content`, or no `previous_sender`
   in `content`, reject.
2. If `membership` is not a valid `m.room.member` membership, reject.
3. If the `sender` is not the room creator, reject.
4. If the `sender` does not have permission to invite users, reject. This includes the
   room creator no longer being a member of the room themselves.
5. If the `sender` and the `state_key` are the same, reject.

`third_party_event` in the `content` of `m.room.previous_member` is not validated
and serves only audit purposes.

The redaction rules for `m.room.member` are copied for `m.room.previous_member`, with
the addition of preserving `previous_sender` in `content`. Although the `previous_sender`
does not serve a protocol purpose, it is metadata important for the audit trail of the
room.

Servers for these previous membership events are not expected to receive them over
federation until they actually join the room.

`m.room.previous_member` is only used in the auth rules when a user is attempting to
join the room. For all other scenarios (such as sending messages), the auth rules must
continue to look for an appropriate `m.room.member` event. The rules for handling joins
in the new room are as follows:

1. If the user has an `m.room.member` state event in the room, use that instead of the
   `m.room.previous_member` event. Stop processing these new rules and use the rules for
   handling a join with a `m.room.member` event instead.
2. If the `m.room.create` event does not have a `predecessor` in its `content`, reject.
2. If the `m.room.previous_member` `membership` is `invite`, process the join as though
   the user was invited (allow a `m.room.member` with `membership` of `join`).
3. If the `m.room.previous_member` `membership` is `join`, process the join as though the
   user was already joined (allow a `m.room.member` event to take its place).
4. If the `m.room.previous_member` `membership` is `ban`, process the join as though the
   user was banned (reject).
5. If the `m.room.previous_member` `membership` is `leave`, process the join as though the
   user has left the room (for example, reject if the room is invite-only).

`m.room.member` events use their own auth rules even when they replace a `m.room.previous_member`
event. For example, a user cannot introduce an `m.room.member` event with `membership`
of `ban` unless the user has permission to ban users, even if the `m.room.previous_member`
event had a `membership` of `ban` as well.


## Security considerations

This effectively gives the room creator the power to invite users until the end of time.
However, this is no different than any other user's ability to invite members to a room
in the vast majority of rooms today. The only difference is that the room creator is able
to lie about the previous membership of a user with no verification that it is accurate.

Clients should be skeptical of `m.room.previous_member` events and largely treat them as
invites.

Servers could additionally forget (intentionally or otherwise) to include valid members.
This is treated similar to the semantics of not inviting someone to your private room,
and should have the same social consequences (forever being disappointed in the person
who didn't invite you to the party).


## Alternative solutions / known problems

There's many solutions to this kind of problem. For example, we could change the auth
rules to allow a room creator to set `membership` of `join` on `m.room.member` events
without the target user being involved. This results in very complicated auth rules
however, as it would be possible for any room creator to craft a room which automatically
joins users without them having been in a relevant previous room. This would be bad.

This solution is not meant to be the silver bullet to the problem of automatically
transferring membership to the new room. It is just meant to alleviate a pain point in
upgrades while a better solution can be created.

Another problem with this proposal is that users are not told they are invited to this
new room. This is a designed feature of this proposal to prevent unnecessary notifications
to target users (they already get one that a room was upgraded, so another that they are
invited to a room would be confusing). Servers can of course ignore this proposal and
just spam invites if they wanted to.

To further clarify: because these events are treated very similar to invites, it is
possible to "kick" or ban a user from a room to prevent them from joining. This proposal
does not revoke an admin/moderator's ability to stop someone from joining/accepting
their invite.
