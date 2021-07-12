# HS -> AS authorization header
Most of the auth tokens in the spec are passed in the `Authorization` header,
with the `access_token` query parameter supported for backwards-compatibility.
For some reason, the application service spec was not updated in the same way
and it still requires using the archaic query parameter when the homeserver
pushes transactions to the appservice.

## Proposal
The `access_token` query parameter is deprecated and homeservers are encouraged
to use the `Authorization` header with `Bearer <token>` as the value when
sending transactions or other requests to application services.

Application services MUST support checking the access token from the header.
Appservices SHOULD still support the old query param auth, but it is not
required, as there are no cases where a homeserver is unable to set HTTP
request headers.

### Transition to auth header
Similarly to how [legacy routes](https://matrix.org/docs/spec/application_service/r0.1.2#legacy-routes)
work in the appservice spec, homeservers should prefer using the authorization
header, but fall back to the query parameter if the appservice returns a status
code indicating invalid auth (401 or 403).

## Security considerations
Not fixing this causes access tokens to be logged in many bridges.

## Alternatives
The transition could be done differently, e.g. with an appservice registration
field or homeserver config. Some sort of version identifier in appservice
registrations would be the optimal solution (define that after vX, auth always
uses the header), but such an identifier does not currently exist.

## Unstable prefix
The authorization header is already used in the client-server spec, and an
unstable prefix would just unnecessarily complicate things. If the transition
is decided to be done with an appservice registration field, then that field
could have an unstable prefix.
