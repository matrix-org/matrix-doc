# Remove Authentication on /submitToken Identity Service API

[MSC2140](https://github.com/matrix-org/matrix-doc/pull/2140) added
authentication to `v2` endpoints of the Identity Service API. A few endpoints
were exempt from this requirement, but others were not.

As a result, two that do require authentication are the `/submitToken`
endpoints:

* [`GET /_matrix/identity/v2/validate/email/submitToken`](https://matrix.org/docs/spec/identity_service/r0.3.0#get-matrix-identity-v2-validate-email-submittoken)
* [`GET /_matrix/identity/v2/validate/msisdn/submitToken`](https://matrix.org/docs/spec/identity_service/r0.3.0#get-matrix-identity-v2-validate-msisdn-submittoken)

These endpoints are meant to be called by a user's browser when they click a
validation link in their email. These links do not contain access tokens, as
that would be a major security risk.

Additionally, while access tokens are intended to identify a user and bring
authentication, these particular endpoints already contain session ID,
client_secret and token parameters, which serve to identify and authenticate
the user already. Thus a general access token serves no purpose here.

## Proposal

The above mentioned endpoints should have the requirement of authentication
removed.

## Potential issues

None. Riot web and mobile clients (which are the only currently known
implementations of v2 3PID validation) already operate this way. The spec is
just wrong here.

## Security considerations

As stated above, the existing parameters already serve to authenticate the
user making the request.

The alternative that the spec suggests, sending an access token as part of a
validation email, is far more dangerous.
