# MSC2703: Media ID grammar

*Media IDs are the identifiers accompanied by a domain in an MXC URI: `mxc://domain/mediaId`*

Implementations currently rely on assumptions and commonality for media IDs due to lack of specification.

## Proposal

Media IDs must be treated and represented as opaque identifiers. Only characters in the
[RFC 2986 Unreserved Characters](https://tools.ietf.org/html/rfc3986#section-2.3) set can be used.

Media IDs must be less than 255 characters.

## Potential issues

The character set could be overly restrictive, however in practice at 255 characters there's a very
reasonable number of possible identifiers. If a server does find itself running out, we can adjust
the spec or they could deploy a secondary server to handle even more media.

## Alternatives

We could go without this specification, but that sounds very unfortunate.

## Security considerations

None applicable.

## Unstable prefix

None required.
