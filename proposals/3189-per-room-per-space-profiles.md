# MSC3189: Per-room/per-space profiles

People frequently have different identities in different communities. In the
context of Matrix, users may therefore want their display name or avatar to
appear differently in certain social contexts, such as within a room or a space.

While most clients technically already support per-room display names (by
getting profile data from a user's membership events in a room), this feature
is undocumented and lacks server-side support. Thus, this proposal introduces a
more robust concept of per-room/per-space profiles along with a dedicated API to
manage them.

## Proposal

First, the existing behavior: When showing a user's display name or avatar in a
room, clients should reference the `displayname` and `avatar_url` attributes of
the user's `m.room.member` state. In the past, some clients have taken advantage
of this behavior by modifying `m.room.member` state directly in order to set
per-room profiles, however this is deprecated in favor of the more robust system
of profile management proposed in this MSC. As such, clients must be aware that
direct changes to `m.room.member` state may be overwritten without warning.

### Profile scope and inheritance

While `m.room.member` state in individual rooms is sufficient for communicating
how users should appear, we would like per-room/per-space profiles to be a more
first-class concept, so that managing them is simple for clients. For this
purpose, an optional query parameter `scope` which takes a room ID is added to
all `/_matrix/client/r0/profile` endpoints. When specified, `scope` changes the
profile endpoints to interact not with the user's global profile, but with the
profile specific to the given space/room.

With regards to profile data, a space/room can be in one of two states: either
it has a custom profile set via the above `scope` API, in which case it is known
as a *profile root*, or it *inherits* its profile data from another profile root
(i.e. one of its ancestor spaces or the user's global profile). By default, all
rooms and spaces are set to inherit from the global profile. Thus, when profile
updates happen, the server uses this inheritance data to determine which rooms
the update affects, and updates their `m.room.member` state accordingly.

Inheritance is represented in the profile APIs by the optional property
`inherits_from` in request and response bodies. In profile `GET` requests, it
accompanies the relevant profile data for the space/room to indicate where this
data is coming from (either `global` or an ancestor space ID):

```
GET /_matrix/client/r0/profile/@me:example.org?scope=!space1:example.org

{
  "inherits_from": "global",
  "avatar_url": "mxc://example.org/myglobalavatar",
  "displayname": "My global display name"
}
```

In `PUT` requests, `inherits_from` can be specified instead of
`avatar_url`/`displayname` to set which of a room's ancestor spaces (or the
global profile) to inherit from. Note that even though there are separate `PUT`
endpoints for `avatar_url` and `displayname`, setting `inherits_from` on either
of them will affect both, since inheritance applies to the entire profile.

```
PUT /_matrix/client/r0/profile/@me:example.org/avatar_url?scope=!space1:example.org

{
  "inherits_from": "!space2:example.org"
}
```

On the other hand, if a `PUT` request is made without `inherits_from`, it turns
the space/room into a profile root, by copying whatever the previous profile was
and then updating the relevant `avatar_url`/`displayname` property.

Finally, if a profile `PUT` request does not specify `scope`, it behaves as
global profile updates currently do, except it only affects the `m.room.member`
state of rooms and spaces that inherit from `global`. This ensures that global
profile updates will not overwrite per-room/per-space profiles.

### Propagating inheritance

In order to give per-space profiles the desired semantics, whenever a space's
profile settings are updated, its children must be updated as well to inherit
from the right place. The following table outlines the transformations that may
occur for a space A, and how they affect its children:

||from `inherits_from` B|from profile root|
|-|-|-|
|to `inherits_from` C|All children of A that inherited from B recursively changed to inherit from C|All children of A that inherited from A recursively changed to inherit from C|
|to profile root|All children of A that inherited from B recursively changed to inherit from A|No change in inheritance|

### <a id="inheritance-restrictions"/>Inheritance restrictions

In addition, there are some restrictions on what a space/room may inherit from.
If a space/room A inherits from a space B, then B must be an ancestor of A
(determined by following `m.space.child` links), and there must be a direct path
in the space-child graph from B to A that only passes through children which the
user has joined and which are *not* profile roots. This is to prevent
undesirable situations such as a space A having a subspace B which has a child
room C, where B is a profile root and yet C somehow inherits from A.

### Automatic inheritance changes

Per-space profiles are only really useful if they automatically propagate to
newly joined/added rooms and subspaces. Also, servers generally need to keep
track of when rooms and subspaces are left/removed in order to ensure that the
above inheritance conditions are upheld. For these reasons, servers implementing
per-room/per-space profiles must apply the following rules:

- When the user joins a space/room, perform a breadth-first search for an ancestor space that is a profile root, by following `m.space.child` links backwards through spaces the user has joined. Break any ties by selecting the first in a lexicographic ordering of room IDs, and then set the joined space/room to inherit from this profile root, or the global profile if none is found. This profile data should go immediately into the initial `join` state, rather than being updated after the join is complete.
- When the user leaves a space A, if A was a profile root, reset every space/room that inherited from A to inherit from `global`. Otherwise if A inherited from a space B, reset every child of A that inherited from B to inherit from `global`.
- When the user adds a space/room A to a space B, if A inherited from `global` and B is a profile root, set A to inherit from B. Otherwise if A inherited from `global` and B inherits from a space C, set A to inherit from C.
- When a space/room A is removed from a space B (whether by the user or someone else), if A inherited from a space C, check whether A is still allowed to inherit from C by [the above rules](#inheritance-restrictions). If this is no longer the case, then reset A to inherit from `global`.

### Errors

Given that this proposal expands the surface of the profile APIs, there are some
new ways in which they can fail:

- The `scope` profile APIs are only for interacting with one's own profiles. Thus if a user attempts to set/get another user's profile for a given `scope`, the server must return a 403 with `M_FORBIDDEN`.
- Similarly, if a user attempts to set/get their profile for a `scope` which they have not joined / might not exist, the server must return a 403 with `M_FORBIDDEN`.
- If the user attempts to set `inherits_from` to an [invalid value](#inheritance-restrictions), the server must return a 400 with `M_UNKNOWN` along with a more specific explanation.

## Potential issues

There is a pre-existing issue with the profile APIs, namely that updating one's
profile is an O(n) operation with the number of rooms it affects, often taking
multiple minutes to complete on larger accounts. Arguably this should be solved
as part of this proposal by linking through to
[extensible profile rooms](https://github.com/matrix-org/matrix-doc/pull/1769)
in `m.room.member` state, which would allow the most common use-case of profile
updates to be O(1). While this is not undertaken here due to the significant
added complexity, this proposal is structured in a way to hopefully be
compatible with any future changes in this direction.

## Alternatives

An alternative would be to store all per-room/per-space profile data in a single
global [extensible profile](https://github.com/matrix-org/matrix-doc/pull/1769),
essentially keeping a public mapping of room IDs → profile data. However, this
alternative would leak data about users' profiles in private rooms, which is a
significant privacy concern, and it is unclear how conflicting profiles would
affect the "one source of truth" given by `m.room.member` state.

## Security considerations

None that I am aware of.

## Unstable prefix

During development of this feature the versions of the profile APIs augmented
with `scope` will be available at unstable endpoints:

```text
GET /_matrix/client/unstable/town.robin.msc3189/profile/{userId}
GET /_matrix/client/unstable/town.robin.msc3189/profile/{userId}/avatar_url
PUT /_matrix/client/unstable/town.robin.msc3189/profile/{userId}/avatar_url
GET /_matrix/client/unstable/town.robin.msc3189/profile/{userId}/displayname
PUT /_matrix/client/unstable/town.robin.msc3189/profile/{userId}/displayname
```
