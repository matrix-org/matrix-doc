# MSC2839: Dynamic User-Interactive Authentication

[An issue on User-Interactive Authentication (UIA)](https://github.com/matrix-org/matrix-doc/issues/24089)
outlined some issues with the current UIA system and ideas how to fix them.

These issues included:
1. Having multiple optional stages being complicated to model
2. Certain requirements being hard or impossible to model: If you didn't pick stage A and not stage B,
   you *will* have to do stage C
3. Having parameters of a stage depend on previously completed stages, e.g. having some keys depend
   on your mxid

It seems a simple fix for all of these issues is to explicitly allow the `flows` and `params` reply
to be dynamic. While the spec does not explicitly forbid this already, it seems to imply that those
are static between different UIA request roundtrips.

## Proposal

It is proposed that, for UIA, the `flows` and `params` responses can change for the same session id,
thus being dynamic. This allows the server to, down the road, insert stages, add flows and modify
params, based on what the user already did / completed etc.

For servers already serving static UIA nothing changes, as it is still valid to always return the
same `flows` and `params` throughout an entire UIA authorization.

Clients would have to look at the `flows` and `params` of the *last* UIA reply, instead of just caching
those of the first one and relying those won't change.

This allows good backwards compatibility while also greatly increasing the flexibility. A few scenarios
are listed below:

### Dynamic parameters: Depending on MXID

Let's say your `flows` have a password and a 2fa stage, making the UIA response as following:
```json
{
  "flows": [
    {
      "stages": ["m.login.password", "new.type.for.2fa"],
    },
  ],
  "completed": [],
  "params": {},
  "session": "xxxx",
}
```

The new 2fa params might depend on what mxid the user has, or some other private key are associated
with that user account. Thus, it is only possible to generate the params *after* completing `m.login.password`.
Thus, the response after completing that stage could then look as follows:
```json
{
  "flows": [
    {
      "stages": ["m.login.password", "new.type.for.2fa"]
    },
  ],
  "completed": ["m.login.passwod"],
  "params": {
    "new.type.for.2fa": {
      "secret_key": "beep",
    },
  },
  "session": "xxxx",
}
```

### Dynamic stages: 2fa

A user might have different types of 2fa configured, be it TOTP or SMS verification. You don't know
until after completing `m.login.password` which type to pick. A UIA response could look as following:
```json
{
  "flows": [
    {
      "stages": ["m.login.password"],
    },
  ],
  "completed": [],
  "params": {},
  "session": "xxxx",
}
```

Then, *after* completing the `m.login.password` stage a new stage is inserted:
```json
{
  "flows": [
    {
      "stages": ["m.login.password", "new.type.for.totp"],
    },
  ],
  "completed": ["m.login.password"],
  "params": {},
  "session": "xxxx",
}
```

Thus, the client has to complete `new.type.for.totp` next.

### Dynamic stages with multiple choice

Now, let's say after completing some stage, based on whatever options the user has configured, they
get to chose one of two other stages. For that, an entirely new flow could be added. For example, if
the original UIA response was the following:
```json
{
  "flows": [
    {
      "stages": ["m.login.password"],
    },
  ],
  "completed": [],
  "params": {},
  "session": "xxxx",
}
```

After completing `m.login.password` it can look as following:
```json
{
  "flows": [
    {
      "stages": ["m.login.password", "new.stage.to.verify.email"],
    },
    {
      "stages": ["m.login.password", "new.stage.to.verify.sms"],
    },
  ],
  "completed": ["m.login.password"],
  "params": {},
  "session": "xxxx",
}
```

### Hinting future stages

While this dynamic-ness allows the server to just keep adding more and more stages, it can also be
used to hint future stages. For example, if you want a password and then snailmail authentification
to verify someones postal address (just as an example), asking for a password might trigger needing
2fa or some other additional verification next. So, a UIA response could initially look as following:
```json
{
  "flows": [
    {
      "stages": ["m.login.password", "new.snailmail.stage"],
    },
  ],
  "completed": [],
  "params": {},
  "session": "xxxx",
}
```

Which, after completing the password stage, becomes:
```json
{
  "flows": [
    {
      "stages": ["m.login.password", "new.2fa.stage", "new.snailmail.stage"],
    },
  ],
  "completed": ["m.login.password"],
  "params": {},
  "session": "xxxx",
}
```

And then
```json
{
  "flows": [
    {
      "stages": ["m.login.password", "new.2fa.stage", "new.snailmail.stage"],
    },
  ],
  "completed": ["m.login.password", "new.2fa.stage"],
  "params": {},
  "session": "xxxx",
}
```

### Optional stages

Nothing changes for optional stages: If an optional stage appears down the road, a new flow with an
`m.login.dummy` can be added. If multiple stages are optional this can lead to having completed
`m.login.dummy` multiple times.

### Some thoughts
While some of these things can already be modeled with the existing UIA, the examples here were kept
purposefully very simple. As soon as you have e.g. multiple different types of 2fa the user can configure,
the server has to dictate somehow which stage must be the next one to complete. With the old UIA system
that is not possible. Additionally having the params dynamically greatly increases the flexibility,
allowing quite a lot of things not currently possible with UIA.

## Potential issues

If a server dynamically changes the `flows` so that there is no flow that matches the already completed
stages the client has no way of completing the UIA challenge anymore. A client could see this as
"permission denied".

This means that a server has to keep track of how it dynamically changed the stages and flows, to
ensure that there is always one valid flow according to the completed stages.

## Alternatives

While one could make a completely new UIA version, this method is backwards compatible and should
require minimal change on the client side to implement. If existing servers don't want to take use of
this then they don't have to change at all, as static UIA is still valid.

## Security considerations

Together with [MSC2835](https://github.com/matrix-org/matrix-doc/pull/2835) this actually *increases*
the security of e.g. the login, as it would allow the user to configure multiple different 2fa types,
should such stages get specced.
