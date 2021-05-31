# MSC2315: Allow users to select "none" as an integration manager

*Note*: This is part of a larger MSC for an integrations API:
[MSC1956](https://github.com/matrix-org/matrix-doc/issues/1956).

Currently if a client wants to offer the user to select no integration manager they are
forced to use some vendor-prefixed (or similar) approach to store that information. While
they could limit themselves to just detecting one level of integration managers, the UX
for a such an approach would be lacking as all users would have to explicitly pick an
integration manager instead of a default being applied for them.

## Proposal

It is proposed that a new account data event of `m.integrations` (`im.vector.integrations`
during development/pre-spec period) be introduced to the spec under the Integrations API
specification, when the time comes.

The event content is as follows:
```json
{
    "enabled": true
}
```

Other flags may be added at a future time, however a single flag (`enabled`) is currently
proposed. The `enabled` flag is a boolean which defaults to `true` when the flag is missing
or the event not found in the user's account data. When the flag is `false`, clients should
not render any integration managers (or integration manager features) to the user, even if
some are defined by the user/homeserver/client config.
