# MSC2964: Matrix profile for OAuth 2.0

The current authentication mechanisms in Matrix does look like a lot like OAuth 2.0 without most of its security mechanisms.
This MSC is part of a change to replace Matrix authentication mechanisms with OAuth 2.0.
This MSC in particular defines how clients should authenticate with OAuth 2.0 to access the Matrix Client-to-Server API.

## Proposal

### Terminology

**OAuth 2.0** is an authentication framework. Authentication systems are built on top of OAuth2. It is based on numerous RFCs by the IETF.

**OpenID Connect** is a set of specifications defining a standard auth system built on top of OAuth2. Often abbreviated OIDC. Specs to know about: OIDC Core defines the actual auth system, OIDC Discovery defines the discovery of OP metadata, OIDC Registration allows clients to register themselves dynamically.

An **Authorization/Authentication Server** (AS) or **OIDC Provider** (OP) in the context of OIDC is the service that fulfills an authentication request. In the context of Matrix, it is either the homeserver itself acting as the OP or an external one like Keycloak, Auth0, etc.

A **Resource Server** (RS) is a protected service that requires authentication. In the context of Matrix, the homeserver is a RS.

A **Resource Owner** (RO) is an end user.

A **Relying Party** (RP) (client applications) is an app using resources from RS on behalf of the RO. In the context of Matrix, Matrix clients like Element Web are RP.

A **User-Agent** (UA) is a thing that hosts client applications, like a web browser.

### Assumptions and existing specifications

This change assumes the client (RP) knows what authentication server (AS) it should use.
The AS discovery is defined in [MSC2965](https://github.com/matrix-org/matrix-doc/pull/2965).

It also assumes the client (RP) is already known by the authentication server (AS).
The client registration process is defined in [MSC2966](https://github.com/matrix-org/matrix-doc/pull/2966).

The goal of this MSC is not to explain how OAuth 2.0 works but rather what mechanisms of OAuth 2.0 RP and AS are expected to implement.
This is done to ensure interoperability between Matrix clients and Homeservers while ensuring that the login flow is secure.

### Client profiles

#### Native and browser-based clients

This client type applies to clients that are running directly on the user-agent.
These clients are either browser-based or are capable of interacting with a separate web browser to have the user interact with the authentication server.

Those clients must use the authorization code flow by directing the user to the authorization endpoint to obtain authorization.
After the user authenticated and authorized the client, the user's web browser is redirected to a URI hosted by the client with an authorization code.
The client then exchanges the authorization code to obtain an access token using the token endpoint.

Those clients are public and therefore must use [PKCE](https://tools.ietf.org/html/rfc7636) with the S256 code challenge mechanism.

The authorization must issue refresh tokens for those type of clients if requested by them.

#### Server-based clients

This client type applies to hosted clients.
These clients must be capable to redirect the user to have them interact with the authentication server.

As with native and public browser-based clients, they must use the authorization code flow to obtain authorization.
Those clients are confidential and must authenticate their requests to the authorization server with their client credentials.

The authorization must issue refresh tokens for those type of clients if requested by them.

#### TBD

Restricted input clients like TVs might use the [Device Authorization Grant](https://tools.ietf.org/html/rfc8628).
CLI tools might use the [Client Credentials Grant](https://tools.ietf.org/html/rfc6749#section-4.4).

The details of those are still TBD.

### Requests to the authorization endpoint

When making a request to the authorization endpoint, clients must provide an unpredicatble value for the `state` parameter and validate it when returning to the redirect URI.
They must ensure the `state` value is securely tied to the current session.

The redirect URIs used by the clients must match exactly with the ones registered to prevent open redirection attaks.
The full redirect URI must be included in the authorization request.

The client might include a login hint to what MXID the user is trying to use.

The scopes the client can request are defined in [MSC2967](https://github.com/matrix-org/matrix-doc/pull/2967).

Sample authorization request:

```
https://account.example.com/oauth2/auth?
    client_id     = s6BhdRkqt3 &
    response_type = code &
    redirect_uri  = https://app.example.com/oauth2-callback &
    scope         = openid urn:matrix:* &
    state         = ewubooN9weezeewah9fol4oothohroh3 &
    nonce         = aazeiD3ahmai6ui9eiveiphochoyaewi &
    login_hint    = mxid:@john:example.com &
    code_challenge        = 72xySjpngTcCxgbPfFmkPHjMvVDl2jW1aWP7-J6rmwU &
    code_challenge_method = S256
```

### Requests to the token endpoint

When exchanging the `code`, clients must include their `client_id` and the `redirect_uri` they used for the initial request.
The server must verify they match for this `code`.

If PKCE was used in the authorization request (required for public client), the client must include the `code_verifier` and the server must validate it.

If the client is confidential, it must authenticate by including its `client_secret`.

TBD: should confidential clients use [JWT assertions](https://tools.ietf.org/html/rfc7523#section-2.2) instead?

```
POST /oauth2/token HTTP/1.1
Host: account.example.com
Content-Type: application/x-www-form-urlencoded
Accept: application/json

grant_type=authorization_code
  &code=iuB7Eiz9heengah1joh2ioy9ahChuP6R
  &redirect_uri=https%3A%2F%2Fapp.element.io%2Foauth2-callback
  &client_id=s6BhdRkqt3
  &code_verifier=ogie4iVaeteeKeeLaid0aizuimairaCh
```

```json
{
  "access_token": "2YotnFZFEjr1zCsicMWpAA",
  "token_type": "Bearer",
  "expires_in": 299,
  "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
  "scope": "openid urn:matrix:api:*",
  "id_token": "..."
}
```

The access token must be short-lived and should be refreshed using the `refresh_token` when expired.

### Existing authentication types equivalence

The current authentication mechanism can have multiple stages allowing to ask users to perform certains actions.
This includes:

- social login (`m.login.sso`), with multiple providers ([MSC2858](https://github.com/matrix-org/matrix-doc/pull/2858))
- complete a CAPTCHA (`m.login.recaptcha`)
- agree to terms of services and privacy policies (`m.login.terms`, [MSC1692](https://github.com/matrix-org/matrix-doc/pull/1692))
- TOTP/2FA (`m.login.totp`, [MSC2271](https://github.com/matrix-org/matrix-doc/pull/2271))

All of this can be done by the authentication server without any modification to the specification.

### Replacement of UIA

Some API endpoints use User-Interactive Authentication to perform some higher-privileged operations, like deleting a device or adding a 3PID.
An equivalent behaviour can be achieved by temporarily upgrade the client authorization with additional scopes.

Whenever the client ask for a token (either with a refresh token or by initiating a authorization code flow) the authentication server returns the list of scopes for which the token is valid.
This helps client track what scopes they currently have access to, and let them upgrade temporarily a token with additional scopes to perform privileged actions.
The authorization server can also downgrade the scopes of a session after a certain time by returning a reduced list of scopes when refreshing the token.
The scope definitions are out of scope of this MSC and are defined in [MSC2967](https://github.com/matrix-org/matrix-doc/pull/2967).

### User registration

User can register themselves by initiating a authorization code flow with the `prompt=create` parameter as defined in [_Initiating User Registration via OpenID Connect - draft 03_](https://openid.net/specs/openid-connect-prompt-create-1_0.html).

### Logging out

TBD. [OIDC Frontchannel logout](https://openid.net/specs/openid-connect-frontchannel-1_0.html) might be helpful.

## Potential issues

There are still many open questions that need to be adressed in future MSCs.
This includes:

- using OAuth 2.0 to authenticate application services
- account management, including active session management
- interactions with widgets and integrations
- 3PID logins
- guest logins

The current authentication mechanism will be deprecated later on, but a migration period where the two authentication mechanisms cohabit needs to exist.
This is doable in clients but harder to do in servers.
One requirement for a smooth migration is to adopt [MSC2918](https://github.com/matrix-org/matrix-doc/pull/2918).
The migration path and the deprecation of the current APIs will be done in a separate MSC.

## Alternatives

None relevant.

## Security considerations

Since this touches one of the most sensitive part of the API, there a lot of security considerations to have.
The [OAuth 2.0 Security Best Practice](https://tools.ietf.org/html/draft-ietf-oauth-security-topics-16) IETF draft has many attack scenarios.
Many of those scenarios are mitigated by the choices enforced in the client profiles outlined in this MSC.

## Unstable prefix

None relevant.
