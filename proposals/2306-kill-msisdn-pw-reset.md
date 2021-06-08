# MSC2306: Removing MSISDN password resets

Currently Matrix allows password resets to be performed through phone numbers,
however this is a terrible idea because phone numbers can be recycled. Note
that although many services and similar platforms to Matrix offer password resets
via phone number, they are often authenticated in multiple ways. This proposal
aims to minimize the security risk a user can face without reworking password
resets entirely - a future proposal can (and should) take on the effort of
improving password resets more generally.

## Proposal

Simply put, `/account/password/msisdn/requestToken` is to be removed from the
specification. The other msisdn `/requestToken` endpoints in the client-server API
are left untouched by this proposal (registration and adding 3PIDs).

Servers SHOULD return a HTTP 404 error when the now-removed endpoint is requested.
Clients should already have error handling in place, so it is expected that they
can handle the endpoint disappearing. The remainder of clients, including Riot,
do not support password reset by phone number despite this endpoint having existed
for a long time.

Matrix and this proposal still supports password reset through UIA (User-Interactive
Authentication), which includes support for email addresses. No action is needed to
disable support for `m.login.msisdn` from the specification because the endpoint that
clients would call is being removed. It would be counterproductive from a server
perspective to advertise msisdn support when the endpoint is not supported anymore.

## Reference material

* riot-web's lack of support: https://github.com/vector-im/riot-web/issues/5947
* matrix-doc issue: https://github.com/matrix-org/matrix-doc/issues/2303


## Alternative solutions

The specification could instead recommend/demand that servers require additional
stages when resetting passwords to avoid potential phone number recycling issues.
