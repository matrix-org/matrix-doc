# Application service ping endpoint

## Problem
A relatively common problem when setting up appservices is the connection
between the appservice and homeserver not working in one or both directions.
If the appservice is unable to connect to the homeserver, it can simply show
the error message to the user. However, there's currently no easy way for the
appservice to know if the homeserver is unable to connect to it. This means
that the appservice might start up fine, but not actually work, because the
homeserver isn't sending events to it.

## Proposed solution
The proposed solution is a new endpoint in homeservers that appservices can use
to trigger a "ping". When the endpoint is called, the homeserver will send an
empty transaction to the appservice and reply with the result of that transaction.

Appservices can use the endpoint at startup to ensure communication works in
both directions, and show an error to the user if it doesn't.

### `POST /_matrix/client/r0/appservice/{appserviceId}/ping`
The request body has an optional `txn_id` field that the homeserver must pass
through to the `PUT transactions` call. If not specified, the transaction ID is
up to the homeserver.

The transactions sent via this endpoint should only be attempted once and
excluded from any automatic retry that normal transactions have.

The endpoint is only allowed when using a valid appservice token and it can
only ping the appservice ID associated with the token. Trying to use a
non-appservice token must result in a `M_FORBIDDEN` error.

#### Response
If the transaction request returned successfully, the endpoint returns
HTTP 200 with an empty JSON object as the body.

If the transaction request fails, the endpoint returns a standard error
response with `errcode`s and HTTP status codes as specified below:

* For non-2xx responses, `M_BAD_STATUS` and HTTP 502.
  Additionally, homeservers should return the status code and response body in
  the `status` and `body` fields respectively to aid with debugging.
* For connection timeouts, `M_CONNECTION_TIMEOUT` and HTTP 504.
* For other connection errors, `M_CONNECTION_FAILED` and HTTP 502.

## Unstable prefix
The endpoint can implemented as `/_matrix/client/unstable/net.maunium.msc2659/appservice/ping` until it lands in the spec.
