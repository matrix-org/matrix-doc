# MSC3216: Synchronized access control for Spaces

A mechanism like Spaces
([MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772), now merged) is
frequently used to group together rooms with different topics, that belong to
the same community or organization with a single moderation team and policy. To
this end, it should be possible to define both roles ("powerlevels") and
permissions ("required powerlevels") once and then have them apply to every room
in a Space.

[MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962) is one proposal
that aims to address the "roles" side, though not the "permissions" side.
Unfortunately, it has a high degree of complexity, does not fit well into the
existing protocol semantics, and has a lot of unanswered questions regarding
authorative homeservers which could lead to it becoming a de-facto centralized
mechanism.

This MSC proposes an alternative solution to the problem which does not suffer
from these issues, and which additionally also covers the "permissions" side of
the problem. *Unlike* the original MSC2962 (since split out into
[MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083)), however, it does
not address membership restrictions at all - I consider this a separate concern
which may not even be specific to Spaces, and therefore it should live in a
separate proposal. It would be neither a dependency nor a dependent of this
proposal.

## Proposal

Whereas MSC2962 addresses the problem from an angle of a specially-privileged
pseudo-user which is externally controlled with its own authorization rules,
this proposal instead addresses it as strictly a *replication* problem - if an
already-privileged user chooses to apply role or permission changes to a Space
as a whole, how can this be replicated to all of its child rooms in a
semantically consistent and predictable manner?

This approach has three main advantages:

1. It does not introduce an all-powerful pseudo-user with its own access control
   mechanisms. This avoids the entire class of [confused deputy
   problems](https://en.wikipedia.org/wiki/Confused_deputy_problem), where said
   pseudo-user could be abused by an attacker to make changes that they would
   not otherwise be permitted to make, if for any reason its access control
   mechanism didn't *exactly* match that of the normal powerlevel system.
2. All access control changes are made *directly* by the initiating user. This
   means that there is no question of which homeserver should be authoratively
   responsible for updating the powerlevels - the answer is always "the
   homeserver of the user making the changes". Likewise, it means that it is
   always clear from the room history who initiated the change, without needing
   further lookups.
3. It is completely agnostic to the actual powerlevel system used; since the
   proposal just concerns itself with *replication*, it does not matter *what*
   gets replicated, and so any future changes to the access control mechanism in
   the Matrix protocol would likely not require changes to this replication
   mechanism.

In the rest of this proposal, "roles" will be used to refer what are currently
the powerlevel assignments to specific users, and "permissions" will be used to
refer to what are currently the *required* powerlevels for executing some sort
of action.

The high-level mechanism works as follows: when a user updates either the roles
or permissions of a Space, their homeserver will, on their behalf, translate
this to a role/permission update for each room that the Space contains. If this
is not possible because the user has an insufficient role in some rooms, then
the operation will atomically fail unless an "allow partial" flag is set. If the
replication fails in *all* rooms, the operation will fail completely, with or
without the flag.

UI-wise, this allows for roughly three scenarios:

1. The user has the necessary role in all of the Space's rooms, and the
   operation succeeds at once. This is the common case for Spaces which are
   correctly set up to provide multiple topic rooms for a single community or
   organization.
2. The user has the necessary role in some but not all of the Space's rooms. In
   this case, the flag-less operation will fail, and the user can be prompted
   whether they would like to apply the change to those rooms where it is
   possible anyway. If the user chooses yes, the operation is reattempted, but
   this time with an "allow partial" flag, and it succeeds. This case will
   typically occur when a Space is not correctly set up, or in private Spaces
   for the user's personal bookmarking/categorization purposes.
3. The user does not have the necessary role in any of the Space's rooms. The
   operation will fail. This is also typical for private Spaces.

The prerequisite for correct setup of a Space, such that this replication
mechanism will function as intended, is for at least one user to have a
sufficient role in all of the Space's rooms - where "sufficient" means "has the
necessary role to apply all of the intended access control changes, including
future ones". In practice, the easiest way to satisfy this requirement under
typical circumstances is to ensure that they are an Admin (PL 100) in all of the
Space's rooms.

From this point on, the "bootstrapping user" can then simply define the rest of
the roles and permissions for the Space, which gets replicated to all of its
rooms; those with a sufficient role on this replicated list can then,
transitively, start to use the Spaces access control replication mechanism
themselves, as *their* roles are now also consistent across rooms. In this way,
the mechanism keeps itself consistent across rooms over time, so long as no
rules are defined directly in a specific room that interfere with it (such as a
single-room demote).

Such interfering rules may actually be desirable in some cases; for example,
preventing a specific user from obtaining a specific role in a specific room,
despite holding it in the rest of the Space. Because of this, replicated roles
and permissions are defined separately in `m.room.power_levels` from the
explicitly-given ones; this works similarly to MSC2962, where the
explicitly-given settings take precedence.

### Technical changes

The `m.room.power_levels` event would be extended with a `space_defaults`
property, which may contain all of the same keys (except for `space_defaults`
itself) that an `m.room.power_levels` event may contain directly.

Additionally, an `m.space.power_levels` state event would be introduced, which
stores the most recent replicated powerlevels directly into the Space. This
event does not play a role in the state resolution algorithm, and only serves as
a way for clients to learn what the most recent Space-level powerlevels were set
to, for UI/display purposes. This way, clients do not need to pull the
`space_defaults` from multiple rooms and try to work out which of them actually
belong to this specific Space.

The state resolution algorithm would be modified so that instead of the current
permission/role lookup algorithms...

```
kick / ban / invite / redact -> 50
events[type] -> state_default / events_default -> 50 / 0
users[mxid] -> users_default -> 0
```

... the algorithms are changed to include a lookup in the `space_defaults`, like
so:

```
kick / ban / invite / redact -> space_defaults.kick / space_defaults.ban / space_defaults.invite / space_defaults.redact -> 50
events[type] -> space_defaults.events[type] -> state_default / events_default -> space_defaults.state_default / space_defaults.events_default -> 50 / 0
users[mxid] -> space_defaults.users[mxid] -> users_default -> space_defaults.users_default -> 0
```

Note that a `space_defaults` lookup for specific users and event types is done
__before__ using a local event/user default like `state_default`; otherwise, it
would not be possible for a Space to specify any specific entries at all
whenever a local default is set. Essentially, "check specific before general
levels" has precedence over "check local before space levels".

For this to work correctly, it's important that clients and homeserver
implementations *do not* automatically set any permissions in a newly-created
room, other than those which the user has explicitly asked for - explicitly
reproducing the defaults in an `m.room.power_levels` event would result in the
fallback to `space_defaults` never occurring.

A new API endpoint would be created at `POST
/_matrix/client/r0/spaces/{spaceId}/set_power_levels`, taking a `power_levels`
property that defines the new power levels to apply to the Space's rooms (to be
inserted in the `space_defaults` property of each room's power levels event),
and an `allow_partial_update` property that implements the behaviour described
earlier.

XXX: An endpoint prefix of `/rooms` could also be used instead of `/spaces`?
This would be consistent with eg. the `join` and `invite` routes, but since this
operation is only semantically meaningful on a Space, it should perhaps *not* be
consistent in that way.

Subspaces should be accounted for, and treated as a part of the Space, for the
purpose of this operation; that is, all rooms in subspaces (to arbitrary depth)
should have the powerlevel changes applied to them, likewise causing a failure
if this is not possible for some rooms.

The following error responses may occur for this endpoint:

- __200__ - Operation succeeded as requested; either all or some rooms have been
  updated, depending on the `allow_partial_update` flag.
- __403 M_FORBIDDEN__ - Reserved for Space-level permission issues, eg. if there
  were to be some kind of required permission in the Space itself for doing a
  replicated powerlevel change. This proposal does not currently define such a
  mechanism, but reserves it to avoid confusion with permission issues caused by
  rooms.
- __403 M_ALL_FORBIDDEN__ - The user does not have the necessary access to
  change powerlevels in *any* of the rooms in the Space. Retrying with
  `allow_partial_update` will still fail.
- __403 M_PARTIALLY_FORBIDDEN__ - The user does not have the necessary access to
  change powerlevels in *some* of the rooms in the Space. Retrying with
  `allow_partial_update` will likely succeed; though a client should still
  account for receiving an `M_ALL_FORBIDDEN` in that case, eg. if the user's
  role in the affected rooms changes in the meantime.

XXX: Should we allow a homeserver to always return M_PARTIALLY_FORBIDDEN even
when *none* of the rooms can be updated, eg. for performance reasons? This would
make it difficult for clients to present a coherent UX, as a "do you want to
apply the change to only some of the rooms" dialog will be shown even in cases
where choosing "yes" could never result in success anyway - which would be
confusing messaging to users.

If successful, the response body is as follows:

```js
{
  "partialSuccess": true, // Whether only some rooms succeeded (true) or *all* rooms succeeded (false)
  "failedRooms": [ // A list of room IDs of those rooms whose powerlevels could *not* be updated
    "!room1:homeserver.tld",
    "!room2:homeserver.tld",
    "!room4:homeserver.tld"
  ]
}
```

## Potential issues

1. This approach will require a new room version to be specified, which takes
   into consideration `space_defaults`. The same is true, however, for MSC2962.

2. With this approach, powerlevel changes will be published as an event created
   by the user who actually initiated them, rather than a bot. While this
   removes a certain degree of anonymity from moderation operations, that
   anonymity can be regained by simply outsourcing this job to a bot user if a
   given community desires to have this property.

3. Determining whether a powerlevel change was "successfully replicated" is
   dependent on having an accurate view of the *current* permissions and roles
   of each affected room. There may be circumstances where the initiating user's
   homeserver is 'behind' on this, and so their homeserver may end up
   (incorrectly) reporting success, with the change being reverted down the
   line. This is already currently the case for regular powerlevel changes, and
   should be quite rare, so I don't feel that this is a significant problem.

4. It is possible for a room to be "desynced" from the Space when one room
   moderator removes the role of another, making it impossible for them to do a
   replicated powerlevel change across the Space without using the 'partial'
   flag. While this doesn't literally *break* anything, it can be confusing for
   a moderator to be faced with an unexpected warning dialog, and there should
   probably be some mechanism for debugging such desyncs; eg. a way to see the
   specific rooms in the Space where the user's role diverges from the other
   rooms.

5. If a room is added to multiple Spaces, and receives different replicated
   powerlevel changes through both of them, the room's powerlevels can
   "oscillate" between those of the two Spaces. This is mainly a UX issue.

## Alternatives

Those listed in
[MSC2962](https://github.com/matrix-org/matrix-doc/blob/matthew/msc2962/proposals/2962-spaces-access-control.md#alternatives),
as well as MSC2962 itself.

## Security considerations

As stated above, a major consideration for choosing this approach is that it's
not prone to confused deputy problems.

It does not introduce any new security mechanisms, other than a small mechanical
change in state resolution, the correctness of which can be easily reasoned
about.

## Unstable prefix

Unstable implementations should use the following identifiers:

- Space-level state event: `net.cryto.msc3216.space.power_levels` instead of
  `m.space.power_levels`
- Space defaults property: `net.cryto.msc3216.space_defaults` instead of
  `space_defaults`
- API endpoint:
  `/_matrix/client/unstable/net.cryto.msc3216/spaces/{spaceId}/set_power_levels`
  instead of `/_matrix/client/r0/spaces/{spaceId}/set_power_levels`
- Room version: `net.cryto.msc3216.1`
