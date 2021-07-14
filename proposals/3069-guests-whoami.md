# MSC3069: Allow guests to use /account/whoami

Currently the [/account/whoami](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-account-whoami)
endpoint does not mention anything about guests, which is a bit of an oversight. The implementation
of the endpoint got created such that guest access was declined.

## Proposal

Guests are allowed to use `/account/whoami`. When a guest makes a request, the response will have
an added `is_guest: true` field - this field is optional (default `false`) otherwise.

## Potential issues

None forseen. This corrects a mistake.

## Alternatives

None relevant.

## Security considerations

Guests will be able to know their user ID, as they would when they registered in the first place.

## Unstable prefix

While this MSC is not in a stable version of the specification, implementations should use
`org.matrix.msc3069.is_guest` in place of `is_guest`. Callers should note that they might see
`M_GUEST_ACCESS_FORBIDDEN` errors if the server is not implementing this MSC.
