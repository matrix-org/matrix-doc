# MSC3088: Room subtyping

Rooms have traditionally been used for conversation, however in recent times it has become more relevant
that rooms can serve non-conversational purposes. [MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840)
describes how to best identify a room's purpose, particularly for not-chat rooms, but does not cover
potentially mutable types within those coarse types. This MSC aims to describe scenarios where rooms
may wish to change subtype within a larger MSC1840 type.

This is a ground-up remake of [MSC2773](https://github.com/matrix-org/matrix-doc/pull/2773), and extends
[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) a bit.

*Author's note: The use cases for this are somewhat weak. Suggestions for what sorts of problems this
MSC might solve are appreciated.*

## Problem case: DMs

DMs, if made [canonical](https://github.com/matrix-org/matrix-doc/pull/2199), would need a way to 
fluidly change between being a DM and a not-DM. This MSC proposes one approach for how that could
work, though does acknowledge that it's not great for members of a DM to decide it's suddenly not
a DM for everyone.

## Problem case: Spaces, but not quite spaces

[Spaces](https://github.com/matrix-org/matrix-doc/pull/1772) are a structure which help organize rooms
into a tree-like hierarchy. It's perceivable that an implementation of Matrix could want a Space to
organize their non-conversational data with the benefits that a Space would provide. Those sorts of
spaces are unlikely to be useful to a user, and as such should be hidden from their conversational
clients - this MSC defines a way for clients to detect those kinds of rooms, and handle them accordingly.

## Proposal

A new state event, `m.room.purpose`, is defined with a namespaced state key representing that purpose.
The state event's contents would be metadata specific to that purpose, plus a flag to aid removal
of purposes until [deleting state events](https://github.com/matrix-org/matrix-doc/issues/456) is
possible.

`m.enabled` in the event content signifies whether the room is actively using that purpose. If,
and only if, `true` the purpose applies. This means to remove a purpose a sender would redact
the event, omit the `m.enabled` field, set it to `false` or set it to otherwise invalid data
(such as `"no"` - strings are not interpreted as valid values).

Other fields in the `content` should be namespaced at all times to help differentiate Matrix
identifiers from others.

Note that this structure intentionally allows rooms to serve more than one purpose in addition to
their higher order type (from MSC1840). If a room consists of solely unknown purposes, the client
should make an assumption which is best aligned to the higher order type. Because this assumption
can and does change between the types, this MSC does not list any requirements. An example might
be to treat a Space room as a data-driven space if the client doesn't recognize the purposes of the
room. Clients should be wary of accidentally considering *no* purpose as unknown purpose: these rooms
would be pure representations of their higher order type.

This MSC does not currently propose any purposes of its own. The following are examples of what
other MSCs could introduce.

### Example: Canonical DMs

Canonical DMs define a concept of DM mutability and that DMs can have "important" users for a
given power level. This is what that mutable flag could look like, taking into consideration a
theoretical configurable importance power level.

```json5
{
  "type": "m.room.purpose",
  "state_key": "m.dm",
  "content": {
    "m.enabled": true,
    "m.importance_level": 50
  }
}
```

### Example: Data-driven Space

If someone were to be (ab)using Spaces to represent data-only structures, they'd potentially do something
like the following:

```json5
{
  "type": "m.room.purpose",
  "state_key": "m.data",
  "content": {
    "m.enabled": true
  }
}
```

## Potential issues

Rooms having multiple purposes, or purposes which conflict with the room's type, might be confusing
to clients and ultimately end users. Rooms should not be created in these confusing ways, and will
generally have at most 1 purpose given to them. MSCs which introduce new purposes should consider
and describe the behaviour when applied to "unexpected" room types.

## Alternatives

[MSC2773](https://github.com/matrix-org/matrix-doc/pull/2773) is the closest available alternative to
this, though lacks the mutability and shared understanding this MSC offers. MSC2773 failed to specify
a way for the `m.kind` to be known over federation, for example.

[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) also serves as a viable option if one
were to define types like `m.room_type.space.data_driven`. This sort of additional subtyping approach
would generally mean that any server-side behaviour needs to consider multiple types when handling
the rooms, leading to unnecessary server implementation. Purposes are generally intended to define how
clients behave rather than servers, and thus should be in the client space of the spec.

## Security considerations

As mentioned, mutable purposes by moderators/admins of the room might not help the DM use case at a
minimum: it would be unfortunate, though maybe required, to have your DM partner de-DM your room.

Other security considerations TBD.

## Unstable prefix

While this MSC is not in a stable version of the specification, implementations should use `org.matrix.msc3088.`
in place of `m.` for identifiers. This means `org.matrix.msc3088.room.purpose` and `org.matrix.msc3088.enabled`.
