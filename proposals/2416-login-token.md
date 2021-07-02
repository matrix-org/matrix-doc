# MSC2416: Add m.login.jwt authentication type
An appservice might want to log in to the homeserver as another user or a system administrator might
want an easy way to authenticating as someone else to be able to investigate an issue. Currently
two solutions for that exist: either using [shared secret auth](https://github.com/devture/matrix-synapse-shared-secret-auth)
or synapses unspeced `org.matrix.login.jwt` ([documentation](https://github.com/matrix-org/synapse/blob/master/docs/jwt.md)).
This proposal adds `m.login.jwt` properly.

## Proposal
The proposal adds JWTs ([Json Web Token](https://jwt.io/)) to the authentication type `m.login.jwt` upon login.
It is expected that the tokens are signed by a secret key. The algorithm of the JWT can be
configured by the homeserver. As this endpoint is meant to be used by automated processes like
application services there is no need to provide a mechanism to generate such tokens for clients.

The following claims are to be validated:

 - The `sub` claim must be present, and must be either the localpart or the full mxid of the user
 - The expiracy `exp`, not before `nbf` and issued at `iat` claims must be validated, if present. A
   homeserver MAY enforce existance of all or a subset of these claims
 - The issuer `iss` claim is optional, but is required and must be validated if the homeserver configures it
 - The audience `aud` claim is optional, but is required and must be validated if configured. If this
   claim is provided but not configured, authentification should fail

Whether to register new users via this endpoint or not is up to the homeserver.

An example JWT could look as follows:

Header:
```json
{
  "alg": "HS512",
  "typ": "JWT"
}
```

Payload:
```json
{
  "sub": "alice",
  "exp": 1579373788
}
```

A POST request to the `/_matrix/client/r0/login` endpoint could look as follows:
```json
{
  "type": "m.login.jwt",
  "token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTU3OTM3Mzc4OH0.4YXhRYNfzdns8qf60fE7pu9RKFt3uhxqj6y-Gy4d2bbDkQ5-mTbTNgDdi350ZMrY5VV22WHp_-BOjtGFkwOqgA"
}
```

### Differences to `org.matrix.login.jwt`
 - The server may enforce existing of `exp`/`nbf`/`iat` claims
 - The server may not allow registering new users via JWTs

## Potential Issues
A new login method is added which adds complexity.

## Alternatives
A `m.login.password` auth provider could be used to log in as someone as a special user. This,
however, feels rather hacky and not the intended purpose of `m.login.password`.

Instead of introducing a new `m.login.jwt`, the existing `m.login.token` could be expanded to accept both
a jwt and an sso token. This, however, seems unneededly complicated.

## Security considerations
Possession of the secret allows you to be logged in as anyone on that homeserver. As such, this
secret has to be kept securely.

## Unstable prefix
Instead of `m.login.jwt`, `org.matrix.login.jwt` is used, to have compatability with the existing synapse
jwt format
