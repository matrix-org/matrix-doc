# Custom emoji and sticker packs in Matrix

This proposal is an iteration on [MSC1256](https://github.com/matrix-org/matrix-doc/issues/1256) which
uses pre-existing Matrix concepts (namely rooms) to achieve the same goals.

Having the ability to use custom emojis and stickers are often requested in various support channels,
and the show of support on MSC1256 in +1's alone reinforces just how much this feature is desired by
the community. Through some experimentation by the author, it is already possible to create custom
sticker packs when using the author's integration manager (Dimension) and dedicated bot - this
experimentation is a large driving factor for this proposal.

For scope, this proposal aims to give users the ability to define their own custom emoji and sticker
packs, share them, and actually use them. Rooms should also be able to recommend custom emoji and
sticker packs for members of the room to use. In future, communities/groups should be able to do the
same thing.

Some issues, related projects, and documentation on the matter are:
* https://github.com/vector-im/riot-web/issues/2950
* https://github.com/vector-im/riot-web/issues/2648
* https://github.com/vector-im/riot-web/issues/5157#issuecomment-340364320
* https://github.com/matrix-org/matrix-doc/pull/1174 - n.b. this is incorporated in this proposal.
* https://github.com/turt2live/matrix-dimension/blob/master/docs/custom_stickerpacks.md - documentation
  on using Dimension to achieve this, with links to matrix-sticker-manager which handles the curation
  aspect. Implementation is within the same repo.

## Proposal

Custom emoji and sticker packs are the same thing technically, just handled differently in the client.
Stickers in this proposal are the same `m.sticker`s found in the current Client-Server API specification.
Emoji in this proposal are intended to be rendered by clients in a similar fashion to how they'd render
regular unicode emoji in terms of sizing, positioning, etc. A "pack" is a collection of either emoji
or stickers.

Packs are to be mapped to dedicated rooms with the following semantics:
* The room name is the pack's display name.
* The room topic is the pack's description.
* The room avatar is a thumbnail for the pack. If not present, the first sticker/emoji should be used.
* The join rules and guest access control who is able to see the pack. For example, an invite only room
  would not be sharable without inviting people directly.
* Specific state events (defined later) represent other metadata for the pack, such as the stickers/emoji
  and who created it.
* The power levels define who is able to edit the pack.
* Deleting a pack would be done by making the room invite only and kicking everyone.

The room is just a plain Matrix room, therefore concepts like ACLs and upgrades still apply. As a note
for implementations, pack metadata should be transferred when room upgrades happen to preserve the pack.
Implementations should use the event timeline as a sort of comment section for the pack.


#### Sharing packs with other users

Sharing is achieved by sharing a link to the room, or inviting someone. There is no explicit grammar for
what the room's alias should be as the presence of the pack metadata state events is an indicator that
the room is a pack.

Sharing can also be done through distributing plain `http` or `https` URLs which are able to point to the
room in which the pack is defined. The intent is that 3rd party services can create sticker packs and
distribute user friendly or SEO optimized URLs, such as `https://packs.example.org/1234/official-sheltie-pack`.
When approached with  `Accept: application/json` or have `.json` appended to the end of the URL, the
following JSON body should be returned:
```json
{
    "room_uri": "https://matrix.to/#/%23_stickerpack_example%3Aexample.org"
}
```

The `room_uri` is a URI which references a Matrix room. Currently that means a `matrix.to` URI however
with future proposals that could be `mx://` or similar style schemes. When not approached with the
intent of JSON, the response is up to the application serving the content. For example, this would be a
good opportunity to render the sticker pack for viewing by a human.


#### Recommending which packs to use in a room

Rooms can recommend which packs to use for members viewing the room by setting a state event which looks
like the following:
```json
{
  "type": "m.room.recommended_packs",
  "sender": "@travis:t2l.io",
  "content": {
    "packs": [
      "https://matrix.to/#/%23_stickerpack_sample1%3Aexample.org",
      "https://matrix.to/#/%23_stickerpack_sample2%3Aexample.org"
    ]
  },
  "state_key": "",
  "origin_server_ts": 1554344486692,
  "event_id": "$D4h43bYVTf48tDTfkja6ROV13yJrzGUNGj7pySOVj6E",
  "room_id": "!gdRMqOrTFdOCYHNwOo:example.org"
}
```

If a client is making use of an embedded picker (such as the stickerpicker widget), it will need to send
this information to the picker when it is opened. Building on [MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236),
when a widget is approved the `m.sticker` capability, a `toWidget` action of `recommended_packs` is sent
roughly around the same time a `visibility` action would be sent to show the picker. The `data` of
`recommended_packs` is:
```json
{
    "room_id": "!gdRMqOrTFdOCYHNwOo:example.org",
    "packs": [
      "https://matrix.to/#/%23_stickerpack_sample1%3Aexample.org",
      "https://matrix.to/#/%23_stickerpack_sample2%3Aexample.org"
    ]
}
```

The `room_id` is the room ID where the packs are recommended and `packs` is verbatim from the
`m.room.recommended_packs` state event content. The picker is then responsible for showing the packs to
the user. The picker must acknowledge the `recommended_packs` action with an empty `response` object.
Clients making use of their own picker are responsible for showing the packs to the user. In either
case (built-in picker or widget), the application is not required to automatically show the whole pack
to the user - a step where the user approves the use of the pack (potentially enabling it for all rooms)
is encouraged.

There is no current specification for an emoji picker widget, however future proposals which add this
are encouraged to support the `recommended_packs` action.


#### Tracking changes in sticker packs

To track changes to packs, the interested application would join the pack's room. In the case of clients
using their own picker, the logged in user would join the room (potentially with the client's assistance
through dedicated UI/UX) - the client should hide the pack's room from the user where applicable, such as
by not showing it in the room list. Pickers would perform the same action, however instead of using the
logged in user's account they would use a bot account in the background to keep track of the pack. How
this is accomplished is left as an implementation detail.

How the application tracks changes is up to the application. For instance, this may be done with the `/sync`
API or via Application Services.


#### State events in the pack room

There are two kinds of special events which appear in a pack's dedicated room: `m.pack.metadata` for
the pack's metadata and zero or more `m.pack.item` for the stickers/emoji themselves. Both event types
are state events. The presence of a `m.pack.metadata` event indicates that it is a pack room.

A `m.pack.item` event looks as follows:
```json
{
  "type": "m.pack.item",
  "sender": "@travis:t2l.io",
  "content": {
    "uri": "mxc://example.org/media_id",
    "description": "This is where a short sentence explaining the sticker goes",
    "shortcodes": [
        ":sample:",
        ":cool_sticker:"
    ]
  },
  "state_key": "ThisIsTheItemIdToDistinguishItFromAnotherItem",
  "origin_server_ts": 1554344486692,
  "event_id": "$D4h43bYVTf48tDTfkja6ROV13yJrzGUNGj7pySOVj6E",
  "room_id": "!gdRMqOrTFdOCYHNwOo:example.org"
}
```

`shortcodes` are best explained as tags which can be used to find the item in the pack. They are arbitrary
strings which clients (and pickers) should use to recommend things to the user. In the case of emoji, these
will typically be surrounded in colons whereas stickers may simply have emoji like 🙂 and 😥. `shortcodes`
are optional.

The `description` is required and should be a human representation of the emoji or sticker. The description
should be a single short sentence, but has no length limit.

The `uri` is required and is a Matrix Content URI to the represented emoji or sticker.

The `state_key` of the item is the ID for the item. This is referenced by the `m.pack.metadata` event for
listing which items are active.

Items which have empty content or do not meet the schema should be considered inactive, even if the
`m.pack.metadata` event recommends otherwise. This allows for an item to be deleted more easily from the
pack, with the understanding that state in Matrix is permanent. Redacted `m.pack.item` events should be
handled in this same way.


A `m.pack.metadata` event looks as follows:
```json
{
  "type": "m.pack.metadata",
  "sender": "@travis:t2l.io",
  "content": {
    "active_items": [
        "ThisIsTheItemIdToDistinguishItFromAnotherItem-1",
        "ThisIsTheItemIdToDistinguishItFromAnotherItem-2"
    ],
    "creator": "https://matrix.to/#/%40alice%3Aexample.org",
    "author": "https://matrix.to/#/%40alice%3Aexample.org",
    "license": "CC-BY-NC-SA-4.0",
    "kind": "m.stickers"
  },
  "state_key": "ThisIsTheItemIdToDistinguishItFromAnotherItem",
  "origin_server_ts": 1554344486692,
  "event_id": "$D4h43bYVTf48tDTfkja6ROV13yJrzGUNGj7pySOVj6E",
  "room_id": "!gdRMqOrTFdOCYHNwOo:example.org"
}
```

`active_items` (required) are the `state_key`s of the `m.pack.item` events which should be considered
active in the pack, provided they meet the criteria previously mentioned.

The `creator` (required) is the person who created the pack, but not necessarily authored it. This is
generally  used by third party services which allow users to upload items which they have not created.
This must be a valid `http`, `https`, or `matrix.to` (in future `mx://`) URI.

The `author` is optional and if not provided is assumed to be the same as the `creator`. This is the
person who authored the items contained within the pack. For example, if the pack was commissioned by
the `creator`, this would be the person who did the artwork. This must be a valid `http`, `https`, or
`matrix.to` (in future `mx://`)  URI.

The `license` is required and must be a valid SPDX identifier. This applies to all the items contained
within the pack.

The `kind` must be either `m.stickers` for a sticker pack or `m.emoji` for emoji. This is the hint used
by applications to determine how best to handle items.

While the presence of an `m.pack.metadata` event signifies that the room is a pack room, if the event
is invalid then it should be treated as an error by applications.


#### Representation of packs on `m.sticker` events

To cover [matrix-doc#1174](https://github.com/matrix-org/matrix-doc/pull/1174), a new optional field
is to be added to `m.sticker` events: `pack_url`. This is the sharable URI for the pack which contains
the sticker, if the sticker is contained within a known pack. For example, this may be a `matrix.to`
(or `mx://` in future) URI or a URL which the application can resolve to a room as per earlier in this
proposal.

Because access control is handled by Matrix itself, applications should not omit the field if the pack
is private and instead send it anyways.


#### Representation of custom emoji in messages

Emoji are intended to be represented inline as `<img>` elements in the HTML body. For the plain text
representation, the shortcode the user used (or the first one) should be used. Using the `mxc://` URI
for the item, the `img` element should look similar to:
```html
<img src="mxc://example.org/media_id" width="16" height="16"
     alt="This is the item's description"
     data-mx-pack="https://matrix.to/#/%23_stickerpack_sample1%3Aexample.org" />
```

The `src` is the `mxc://` URI of the item, and the `alt` is the description of the item. The `width`
and `height` are provided as a fallback for clients which do not support custom emoji. Clients which
do support custom emoji can ignore the dimensions and use whatever is appropriate for their purposes.
The `data-mx-pack` attribute has the same requirements as the `pack_url` for stickers mentioned above.


## Tradeoffs

This proposal does not define an emoji picker widget similar to the existing sticker picker widget. An
emoji picker would be best served as a dedicated proposal due to the complexity involved in defining
its behaviour, such as how it interacts with a client's potential autocomplete mechanics. Similarly,
the sticker picker widget is minimally extended in this proposal to push the problem of enhanced client
interaction to a future proposal. Clients are likely to want to handle custom emoji themselves anyhow
for integration with their autocomplete mechanisms and for general performance.


## Security considerations

Due to the heuristics of `m.pack.metadata` events, it is possible for moderators to hide rooms from
existing members by applying the state event. Moderators already have several opportunities to damage
a room, and are already considered in a place of trust to not do so maliciously - therefore, this
risk of mitigated by having trusted moderators and administrators in a room, just like with any other
new state event which would be added.

The sharable URL for a pack could leak information about who created it or what it contains, potentially
subjecting the user to personal risk. It is expected that implementations handle this appropriately
where possible, such as by giving the creator the option to create private packs with randomly generated
room aliases to hide their contents from outsiders.
