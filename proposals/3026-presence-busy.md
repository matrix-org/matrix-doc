# MSC3026: `busy` presence state

The current specification for presence in Matrix describes three states:

* `online` if the user is online and active
* `unavailable` (aka idle or away) if the user is online but inactive
* `offline` if the user is offline

There is currently no presence state to express that the user is online and
active, but busy, i.e. in a state that would prevent them from giving their full
focus to solicitations from other users. A practical example would be a user
that's on a call with another user (or on a group call).


## Proposal

A new presence state is added, `busy`, which describes a state where the user is
online and active but is performing an activity that would prevent them from
giving their full attention to an external solicitation, i.e. the user is online
and active but not available.

It is left to the implementation to decide how to update a user's presence to
the `busy` state (and from this state to another); suggestions would include
allowing the user to set it manually, setting it automatically when the user
joins a call or a Jitsi group call, etc..

If a user's presence is set to `busy`, it is strongly recommended for
implementations to not implement a timer that would trigger an update to the
`unavailable` state (like most implementations do when the user is in the
`online` state). This is because there are some valid use cases for the user not
triggering any event in the client but still being online and active, e.g. if
they're on a call, and because such automation while taking the specific
semantics of the `busy` state into account is complex when the user is using
multiple devices.

For backwards compatibility, servers implementing this MSC must expose a flag in
`/_matrix/client/versions` responses, under `unstable_features`, named
`org.matrix.msc3026.busy_presence`, which is set to `true`. Before setting a
user's presence to `busy`, clients must check the presence of this flag and that
it's set to `true`. If it's not, clients should fall back to setting the user's
presence state to `unavailable`, which is the closest state to `busy`
semantically.


## Potential issues

It is unclear whether introducing a new presence state will break some clients
that don't implement this MSC yet. If this happens, the mitigation is unclear
and open to discussion.


## Unstable prefix

Until this proposal is merged into a stable version of the Matrix specification,
implementations must use `org.matrix.msc3026.busy` instead of `busy` as the new
presence state.
