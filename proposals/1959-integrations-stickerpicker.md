# MSC1959: Sticker picker API

[MSC1951 - Custom sticker packs and emojis](https://github.com/matrix-org/matrix-doc/pull/1951) adds a way
for pack authors to share their creations with other users, however the interaction between them and the
sticker/emoji pickers themselves are not defined. Although this proposal does not include an emoji picker
definition, the API it proposes can easily and transparently be extended to such a widget.


## Proposal

Some clients may wish to not embed the sticker picker widget into their application and instead get the sticker
packs and render them as one common picker. To do this, the client would use the `api_url` specified in the
widget's `data`. If the `api_url` is a trusted integration manager, the client should make requests to the API
endpoints defined in this proposal using
[MSC1961 - Integration manager authentication](https://github.com/matrix-org/matrix-doc/pull/1961). If the
URL is not trusted, the user should be prompted for approval or the sticker picker skipped by the client.

#### GET /_matrix/integrations/v1/widgets/{widgetId}/packs

Retrieves the packs (as defined by MSC1951) for the sticker picker. In future, this API could be used by an
emoji picker widget if it were to exist. No additional information is required to make the request, besides
authorization tokens. The token should belong to the user which also owns the picker widget.

An example response is:
```json
{
    "packs": [
        {
            "kind": "m.stickers",
            "name": "My Cool Stickerpack",
            "description": "This is the topic from the pack's room",
            "thumbnail": "mxc://example.org/media_id",
            "sharable_url": "https://packs.example.org/1234/my-cool-stickerpack",
            "creator": "https://matrix.to/#/%40alice%3Aexample.org",
            "author": "https://matrix.to/#/%40alice%3Aexample.org",
            "license": "CC-BY-NC-SA-4.0",
            "active_items": [
                {
                    "id": "ThisIsTheItemIdToDistinguishItFromAnotherItem-1",
                    "uri": "mxc://example.org/media_id",
                    "description": "This is where a short sentence explaining the sticker goes",
                    "shortcodes": [
                        ":sample:",
                        ":cool_sticker:"
                    ]
                },
                {
                    "id": "ThisIsTheItemIdToDistinguishItFromAnotherItem-2",
                    "uri": "mxc://example.org/media_id_2",
                    "description": "Words go here",
                    "shortcodes": [
                        ":words:",
                        ":example:"
                    ]
                }
            ]
        }
    ]
}
```

Note that the pack object in the response is very similar to that of a `m.pack.metadata` event containing
`m.pack.item` events. The additional fields are `name` (required), `description` (optional), `thumbnail`
(optional - use first item's `uri` if not present), and `sharable_url` (required). The `active_items`
array has also been modified to be `m.pack.item` event contents with an added `id` field for tracking
purposes.

#### PUT /_matrix/integrations/v1/widgets/{widgetId}/packs

Adds a new pack to the picker. The picker is responsible for resolving the sharable URL provided and tracking
changes to it. The response is 200 OK with a pack object (see `GET` version of this API above).

An example request body would be:
```json
{
    "sharable_url": "https://packs.example.org/1234/my-cool-stickerpack"
}
```

#### DELETE /_matrix/integrations/v1/widgets/{widgetId}/packs

Similar to the `PUT` version, this deletes a pack from the picker. The picker is expected to resolve the
sharable URL provided to determine which pack needs to be removed. If the pack was removed, an empty
JSON object with 200 OK is returned. The request body is the same as the `PUT` version of this endpoint.
