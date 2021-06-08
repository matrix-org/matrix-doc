# Cancellation of 3pid validation tokens

Currently the Identity Service spec requires that validation tokens (those received from `/submitToken`)
expire after 24 hours of the most recent modification. This works nicely for the vast majority of
cases where the user validates their 3pid and moves on to using Matrix within the time frame, however
not all cases are like this.

Occasionally, a user may wish to cancel a validation because they accidentally typed the wrong address
or decided that they don't want to go through with the request. We should keep the time-based expiration
and add routes for clients to invoke early cancellation of a validation session.

As a reference to readers, this proposal was written in the context of working on
[vector-im/riot-web#6560](https://github.com/vector-im/riot-web/issues/6560) - it's fine to add a 'go back'
button and just let the session expire, however that is also a great time to cancel the session before the
wrong target has a chance to try and claim the account for themselves.


## Proposal

Two new endpoints are to be added to the Identity Service specification, which are similar in structure:
* `POST /_matrix/identity/api/v1/validate/email/cancelToken`
* `POST /_matrix/identity/api/v1/validate/msisdn/cancelToken`

Both endpoints take the same arguments as the `/submitToken` APIs however instead of binding the identifier,
the session becomes expired. In practice this means a `sid`, `client_secret`, and `token` must be provided
to the Identity Server via `/cancelToken`.

A status code of `200` and empty JSON object (`{}`) shall indicate success. 4xx error codes, with applicable
standardized error codes, shall indicate validation failure.

*Note*: This proposal does not support the idea of allowing `application/x-form-www-urlencoded` as a content
type for the request. Therefore the new endpoints are expected to only consume and produce JSON.

To aid clients going through a homeserver to contact the identity server, a similar set of endpoints are to
be added to the Client Server API:
* `POST /_matrix/client/r0/account/3pid/email/cancelToken`
* `POST /_matrix/client/r0/account/3pid/msisdn/cancelToken`

Similar to other endpoints in this area, these endpoints proxy requests to the given `id_server`.


## Security considerations

Servers should be careful to validate session parameters are correct before actually cancelling them. There
is an argument to be made about cancelling the session when *any* of the parameters are given, however it is
believed by the author that the additional security of ensuring the requester has permission to actually
cancel the session is more worthwhile than trying to fail fast.

Servers should also be aware of a potential resource exhaustion vector where an attacker requests a token and
cancels it immediately, in a loop. Servers are welcome to rate limit either request to prevent such attacks.
