# MSC2967: API scope restriction

When a user logs in with a Matrix client, it gives this client full access to their Matrix account.

This introduces scopes to allow restricting client access to only part of the Matrix client API.

## Proposal

The [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964) introduces the usage of OAuth 2.0 to authenticate against a Matrix server.
OAuth 2.0 grants have scopes associated to them and encourage to ask for user consent when a client asks for a new scope that was not granted before.

This MSC does not attempt to define all the scopes necessary to cover the whole API, but lays out a base for that.

### Format

URN are widely used formats for OAuth 2.0 scopes.
All scopes related to Matrix must therefore start with `urn:matrix:`.

Calls to the Matrix client API, excluding calls that need UIA, must be restricted by scopes prefixed by `urn:matrix:api:`.
Calls to endpoints that currently need User-Interactive Authentication (UIA) must be restricted by scopes prefixed by `urn:matrix:sudo:`.

Protected resource can have both `read` and `write` operations.
`write` access to a resource implies `read` access to it.
Access to those operations are specified as the scope suffix, e.g. `urn:matrix:api:[resource]:read`.

### Globs

Scopes used by the Matrix client API support wildcard globs.
`urn:matrix:api:*` gives full access to the API (excluding UIA).
`urn:matrix:api:*:read` gives read-only access to the API.
Access to the `urn:matrix:sudo:*` can be time-restricted and require user re-authentication for sensitive operations.

Top-level wildcards (`urn:matrix:*` or `*`) are not valid and must be rejected by the authentication server.
Wildcards can only replace URN segments, e.g. `urn:matrix:a*` is invalid.

### Exact scopes

The exact scopes are intentionally not specified in this MSC.
The glob mechanism allows to the existing behaviour during a transition period while allowing further MSCs that introduces those exact scopes.

### Device handling

With the pre-MSC2964 authentication mechanism, a `device_id` was associated with the access token.
Since there are no such thing as a session in OAuth 2.0, this can be hardly mapped like this.

`device_id` can be bound to a client session via a scope with this format: `urn:matrix:device:[device_id]`.
If the client does not ask such a scope during the initial login, the authentication server must generate a new `device_id` and give it as a granted scope to the client.
A client can adopt and rehydrate an existing client by asking for its scope on login.
This also has a nice side-effect: if the device asked was never used by the client making the request, the authorization server will ask for explicit consent from the user.

The authentication server must only grant exactly one device scope for a token.
Wildcards are not allowed under the `urn:matrix:device:` prefix.

## Potential issues

The Device ID handling involves some custom logic on the authorization server side.
This means the Matrix server must be involved at some point in the authorization logic, which also involves implementation-specific code for each Matrix server implementation and OAuth 2.0 authentication server implementation.
This is not a problem when the Matrix server acts as the authorization server.

## Alternatives

Scope format could also have an URL format, e.g. `https://matrix.org/api/*/read`.
The URL prefix could either be static (`https://matrix.org`) or dependant on the homeserver (`https://matrix.example.com`).
In both cases, the URL could be confused with API endpoints and in the second case it would require discovery to know what scopes to ask.

The actual prefix as well as the `:api:`, `:sudo:` and `:device:` URN parts are open to debate.

## Security considerations

TBD

## Unstable prefix

None relevant.
