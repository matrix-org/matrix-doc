# MSC2918: Refresh tokens

In Matrix, requests to the Client-Server API are currently authenticated using non-expiring, revocable access tokens.
An access token might leak for various reasons, including:

 - leaking from the server database (and its backups)
 - intercepting it with a man-in-the-middle attack
 - leaking from the client storage (and its backups)

In the OAuth 2.0 world, this vector of attack is partly mitigated by having expiring access tokens with short lifetimes and rotating refresh tokens to renew them.
This MSC adds support for expiring access tokens and introduces refresh tokens to renew them.

## Proposal

The access token returned by the login endpoint expires after a short amount of time, forcing the client to renew it with a refresh token.
A refresh token is issued on login and rotates on each usage.

Homeservers can choose to use signed and non-revocable access tokens (JWTs, Macaroon, etc.) for performance reasons if their expiration is short enough (less than 5 minutes).

### Login API changes

The login API returns two additional fields:

- `expires_in_ms`: The lifetime in milliseconds of the access token.
- `refresh_token`: The refresh token, which can be used to obtain new access tokens.

This also applies to logins done by application services.

Both fields are optional.
If `expires_in_ms` is missing, the client can assume the access token won't expire.
If `refresh_token` is missing but `expires_in_ms` is present, the client can assume the access token will expire but it won't have a way to refresh the access token without re-logging in.

### Account registration API changes

Unless `inhibit_login` is `true`, the account registration API returns two additional fields:

- `expires_in_ms`: The lifetime in milliseconds of the access token.
- `refresh_token`: The refresh token, which can be used to obtain new access tokens.

This also applies to registrations done by application services.

As in the login API, both field are optional.

### Token refresh API

This API lets the client refresh the access token.
A new refresh token is also issued.
The existing refresh token remains valid until the new access token (or refresh token) is used, at which point it is revoked.
This allows for the request to get lost in flight.
The Matrix server can revoke the old access token right away, but does not have to since its lifetime is short enough that it will expire anyway soon after.

`POST /_matrix/client/r0/refresh`

```json
{
  "refresh_token": "aaaabbbbccccdddd"
}
```

response:

```json
{
  "access_token": "xxxxyyyyzzz",
  "expires_in_ms": 60000,
  "refresh_token": "eeeeffffgggghhhh"
}
```

If the `refresh_token` is missing from the response, the client can assume the refresh token has not changed and use the same token in subsequent token refresh API requests.

The `refresh_token` parameter can be invalid for two reasons:

 - if it does not exist
 - if it was already used once

In both cases, the server must reply with a `401` HTTP status code and an `M_UNKNOWN_TOKEN` error code.
This new use case of the `M_UNKNOWN_TOKEN` error code must be reflected in the spec.
As with other endpoints, the server can include an extra `soft_logout` parameter in the response to signify the client it should do a soft logout.

This new API should be rate-limited and does not require authentication since only the `refresh_token` parameter is needed.
Identity assertion via the `user_id` query parameter as defined by the Application Service API specification is disabled on this endpoint.

### Device handling

The current spec states that "Matrix servers should record which device each access token is assigned to".
This must be updated to reflect that devices are bound to a session, which are created during login and stays the same after refreshing the token.

## Potential issues

The refresh token being rotated on each refresh is strongly recommended in the OAuth 2.0 world for unauthenticated clients to avoid token replay attacks.
This can however make the deployment of CLI tools for Matrix a bit harder, since the credentials can't be statically defined anymore.
This is not an issue in OAuth 2.0 because usually CLI tools use the client credentials flow, also known as service accounts.
An alternative would be to make the refresh token non-rotating for now but recommend clients to support rotation of refresh tokens and enforce it later on.

## Alternatives

This MSC defines a new endpoint for token refresh, but it could also be integrated as a new authentication mechanism.

## Security considerations

The time to live (TTL) of access tokens isn't enforced in this MSC but is advised to be kept relatively short.
Servers might choose to have stateless, digitally signed access tokens (JWT are good examples of this), which makes them non-revocable.
The TTL of access tokens should not exceed 15 minutes if they are revocable and 5 minutes if they are not.

## Unstable prefix

While this MSC is not in a released version of the specification, clients should add a `org.matrix.msc2918.refresh_token=true` query parameter on the login endpoint, e.g. `/_matrix/client/r0/login?org.matrix.msc2918.refresh_token=true`.
The refresh token endpoint should be served and used using the unstable prefix: `POST /_matrix/client/unstable/org.matrix.msc2918/refresh`.
