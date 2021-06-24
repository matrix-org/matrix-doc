# Proposal to support two-factor authentication providers

This proposal intends to solve [#1997][issue1997]. At the moment, there isn't a
way for a user to have a "standard" two-factor authentication flow on their
account. Most homeservers currently only support the `m.login.password` stage,
making the user susceptible to keyloggers or rogue apps being able to
re-authenticate even after the user decides to de-auth the device.

In the context of end-to-end encryption, users are in a bit of a better
position because new devices are untrusted-by-default and even backed up megolm
sessions (as in [MSC1219][msc1219]) require additional passphrases or recovery
keys. However this is far from ideal because other users might be tricked into
trusting such a device, and without a mechanism such as [MSC1756][msc1756] the
likelihood of such a mistake is quite high.

Thus, having an easy-to-use two-factor-authentication flow would allow for an
improvement in the baseline security of a Matrix account. Since the vast
majority of web services provide two-factor authentication using TOTP tokens
(as defined in [RFC 6238][rfc6238]) we replicate this for Matrix so users can
re-use their existing TOTP applications.

It is also necessary to include a recovery code flow (which server admins might
choose to not support) so that a user who loses their TOTP generating device
can get back into their account. We also take care to allow this system to be
extended in the future with more two-factor providers.

[issue1997]: https://github.com/matrix-org/matrix-doc/issues/1997
[msc1219]: https://github.com/matrix-org/matrix-doc/issues/1219
[msc1756]: https://github.com/matrix-org/matrix-doc/pull/1756
[rfc6238]: https://tools.ietf.org/html/rfc6238

## Proposal

The CS API natively provides the ability to have multi-stage authentication, so
the bulk of this proposal is defining a new set of authentication stages:

  * `m.login.two-factor.totp` for TOTP tokens.
  * `m.login.two-factor.recovery` for recovery codes.

Servers must specify these as required stages in the authentication flow (with
a separate flow for each provider) for users which have enabled them on their
accounts. They must also be placed after a stage (such as `m.login.password`)
where the user being authenticated in this session has been determined, as
otherwise the homeserver cannot be sure what user's token is being verified.

A concrete example would mean that a user with both two-factor providers
enabled will have the following flows available:

  * `[ "m.login.password", "m.login.two-factor.totp" ]`
  * `[ "m.login.password", "m.login.two-factor.recovery" ]`

We also require that all future additions to the `m.login.two-factor.*`
namespace have similar semantics to the above and act as two-factor providers
in the following CS API endpoints.

In order to configure two-factor providers, several new CS API endpoints are required:

  * `GET /_matrix/client/r0/account/twoFactor` to get the current state of enabled providers for the account.
  * `POST /_matrix/client/r0/account/twoFactor` to configure providers.
  * `DELETE /_matrix/client/r0/account/twoFactor` to disable providers.

The `POST` and `DELETE` and endpoints all require user-interactive
authentication (including the appropriate `m.login.two-factor.*` stages if
already configured).

The details of these changes are outlined in the next few sections.

### `m.login.two-factor.totp`

Clients submit an auth-dict as follows:

```
{
  "type": "m.login.two-factor.totp",
  "token": "<token>",
  "session": "<session ID>"
}
```

Verification of the token is done as described in [RFC 6238][rfc6238], with all
of the relevant parameters being set at configure-time. Each homeserver can
decide how many time-steps of clock skew they wish to allow for a successful
login, though they should be aware of the security trade-off with larger
leniency in clock skew.

If the token is valid then the authentication succeeds. Otherwise the server
must generate a 401 error.

[rfc6238]: https://tools.ietf.org/html/rfc6238

### `m.login.two-factor.recovery`

Clients submit an auth-dict as follows:

```
{
  "type": "m.login.two-factor.recovery",
  "token": "<token>",
  "session": "<session ID>"
}
```

The given token must be a valid, *unused* token provided by the server as a
recovery code for the current account being authenticated. If so, then the
authentication succeeds and the token must be marked as used so it cannot be
re-used for future authentication flows. Otherwise the server must generate a
401 error.

### `GET /_matrix/client/r0/account/twoFactor`

This endpoint provides information about how the user's two-factor settings are
configured.

Clients that wish to find out what two-factor providers are supported by this
homeserver should look at the flows given by `/_matrix/client/r0/login` and
what stages are in the `m.login.two-factor.*` namespace.

| Parameter   | Type                    | Description                                                                                                             |
| ----------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `providers` | `map[string: Provider]` | Set of enabled configured providers (keyed by their `m.login.two-factor.*` name) and associated information about them. |

*Provider*

| Parameter    | Type    | Description                                                                                       |
| ------------ | ------- | ------------------------------------------------------------------------------------------------- |
| `changed_at` | integer | Timestamp, in milliseconds, the last time this two-factor provider had its configuration changed. |
| `enabled_at` | integer | Timestamp, in milliseconds, when this two-factor provider was enabled (reset on `/disable`).      |

An example JSON returned would be:

```
{
	"providers": {
		"m.login.two-factor.totp": {
			"changed_at": 1565749119947,
			"enabled_at": 1557800304221
		},
		"m.login.two-factor.recovery": {
			"changed_at": 1557800304221,
			"enabled_at": 1557800304221
		}
	}
}
```

### `POST /_matrix/client/r0/account/twoFactor`

This endpoint allows the client to enable (or reset) a two-factor provider. In
order to avoid users locking themselves out of their accounts, servers should
enable `m.login.two-factor.recovery` if it is not already enabled for the user.

#### Request

| Parameter   | Type                           | Description                                                                                                     |
| ----------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `providers` | `map[string: Provider Params]` | Providers (keyed by their `m.login.two-factor.*` name) which the user wishes to enable and their configuration. |
| `auth`      | Authentication Data            | Additional authentication information for the user-interactive authentication API.                              |

Authentication Data is identical as in the existing spec. Provider Params is
required to be an empty JSON object (to allow for future extensions that have
configurable two-factor providers).

##### Example

```
POST /_matrix/client/r0/account/twoFactor HTTP/1.1
Content-Type: application/json

{
	"providers": {
		"m.login.two-factor.totp": {}
	},
	"auth": {
		"type": "example.type.foo",
		"session": "xxxxx",
		"example_credential": "verypoorsharedsecret"
	}
}
```

#### Response

In order to facilitate changing two-factor provider parameters in the future,
the server provides all of the parameters of the providers used. It should be
noted that the server may decide to configure more providers than the user
requested. If the response is a success code, the server must have enabled at
least the providers the user specified.

Providers which are already enabled by the user but were not specified in the
request should not be modified by this operation.

| Parameter    | Type                           | Description                                                                                                                                 |
| ------------ | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `providers`  | `map[string: Provider Params]` | Providers (keyed by their `m.login.two-factor.*` name) which the server enabled or re-configured due to this request, and their parameters. |

The structure of Provider Params depends on which provider is the key.

##### `m.login.two-factor.totp`

| Parameter | Type        | Description                                                |
| --------- | ----------- | ---------------------------------------------------------- |
| `params`  | TOTP Params | Parameters for the TOTP algorithm used.                    |
| `seed`    | string      | String used as a seed for [RFC 6238][rfc6238] TOTP tokens. |

*TOTP Params*

| Parameter | Type    | Description                        |
| --------- | ------- | ---------------------------------- |
| `type`    | string  | Identifier for the TOTP algorithm. |
| `step`    | integer | Time-step size in seconds.         |
| `size`    | integer | Number of token digits.            |

`type` must be `m.totp.v1.rfc6238-sha1`. In order to maximise interoperability,
servers should use the following values:

 * `step` should be 30.
 * `size` should be either 6 (recommended) or 8.

##### `m.login.two-factor.recovery`

| Parameter | Type             | Description                                                                                            |
| --------- | ---------------- | ------------------------------------------------------------------------------------------------------ |
| `tokens`  | array of strings | List of one-time-use-only tokens that act as recovery codes for use with `m.login.two-factor.recovery` |

Each token should be a sufficiently randomly generated string and be long
enough that a brute-force attack would be infeasible (but only using
case-insensitive common characters to make it easier for users to enter them).
Our recommendation is 12 alpha-numeric characters excluding look-alikes.

##### Example

And then the server returns a JSON object with the following structure:

```
{
	"providers": {
		"m.login.two-factor.totp": {
			"params": {
				"type": "m.totp.v1.rfc6238-sha1",
				"step": 30,
				"size": 6,
			},
			"seed": "Kung-fu? I'm going to learn ... kung-fu?"
		},
		"m.login.two-factor.recovery": {
			"tokens": [
				"neo",
				"morpheus",
				"trinity",
				"apoc",
				"switch",
				"cypher",
				"tank",
				"dozer",
				"mouse"
			]
		}
	}
}
```

### `DELETE /_matrix/client/r0/account/twoFactor`

This is used to disable two-factor providers. The server must only disable the
providers requested with the exception of `m.login.two-factor.recovery`. If,
after this deletion operation completes, no other two-factor providers would be
enabled anymore then the server may also disable `m.login.two-factor.recovery`.

The value `m.login.two-factor.*` has a special meaning, and is used to indicate
that all enabled providers should be disabled for this user. **XXX: This
interface is probably racy and might not be super-useful.**

**NOTE**: While HTTP does not explicitly define the meaning of a content-body
with `DELETE` we assume it to be the same as `POST` here.

#### Request

| Parameter   | Type                | Description                                                                        |
| ----------- | ------------------- | ---------------------------------------------------------------------------------- |
| `providers` | array of string     | Providers (using their `m.login.two-factor.*` name) to be disabled.                |
| `auth`      | Authentication Data | Additional authentication information for the user-interactive authentication API. |

Authentication Data is identical as in the existing spec.

##### Example

```
DELETE /_matrix/client/r0/account/twoFactor HTTP/1.1
Content-Type: application/json

{
	"providers": [
		"m.login.two-factor.totp",
		"m.login.two-factor.recovery"
	],
	"auth": {
		"type": "example.type.foo",
		"session": "xxxxx",
		"example_credential": "verypoorsharedsecret"
	}
}
```

#### Response

| Parameter   | Type             | Description                                                                                        |
| ----------- | ---------------- | -------------------------------------------------------------------------------------------------- |
| `providers` | array of strings | Providers (using their `m.login.two-factor.*` name) which the server disabled due to this request. |

**XXX: Maybe the response should be the set of providers that remain enabled?**

```
{
	"providers": [
		"m.login.two-factor.totp",
		"m.login.two-factor.recovery"
	]
}
```

## Trade-offs

* We don't allow clients to configure any of the parameters for the current set
  of two-factor providers. This does mean a small reduction in user
  configurability but it reduce the threat of bad configurations and makes the
  server implementations (marginally) simpler because there is no need for
  verification. However we allow for future extensions to add configuration,
  since other two-factor providers (like YubiKey) require the client to specify
  some parameters.

* There is a special-case for `m.login.two-factor.recovery` in order to
  make it act like most two-factor systems. This does result in an increase in
  implementation complexity (this is why the APIs allow the server to configure
  more providers than requested), but it will allow for a far smoother user
  experience than if every client had to reimplement their own special-case
  handling of recovery codes.

* There is a special-case for `m.login.two-factor.*` in order to provide a
  simple "off switch" for two-factor authentication after a user has configured
  it. This does result in an increase in implementation complexity, but such
  complexity would've had to live in clients if it wasn't provided by servers
  (and would've been more racy).

* There are many other two-factor systems that might have more desirable
  security properties, but the primary benefit of TOTP is a very large number
  of people are familiar with it and there are many applications which support
  it. However the two-factor endpoints have been made generic enough that (in
  the future) other two-factor systems (such as YubiKey) could be added easily
  and in a backwards-compatible way.

## Potential issues

* Significant clock skew issues can result in users not being able to log in.
  It's the job of server administrators to decide how much clock skew they
  believe is reasonable to handle. They should be aware that increasing the
  compensation for clock skew results in more computation (TOTP requires
  checking each time-step by computing a HMAC) and results in longer-lasting
  TOTP codes that open the potential for reuse.

## Security considerations

* The recommended parameters for `m.login.two-factor.totp` come directly from
  the RFC, and have been widely implemented. There is no reason to think they
  are insecure.

* The recommended parameters for `m.login.two-factor.recovery` is based on
  common practice by many web services that provide two-factor authentication.
  Recommending the avoidance of look-alikes is a usability feature and doesn't
  meaningfully impact the entropy.

* We do not reset already-configured recovery codes when other two-factor
  methods are configured or disabled. If the concern is that an existing
  two-factor provider was compromised, then it seems unlikely that the recovery
  codes would also be compromised. Some web services do reset your recovery
  codes if you reconfigure TOTP with a new seed, but this appears to be an
  implementation detail rather than a security feature.

## Conclusion

With this proposal, Matrix would be able to increase the baseline security of
users' accounts by adding a very minimal implementation of the widely-used
TOTP-based two-factor system.
