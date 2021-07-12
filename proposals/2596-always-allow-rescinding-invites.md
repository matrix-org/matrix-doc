# Proposal to always allow rescinding invites
Disinviting is equivalent to kicking, which means currently you need the kick
power level to disinvite someone. This can cause embarassing situations if you
accidentally invite someone and don't have the power level to rescind it.

## Proposal
The proposed fix is a modification to the authorization rules to always allow
rescinding invites that you sent. The modifications are applied on top of room
version 6. In section "5. If type is `m.room.member`" -> "d. If `membership`
is `leave`", a new step is added after step `iv`:

> v. If the *target user*'s current membership state is `invite`, and the `sender`
  of that membership event is the same as `sender`, allow.

The existing step `v` is not modified, but is now step `vi`.

If this modification were applied as-is, users could send a new invite event
for users who are already invited and then disinvite them. Therefore, an
additional modification to the "c. If `membership` is `invite`" section is
needed. Step `iii` is modified to add `invite` to the list of prohibited
previous membership states:

> iii. If *target user*'s current membership state is `invite`, `join` or `ban`, reject.

## Potential issues
The additional modification to section 5.c prohibits changing invite event
content, such as the invite reason. It is uncertain if there are any use cases
for changing the reason after sending the invite.

Race conditions over federation could result in weird situations, as users
would have permission to change `invite`->`leave`, but not `join`->`leave`.
Hopefully the state resolution algorithm can handle those cases adequately.

## Unstable prefix
The vendor-prefixed room version `net.maunium.msc2596` can be used until the
proposal is assigned to a future official room version.
