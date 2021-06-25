# MSC 2385: Disable URL Previews
This MSC is an alternative suggestion to [MSC2376](https://github.com/matrix-org/matrix-doc/pull/2376).

Currently URLs posted in chat give a URL preview. Sometimes, for example with bots, this can be
unwanted. For instance if a bot is posting a message with a lot of links, or the content of the link
is already obvious from the message itself.

## Proposal
This proposal adds a new, optional key to `m.room.message` messages, named `url_previews`. It is an
array of strings containing the URLs a preview should be given to. If this key is absent, it is expected
that the client gives URL previews for all URLs present in the message body. If a URL is present in this key that is *not*
present in the body clients SHOULD NOT render a preview for that URL.

### Examples
No key added, preview to all URLs:
```json
{
	"msgtype": "m.text",
	"body": "Wow, check out this song! https://www.youtube.com/watch?v=oHg5SJYRHA0"
}
```

Empty array for `url_previews`, thus no URL preview at all:
```json
{
	"msgtype": "m.text",
	"format": "or.matrix.custom.html",
	"body": "Hey, look at what I did! [MSC2385: Disable URL Previews](https://github.com/matrix-org/matrix-doc/pull/2385)",
	"formatted_body": "Hey, look at what I did! <a src=\"https://github.com/matrix-org/matrix-doc/pull/2385\">MSC2385: Disable URL Previews</a>",
	"url_previews": []
}
```

Array of URLs to preview, only those in the array are previewed:
```json
{
	"msgtype": "m.text",
	"body": "https://example.com https://matrix.org",
	"url_previews": ["https://example.com"]
}
```

## Potential issues
URLs that should have a preview need to be sent twice - once in the body, once in `url_previews`. As
this feature is meant for bots, normal human clients would probably omit `url_previews` alltogether,
resulting in all URLs sent from them having a preview.

URLs in `url_previews` and in the body need to match exactly, which could be confusing with trailing
slashes (`/`).

## Alternatives
There could be an attribute added to the `<a>` tag which disables URL previews. See
[MSC2376](https://github.com/matrix-org/matrix-doc/pull/2376).

Instead of a whitelist there could also be a blacklist of URLs. However, as the likely scenario is a
bot wanting to surpress all the previews for its URLs sent it seems like a whitelist is more appropriate
here.

## Security considerations
You could get tricked more easily into being Rickroll'd. This can be alleviated by encouraging
clients to request previews explicitly (either by hovering or by clicking a special button next to
the link).
