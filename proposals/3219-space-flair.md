# MSC3219: Space Flair

[Spaces](https://github.com/matrix-org/matrix-doc/pull/1772) introduced an improved way of organizing rooms into tree-like 
structures in Matrix. Its predecessor, Groups, had a concept of "flair" (or "related groups" at the technical level) where 
users could have a smaller version of the Group's avatar next to their name in messages they send, if they've enabled flair. 
This primarily only worked in public Groups.

This proposal brings in a similar mechanic for Spaces, using the space-room's avatar as the flair.

## Proposal

Rooms can list the spaces (or technically, rooms) they want to appear as flair for users through a `m.room.flair` state event 
with empty state key. The `content` would look similar to:

```json5
{
    "spaces": [
        {"room": "!room:example.org", "via": ["matrix.org", "example.org"]},
        {"room": "#alias:example.org"},
    ]
}
```

`via` is optional but recommended for routing purposes. The `room` can be a room ID or alias. Clients would peek these rooms to 
get their avatar/aesthetic state events for representation. Clients are recommended to only show flair for rooms which are actually 
spaces, though this proposal doesn't impose any limitations in rooms enabling flair of other non-space rooms.

This approach also allows rooms to enable flair for private spaces if the user viewing the flair is in the private space, though 
this is not seen as a realistic usage scenario given users joined to the space would be able to identify the other space members 
(typically).

Flair is disabled by default for all users. Individual members can set a `"m.flair": true` flag on their own membership event in 
the relevant space to enable visibility of their flair. Clients should ignore this flag on non-`join` membership events to prevent 
inviters, moderators, etc from "enabling" flair for the user without being an active participant. Servers are expected to preserve 
the flag, if present, when changing profile information for the user (displayname/avatar). When not explicitly `true`, flair should 
be considered disabled.

## Alternatives

### Extensible profiles ([MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769))

Extensible profiles are commonly referred to as profiles-as-rooms, where each user has a personal room which represents their "profile" 
(display name, avatar, etc). Because this room is, well, a room it means that it can contain arbitrary state (metadata) that user 
wishes to make public, such as Flair. 

Flair in a profiles-as-rooms setup could be achieved with an `m.flair` (or `m.space.flair`?) state event which lists the Spaces the 
user wishes to make public. This would mean that clients "peek" into profile rooms to determine changes to flair, but could also mean 
that clients have to peek spaces too for cross-referencing. [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) had some 
[prior art](https://github.com/matrix-org/matrix-doc/pull/1772/commits/cd5a8420a8849b980df14df7dcc40c69a21bbbcd) on how this could work, 
such as by including membership event IDs in the flair event and having the server validate the reference itself.

However, we don't have profile rooms today. This may change before this proposal can be considered, though.

## Potential issues/dependencies

Aside from extensible profiles, this proposal largely relies on peeking over federation being functional, which is covered by 
[MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444). Clients might prefer a simpler (non-deprecated) peek API as well, as 
covered by [MSC2753](https://github.com/matrix-org/matrix-doc/pull/2753).

## Security considerations

Most of the security considerations revolve around private, or semi-private, membership to Spaces. Because flair only works if the 
link between a user and a Space can be verified, this means that the Space must either be exposed publicly for peeking or accept that 
flair will not work for non-members. This effectively means disclosing either all of the members of a Space, or none. The problem of 
exposing only a subset of state to non-members is considered functionality for a future/different MSC.

Clients should additionally be aware that Spaces can be peekable (history set to `world_readable`) but *not* joinable (join rules of 
`invite` or similar). This can also represent how a community can create a concept of "official" members by inviting them to a peekable, 
but non-public, space. Flair would be enabled for this Space to denote official community members.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3219` as a namespace. This means `m.room.flair` 
becomes `org.matrix.msc3219.room.flair` and `m.flair` becomes `org.matrix.msc3219.flair` for example.
