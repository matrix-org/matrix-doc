# Proposal to leverage SRV records to discover homeservers from clients

Currently, the [specifications on server discovery by client](https://spec.matrix.org/unstable/client-server-api/#server-discovery) merely mentions the use of the `/.well-known/matrix/` HTTP path.
This comes in contradiction with the [specifications on server discovery by servers](https://spec.matrix.org/unstable/server-server-api/#server-discovery) which also leverage the existence of a SRV record.

Furthermore, this oddity makes the user front, arguably the most crucial part for technology
adoption, the most complicated when a HTTP path is not used by the Matrix instance operator.
For instance, in such a case, when an instance operator uses a `_matrix._tcp.example.org` SRV record
pointing to an `example.com` instance on port `8448`, the `example.org` hostname shall be used
in conjunction with the instance's (`example.com`) port for a client to find the homeserver.

This oddity strengthens when you consider the technologies at hand: by design, the hierarchical and
distributed design of DNS and the usual cache done by recursive (non-authoritative) resolvers,
distributed amongst different operators, makes it so extra DNS requests usually have small to no impact
on a target instance. On the other hand, HTTP endpoints scaling remaining in the hands of the end-of-line
operators, extra HTTP request _do_ have an immediate impact on them.

## Proposal

The `SRV` record shall be used as specified in the server -> server API for client -> server discovery.

## Tradeoffs

If current server -> server API is kept, an extra DNS lookup will only be made in case the HTTP one fails.
In case it is decided the `SRV` lookup shall be done first, the cost would still be minimal,
DNS being designed to scale.

## Additional information
This proposal would help proving clients, like Element, cf. [vector-im/element-web#15054](https://github.com/vector-im/element-web/issues/15054#issuecomment-681969376)
