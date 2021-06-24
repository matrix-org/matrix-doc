# MSC2705: Animated thumbnails

Some clients would like animated versions of media for thumbnail purposes. The use cases vary, however
the common ask is frequent enough to warrant an MSC.

## Proposal

By specifying `animated=true` in the query string for a `/thumbnail`, the server SHOULD return
an animated thumbnail for the media if possible. When the parameter is `false` the server SHOULD NOT
attempt to generate a thumbnail, as many implementation do today.

If the server supports the flag, it MUST support animating the following mimetypes:
* `image/gif`
* `image/png` (for animated PNGs - non-animated PNGs cannot be supported)

Other potential formats include videos and other image types - servers can support additional types
at their discretion.

If media cannot be animated, a static thumbnail should be returned instead. For example, if the client
requests `?animated=true` on a JPEG the server should not error but instead just return the downsized
JPEG as though the request was `?animated=false`.

When thumbnailing, servers SHOULD return one of the following types:
* `image/jpeg` (or `image/jpg`)
* `image/png` (non-animated)
* `image/gif` (animated)

The server's discretion about which one to use is trusted here. Servers can return alternative formats,
however currently it is strongly recommended that servers do not deviate from the set described here.

The default for `animated` is intentionally left undefined due to a variety of use cases within the
ecosystem which could demand that either `true` or `false` be preferred. Instead of picking a value,
servers SHOULD NOT animate thumbnails by default, but are not required to respect this condition. An
example use case would be a chat platform which is based on Matrix advertising the feature and wanting
to use pre-existing clients. They could go around and fork all the Matrix clients out there, or they
could have their server return a GIFs for everything.

## Potential issues

Server load could increase when the server tries to thumbnail a large file. Servers are expected to
mitigate this on their own, such as by providing an option to disable the feature or limiting how/when
they will animate the media.

## Alternatives

None that have presented themselves as reasonable.

## Security considerations

As mentioned, servers could face resource issues if this feature is left unchecked.

## Unstable prefix

While this MSC is not in a released version of the spec, implementations should use `org.matrix.msc2705`
as a prefix. For example, `?org.matrix.msc2705.animated=true`. No unstable endpoints are required due
to backwards compatibility.

## Implementations

This MSC is already implemented by matrix-media-repo.
