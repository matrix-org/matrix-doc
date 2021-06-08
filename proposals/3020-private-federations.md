# Support for private federation networks

In an ideal world, Matrix would be one big public network, where everyone is
able to communicate with everyone else.  In practice, we do not live in an
ideal world, and much as the Web and Email are fragmented into private
intranets, we're aware of several large Matrix deployments which do not yet
federate with the public internet.

Therefore, we need a way to link to content within these private federations
without deep-linking to a specific client.

This MSC extends [MSC2312](https://github.com/matrix-org/matrix-doc/pull/2312) to
propose a URI scheme extension to support linking to content within the
context of a given private federation network.

## Proposal

The matrix: (and matrix.to) URI scheme is extended to support the optional query
parameter `network`.  This parameter's value is a reverse-DNS identifier which indicates the
private federation in which this URI is valid.

We also add a new capability `m.networks` to the CS `/capabilities` endpoint
to let the server report which networks it can connect to.  The value of the
capability gives an array of reverse-DNS identifiers to indicate the available
networks. `m.internet` is defined as a special case to describe the public Internet,
and in the absence of the capability, the server should be assumed to support just
`m.internet`.

For example, to indicate that a given server is able to participate in the
[Tchap](https://www.numerique.gouv.fr/outils-agents/tchap-messagerie-instantanee-etat/) network
and a hypothetical NATO network (but not the public internet), the capability would be:

```json
'm.networks': [
    "fr.gouv.tchap",
    "int.nato"
]
```

When a Matrix client consumes a matrix URI with a `network` parameter, it
checks via the capabilities API if its current server is part of the specified
network. If it isn't, then the client should handle the matrix URI as if
onboarding the user for the first time as described in MSC2312 - i.e.
redirecting them to the `default_client` (or matrix.to, if none is specified).

For instance `matrix:u/matthew:somewhere.tchap.gouv.fr?network=fr.gouv.tchap&default_hs=public.tchap.gouv.fr&default_client=https://www.tchap.gouv.fr`
would be the right shape of uri to link into Tchap.
