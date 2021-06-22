# MSC2499: Fixes for Well-Known URIs

Several minor issues and inconsistencies have come up with the well-known URIs used for
discovering clients and servers. This proposal intends to fix these issues.

## Proposal

The following changes should be made to the spec:

1. The spec does not mention that redirects should be followed for `/.well-known/matrix/client`
and does not clearly specify what type of redirects should be followed for `/.well-known/matrix/server`.
To fix this, the spec should be changed to state that when a well-known URI is requested,
the client or server should follow HTTP 301, 302, 303, 307, and 308 redirects up to 30 times.

1. Currently the spec does not mention which Content-Type should be used for the response to
`/.well-known/matrix/client`. The Client-Server spec should be changed to state the Content-Type
SHOULD be `application/json` however it should be assumed to be JSON regardless of Content-Type.
This is consistent with the Server-Server API.

1. Step 3f in the Client-Server well-known flow should be changed to use the modern
`/_matrix/identity/versions` API to validate the identity server rather than the deprecated
`/_matrix/identity/api/v1`.

1. Mark the `/_matrix/identity/v2` status check API as deprecated. `/_matrix/identity/versions`
is the suggested replacement.

1. The maximum size of size of the well-known file is 51200 bytes. A client or server
requesting a well-known file MUST abort and FAIL_PROMPT if the response exceeds 51200 bytes.
