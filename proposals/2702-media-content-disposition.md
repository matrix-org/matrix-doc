# MSC2702: `Content-Disposition` usage in the media repo

Clients and servers often disagree on how the `Content-Disposition` header should work with respect
to uploads. This proposal aims to settle the disagreement while standardizing the behaviour.

## Proposal

The `Content-Disposition` header becomes required on `/download` and `/thumbnail`, with `/download`. When
a `filename` was supplied to `/upload`, `/download`'s `Content-Disposition` MUST have a filename attribute.

For `/thumbnail`, the `Content-Disposition` MUST be `inline` (with optional server-generated filename).

For `/download`, the attribute MUST be one of `inline` or `attachment`. The server SHOULD intelligently
decide which of the two to use, such as by implying all `image/*` content types are `inline` and binary
blobs are `attachment`s.

To allow for clients to specifically request a behaviour, a new query string parameter is added to
`/download` to let clients pick explicitly which one they would like: `asAttachment`. When not
supplied, the server's default processing is to be used. When supplied as `true`, the server MUST
use `Content-Disposition: attachment` (with possible filename). When supplied as `false`, the server
MUST use `Content-Disposition: inline` (with possible filename).

This proposal does not advocate to let clients specify the entire header out of caution.

## Potential issues

Servers could "intelligently" decide to always use `inline` by default (as they currently do). This
is acceptable under this proposal, though not advocated by the author.

## Alternatives

We could settle the debate by picking one or the other, however from past discussions not everyone
would be happy with the result. Currently clients link to the `/download` endpoint as a literal "download
this" button (implying they'd like `attachment`) whereas others use the endpoint as a fallback, allowing
users to click on it to view the content in their browser. We could introduce an additional `/preview`
or `/view` endpoint which changes the implicit behaviour of the header, however this solution feels like
unneeded endpoint sprawl.

## Security considerations

None known.

## Unstable prefix

While this MSC is not included in a spec release, implementations should use `org.matrix.msc2702` as a
prefix. For example, `?org.matrix.msc2702.asAttachment=true`. As this is backwards compatible otherwise,
no special endpoint is required.
