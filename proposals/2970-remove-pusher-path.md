# MSC2970: Remove pusher path requirement

Recently Synapse was updated to enforce the specified restriction that the URI
for HTTP pushers have a path component of `/_matrix/push/v1/notify`
([synapse#8865](https://github.com/matrix-org/synapse/pull/8865)).

Prior to this change, the ability to use arbitrary paths for pushers had been
found useful for various applications. Examples include:

* Projects such as [matrix-gotify](https://gitlab.com/Sorunome/matrix-gotify)
  offer a mechanism for push notifications which is independent from Google's
  FCM or Apple's push system. These setups, however, typically have a URL
  specific to a device, which is incompatible with the requirement for a fixed
  path.

* Push notifications could be sent directly to the IPv6 address of a phone, if
  it is known. However, depending on implementation, it might be difficult to
  arrange to receive pushes on a specific path.

In general, having a path requirement for the pushers basically forces app
developers to implement and host matrix-specific gateways, instead of just
being able to push general json blobs directly to devices. The removal of the
pusher path requirement would *greatly* increase flexibility here.

## Proposal

The requirements for the `url` parameter for [`POST
/_matrix/client/r0/pushers/set`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-pushers-set)
are relaxed. In particular:

 * The path need no longer be `/_matrix/push/v1/notify`.
 * The requirement that the URL be `https` is extended to allow `http`, but
   strongly recommend `https`.

Some additional constraints are added to ensure compatibility between implementations:

 * The URL MUST contain a valid host, with an optional port. IP literal
   addresses are permitted, in accordance with [RFC3986
   3.2.2](https://tools.ietf.org/html/rfc3986#section-3.2.2).
 * The URL must NOT contain a fragment (ie, it may not contain the character
   `#`). (It *may* contain a query-string.)
 * The URL must NOT include a "userinfo" section (ie, the host may not be
   preceded by a `user@` specification).
 * The URL must consist solely of ASCII characters. (Unicode hostnames should
   be Punycode-encoded. Non-ASCII bytes in the path should be percent-encoded.)
 * The URL may not exceed 8000 characters in length.


### Versioning

One reason that the constraint on paths was introduced was to allow the future
introduction of new, incompatible, push formats - with the intention that the
homeserver pick the format to be used based on the path in the URL of the
pusher.

It is proposed instead that this could be done by changing the `kind` of
pusher: for example by setting it to `httpv2`.

## Potential issues

The removal of the path constraint potentially makes it easier to construct
HTTP magnification/DoS attacks, using the homeserver as a proxy.

It could also make it easier to construct attacks against internal
infrastructure (ie, SSRF attacks). This is somewhat lessened by the fact that
an attacker has no way to read the response to such a request, but blind 
SSRF attacks are still possible.

Although these are valid concerns, we note that Matrix Pushes are not
significantly different in this respect to many other "webhook" systems (for
example, Github's
[webhooks](https://docs.github.com/en/developers/webhooks-and-events/about-webhooks)
system and [AWS
SNS](https://docs.aws.amazon.com/sns/latest/dg/sns-http-https-endpoint-as-subscriber.html)),
which have no such constraint.

Rather, we propose that these attacks be mitigated by other controls such as
the following -- all of which are important anti-abuse controls regardless of
whether the URL path is restricted:

 * All outgoing HTTP requests from the Homeserver should be subject to an IP
   address blacklist, so that the server administrator can prevent access to
   internal resources.

 * We could require that the push endpoint respond to an empty `ping` request -
   and in particular that it must respond at the time that the pusher is
   configured. This would significantly reduce the scope for abuse by directing
   pushes to inappropriate endpoints.

   However, it is considered out-of-scope for this MSC.

 * Outgoing requests must be subject to rate-limiting, to prevent individual
   users creating large volumes of requests. Additionally, there should be a
   per-user limit on the total number of pushers.

 * If a push endpoint does not give a valid response at all (for example, over a
   period of 7 days), the pusher should be disabled.

## Alternatives

### Partial constraints on URI paths

An alternative approach would be to allow more flexibility in the push endpoint
path, whilst still imposing some constraints. For example, we might say that
the path must start with, or end with, `/_matrix/push/v1/notify`. Such an
appproach might help to mitigate SSRF attacks whilst still allowing some
flexibility for alternative implementations.

We consider that requiring that the path *start* with `/_matrix/etc` offers too
little flexibility for some implementations, and that requiring that it *end*
with `/_matrix/etc` offers little protection. For example, an attakcer might
configure a pusher with an endpoint
`https://example.com/app%3Fx%3D/_matrix/etc`, which then appears as a request
to `/app` with a query-string.

In short, we consider the benefits of such an approach are minor.

### Leave the HTTPS requirement in place

Arguably the relaxation of the requirement that the push endpoint be HTTPS is
orthogonal, but we consider this a good time to reconsider that requirement.

In short, there are various deployment strategies - in particular, where a push
gateway is known to be hosted on the same infrastructure as the homeserver -
where the requirement for HTTPS is unnecessarily onerous. In most scenarios,
HTTPS is preferable for obvious reasons, but We don't consider it the job of
the pusher API to enforce this.

### Disallow query-strings

We could also disallow query-strings in the URL. However, these are also useful
in certain applications (in particular, they are sometimes used for addtional
authorization).

## Security considerations

As described above, this change could make DoS and SSRF attacks easier, and it
is important that good countermeasures be put in place before such a change.

## Unstable prefix

We do not anticipate making a public release of the changes proposed here
before the MSC is accepted; an unstable prefix is therefore not required.
