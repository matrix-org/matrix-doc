# Authenticated Content Repository API

Currently anyone can fetch resources from content repositories.
This can be undesired behaviour for several reasons as discussed
in [synapse#2133](https://github.com/matrix-org/synapse/issues/2133) and
somewhat in [synapse#2150](https://github.com/matrix-org/synapse/issues/2150).

Homeserver administrators might want to be able to
restrict access to the content they serve.

This is unrelated to controlling access to content on a per-file basis,
which is something a user might desire.

## Proposal

Homeservers may reject unauthenticated access to media endpoints.

When an unauthenticated client accesses an endpoint, the homeserver
may reject the request like it would with an authenticated endpoint.

Thus it returns status code 401 and an error
with an errcode of `M_MISSING_TOKEN` or `M_UNKNOWN_TOKEN` as apropriate.

Example response:

```json
{
  "errcode": "M_MISSING_TOKEN",
  "error": "Media access is restricted to authenticated clients"
}
```

### Configuration

To allow clients to predetermine whether authentication is required,
the field m.media.unauthenticated is added to
`GET /_matrix/media/r0/config`.
It specifies what content can be accessed unauthenticated.

The following behaviours are defined,
when a client encounters an unknown enum value it should be treated like `m.unspecified` :

| Enum value         | Description                                                                                  |
| ------------------ | -------------------------------------------------------------------------------------------- |
| `m.none` / missing | All content can be accessed unauthenticated                                                  |
| `m.local`          | Only content with an authority the server is responsible for can be accessed unauthenticated |
| `m.cached`         | Cached content can be accessed unauthenticated                                               |
| `m.unspecified`    | Authenticated access might be required in some cases                                         |
| `m.all`            | No content can be accessed unauthenticated                                                   |

Example response:

```json
{
  "m.media.unauthenticated": "m.local"
}
```

Clients can decide based on this
if sharing a download link to a non Matrix user is possible.

### Server to server

To reduce the amount of server to server communication,
when one homeserver tries to fetch content from another homeserver,
the configuration should first be retrieved and cached.
When the value is m.none the server should not attempt to fetch the
content from the remote server
and return status code 404 and an error with an errcode of M_NOT_FOUND.

Example response:

```json
{
  "errcode": "M_NOT_FOUND",
  "error": "Remote homeserver rejected access"
}
```

## Potential issues

- Once homeservers enable this behaviour with a m.media.unauthenticated
  value other than null, older clients will not be able to access some content.
  This is desired for the server operator and undesired for the user.

- Older clients and servers might encounter an unexpected error code
  which may lead to unknown behaviour.

- GUI toolkits used by client authors might not support modifying request headers
  for image widgets. This change would thus increase client complexity in these cases.

## Alternatives and comparisons

- All media endpoints could always require authentication,
  but then the server to server exchange would still need
  to be extended to allow access for remote homeservers.

- **MSC701**

  This MSC proposes a way to authenticate content repo access on a per file basis.
  With it uploads that are not marked public are inaccessible to clients without a
  content token.

  MSC701 provides control to the user as to who sees content.
  Which is unrelated to this proposal which tries to give control to server admins.

  For the following reasons can MSC701 not provide the functionality of this MSC:

  - When the server allows the public flag its admin has no control as
    to who can access content
  - When the server forbids the public flag (which is not specified in MSC701),
    its admin can still not block non-local users who share rooms with local users
  - The federation API of this proposal allows access to non-Matrix users if they can
    get access to a content token (unless the HMAC is enforced)

## Security considerations

- Download links for content might leak the users access token when shared
