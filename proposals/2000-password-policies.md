# MSC 2000: Proposal for server-side password policies

Some server administrators may want to ensure their users use passwords that
comply with a given policy. This is specifically relevant to companies and big
organisations which usually want to be able to apply a standardised password
policy across all services.

This proposal aims to define a way for servers to enforce a configurable
password policy and for clients to be aware of it so they can provide users with
an appropriate UX.

## Proposal

This proposal adds a new route, `GET /_matrix/client/r0/password_policy`,
which would return the following response with a 200 status code:

```json
{
    "policy": {
        // Policy parameter
    }
}
```

Five optional policy parameters are also specified:

* `m.minimum_length` (integer): Minimum accepted length for a password.
* `m.require_digit` (boolean): Wether the password must contain at least one
  digit.
* `m.require_symbol` (boolean): Wether the password must contain at least one
  symbol.
* `m.require_lowercase` (boolean): Wether the password must contain at least one
  lowercase letter.
* `m.require_uppercase` (boolean): Wether the password must contain at least one
  uppercase letter.

Implementations are free to add their own policy parameters in their own
namespace. This  allows server administrators to rely on a custom solution, for
example Dropbox's [zxcvbn](https://github.com/dropbox/zxcvbn) tool which could
lead to a `org.example.complexity` parameter describing the minimum expected
complexity score from zxcvbn's analysis.

Finally, this proposal changes the following routes:

* `POST /_matrix/client/r0/register`
* `POST /_matrix/client/r0/account/password`

By adding new error codes to the list of possible ones returned with a 400
status code:

* `M_PASSWORD_TOO_SHORT`: the provided password's length is shorter than the
  minimum length required by the server.
* `M_PASSWORD_NO_DIGIT`: the password doesn't contain any digit but the server
  requires at least one.
* `M_PASSWORD_NO_UPPERCASE`: the password doesn't contain any uppercase letter
  but the server requires at least one.
* `M_PASSWORD_NO_LOWERCASE`: the password doesn't contain any lowercase letter
  but the server requires at least one.
* `M_PASSWORD_NO_SYMBOL`: the password doesn't contain any symbol but the
  server requires at least one.
* `M_PASSWORD_IN_DICTIONARY`: the password was found in a dictionary, and is
  not acceptable.
* `M_WEAK_PASSWORD` if the reason the password has been refused doesn't fall
  into one of the previous categories.

## Tradeoffs

A less flexible way to define a password policy (e.g. limiting a policy's
definition to the params for `m.default_policy`) would have been simpler,
however some clients are already implementing their own passowrd complexity
policy (Riot Web, for example, uses zxcvbn), and this solution would improve the
compatibility of the proposed solution with existing software.
