# MSC2835: Add UIA to the /login endpoint

Many endpoints in the client-server API currently use [User-Interactive Authentication](https://matrix.org/docs/spec/client_server/latest#user-interactive-authentication-api) (UIA).
This is useful for requiring the client to complete additional steps before hitting the underlying
endpoint, such as asking for a password, or when registering to set an email.

One endpoint, `/_matrix/client/r0/login`, lacks UIA. This is a big limiting factor, as that means
login cannot be interactive: UIA is needed to complete additional steps than just entering a password,
such as asking for a two-factor authentication code or sending a verification email.

## Proposal

It is proposed to add UIA to the `POST /_matrix/client/r0/login` endpoint. In order to preserve
backwards compatibility, if there is no `auth` dict in the POST body, then the entire POST body should
be copied into the new `auth` dict. This is possible because the already speced POST body of `/login`
contains all needed fields for the `m.login.password` and `m.login.token` UIA stages respectively.
The body is copied so that other keys, such as `initial_device_display_name`, remain at root level.

This will yield the following body parameters for `POST /_matrix/client/r0/login`:

| Parameter | Type          | Description
|-----------|---------------|-------------
| auth      | `Authentication Data` | Additional authentication information for the user-interactive authentication API.
| type | `enum` | The login type being used. One of: ["m.login.password", "m.login.token"]. Deprecated in favour of UIA.
| identifier | `User identifier` | Identification information for the user. Deprecated in favour of UIA
| user | `string` | The fully qualified user ID or just local part of the user ID, to log in. Deprecated in favour of UIA.
| medium | `string` | When logging in using a third party identifier, the medium of the identifier. Must be 'email'. Deprecated in favour of UIA.
| address | `string` | Third party identifier for the user. Deprecated in favour of UIA.
| password | `string` | The user's password. Deprecated in favour of UIA.
| token | `string` | Part of Token-based login. Deprecated in favour of UIA.
| device_id | `string` | ID of the client device. If this does not correspond to a known client device, a new device will be created. The server will auto-generate a device_id if this is not specified.
| initial_device_display_name | `string` | A display name to assign to the newly-created device. Ignored if `device_id` corresponds to a known device.

As seen, all existing parameters, apart from `device_id` and `initial_device_display_name` are deprecated
in favour of UIA.

The `GET /_matrix/client/r0/login` endpoint should *only* advertise a stage if it is the only stage
in a UIA flow for this server. This allows, if a server e.g. only needs password login, full backwards
compatibility with clients which did expect UIA on `/login` (all existing clients).

## Potential issues

Some users might be confused why they can't log into their servers anymore, when using an outdated
client and their server takes use of UIA.

Additionally, the UIA flows in `/login` have to be able to resolve which user ID they are for, so that
the server knows whom to log in as. Both `m.login.password` and `m.login.token` allow a server to do
that. A requirement for either stage to be present in any flow has purposefully not been added, to make
it easier to introduce other user-identifying stages.

## Alternatives

While a new endpoint could be added, that does not change the issue with users using old clients not
being able to log into their own server anymore.

## Security considerations

Implementing authentication properly is a crucial security aspect when implementing a server. While
this proposal does add additional complexity to that step, the suggestion of copying the post body into
an `auth` dict, should one not be present, provides a simple way to still support fallbacks. As other
endpoints already use UIA, this change does not introduce anything extraordinary complex.
