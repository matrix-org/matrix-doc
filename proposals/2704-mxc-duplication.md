# MSC2704: Handling duplicate media on `/upload` + clarifying the origin of an MXC URI

Currently some servers will de-duplicate media in an unpredictable way whereas others will not.
Further, some implementations have the capability to return a potentially unexpected origin for
their MXC URIs. This proposal aims to acknowledge the status quo by specifying it explicitly.

## Proposal

MXC URIs can have an origin which does not match the server name on `/upload`. This is currently
implied as potentially being possible under the specification, however this MSC aims to make that
behaviour to be valid and expected by clients. This means, for example, that `@alice:example.org`
could receive an MXC URI pointing to `mxc://cdn.upstream.com/abc123`. No changes are implied by the
origin: it is to be looked up like any other domain name, just as it does today.

Servers SHOULD NOT attempt to "deduplicate" media by returning the same MXC URI for previously
uploaded content, unless the upload meets requirements outlined below. Uploads are often accompanied
by a single reference in an event, and in a world where it is possible to delete media by event ID
it is important to be able to delete a specific record without side effects. How the implementation
handles this internally is up to it - it just cannot return the same MXC URI for what appears to
be the same content.

If the server wants to support deduplication, it should only do so when the media (body), uploader,
origin homeserver, and provided filename all match. This scenario could be perceived as a missed
request on the client side and therefore could be a retry.

## Potential issues

Enforcing that media cannot be deduplicated at the MXC URI level could lead to media ID exhaustion
on the server side, however by explicitly allowing the server to return a different origin for the
URI the pool of potential IDs is unbounded.

By explicitly allowing the server to return a `content_uri` which does not match their server name
the server could potentially imply that media was uploaded to a different server. For example, a user
wishing to upload to `example.com` could be told that their media got uploaded to the public `matrix.org`
homeserver instead. This is perceived by the proposal as a bad idea and needs no enforcement to prevent,
as unless the server managed to gain access to `matrix.org` the media will safely 404.

Implementations may have already deduplicated media such that one MXC URI does not reference one event,
however the intent is to fix the problem going forward and less so resolve the past. Some clients also
have "Forward" features which do not re-upload media, which would cause multiple events to reference
the same media.

## Alternatives

We could not handle deduplication at the spec level, however this leaves implementations open to issues
down the line when we do support deleting/erasing media.

We could also not allow the returned `content_uri` to reference another server. The use case for allowing
this specific behaviour is to allow media to be hosted by a dedicated CDN-like service instead of forcing
all traffic through the homeserver.

## Security considerations

Some considerations are mentioned in the Potential Issues section.

Though not mentioned in the specification, servers can already lie about the MXC URI being returned,
such as always returning a reference to the same image regardless of what was uploaded. This is not
solved by this proposal, and generally not perceived as a legitimate threat currently.

## Unstable prefix

No unstable prefixes are required for this MSC.
