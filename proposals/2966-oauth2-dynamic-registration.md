# MSC2966: Usage of OAuth 2.0 Dynamic Client Registration in Matrix

[MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964) defines how client should login against a Matrix server using OAuth 2.0.
It assumes the client is known to the authentication server.

This MSC specifies how Matrix clients should leverage OAuth 2.0 Dynamic Client Registration Protocol ([RFC 7591](https://tools.ietf.org/html/rfc7591)) to register themselves before initiating the login flow.

## Proposal

If a Matrix server wants to be used by any third-party client, its authentication server must allow dynamic registration of OAuth 2.0 clients.
The client registration endpoint is advertised in the OIDC discovery document and can be used as per [RFC 7591 sec. 3](https://tools.ietf.org/html/rfc7591#section-3).

### Client metadata

When registering itself, a client must provide a list of metadata about itself.

As per [RFC 7591 sec. 2.2](https://tools.ietf.org/html/rfc7591#section-2.2), some of those metadata values may be localized.

```json
{
  "client_name": "Digital mailbox",
  "client_name#en-US": "Digital mailbox",
  "client_name#en-GB": "Digital postbox",
  "client_name#fr": "Boîte aux lettres numérique"
}
```

Some of those metadatas are optional in the RFC but required in this context.

| Name             | Description                                                                                                 | Behaviour                                        | Localizable |
| ---------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ----------- |
| `client_name`    | Human-readable name of the client to be presented to the user                                               | Required                                         | Yes         |
| `client_uri`     | URL of a web page providing information about the client                                                    | Optional                                         | Yes         |
| `logo_uri`       | URL that references a logo for the client                                                                   | Optional                                         | Yes         |
| `contacts`       | Array of strings representing ways to contact people responsible for this client, typically email addresses | Required                                         | No          |
| `tos_uri`        | URL that points to a human-readable terms of service document for the client                                | Required                                         | Yes         |
| `policy_uri`     | URL that points to a human-readable policy document for the client                                          | Required                                         | Yes         |
| `redirect_uris`  | Array of redirection URIs for use in redirect-based flows                                                   | Required with the `authorization_code` grant ype | No          |
| `response_types` | Array of the OAuth 2.0 response types that the client may use                                               | Defaults to `["code"]`                           | No          |
| `grant_types`    | Array of OAuth 2.0 grant types that the client may use                                                      | Defaults to `["authorization_code"]`             | No          |

Other metadata registered in the IANA [OAuth Dynamic Client Registration Metadata](https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#client-metadata) registry might be used and supported by Matrix servers and clients.

### User consent

When authorizing a third-party client for the first time, the authorization server must ask for explicit user consent and display as much information, preferably localized, about the client as possible.
This includes informations about the publisher, the clients terms of service and its policy.

The consent screen must include a human-readable list of the scopes requested by the client.

### Metadata signature

To securely identify themselves, clients must send a digitally signed version of their metadata.
This is done by encoding the client metadata in a JWT and signing it.

In addition the client metadata mentioned earlier, the JWT payload must include the following:

- `iss`: the entity signing the token. This must allow the authorization server to discover the JWT keys of the issuer.
- `iat`: the timestamp when the JWT was signed
- `exp`: a timestamp after which the JWT isn't valid anymore
- `software_id`: a random string uniquely identifying this instance. A random UUIDv4 is suggested for this field

This allows client to securely update their metadata without being considered as a new client and re-asking user consent.

The `software_id` is used to uniquely identify a client and ensure the same `client_id` is returned on subsequent registration.
Each `software_id` is tied to the issuer (`iss`) and therefore subsequent registration must be signed by the same issuer.

The issuer keys can be retrieved using its [OIDC discovery document](https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata) (`<iss>/.well-known/openid-configuration`) or its [authorization server metadata](https://tools.ietf.org/html/rfc8414) (`<iss>/.well-known/oauth-authorization-server`).
The issuer does not have to be an actual authorization server, but its metadata can include human-readable informations about the issuer.
Those informations can be displayed on the user consent screen to tell the user about the client's publisher.

The JWT payload may also include a `software_version` claim denoting the version of the client being registered.
This field should be treated as an opaque string by the authorization server.

A Matrix server may choose to only allow signed client to be registered.
It might also have an list of trusted issuers for software statements and only allow those to restrict third-party clients.

## Potential issues

It is unclear how metadata updates should be handled.
If a client changes its `redirect_uris`, should the old ones be considered for a period of time?
If multiple versions of the same client coexist at the same time, should older versions of the software be able to override the metadata of the newer version?

If an authorization server allows unsigned clients, the number of client registration might explode exponentially.
At the same time, only allowing signed clients can make client development significantly harder.

## Alternatives

None relevant.

## Security considerations

Nothing prevents intentional collisions in `software_id`.
An attacker could register a `software_id` of another client before its first registration, blocking it from registration.
The registration endpoint should be rate-limited and the failed registration monitored by server administrators to detect such abuses.

## Unstable prefix

None relevant.
