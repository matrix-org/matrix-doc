# MSC2438: Local and Federated User Erasure Requests

When communicating across Matrix, it's not uncommon for user data and
metadata to be strewn across many different servers and services. Given this,
it is necessary to have a mechanism for removing as much personal data as
possible across the ecosystem upon user request.

This proposal specifies a best-effort method for erasing one's presence
across a Matrix federation, beginning with your own homeserver.

This proposal will mention 'personal data', however it intentionally leaves
the definition vague on purpose. Implementations SHOULD remove as much
identifying information about a user as they can.

## Proposal

Changes across multiple APIs are necessary to communicate requests of user
data erasure across all the different bits and pieces of the Matrix
ecosystem. We start with the initial erasure request from a user to their
homeserver.

A new parameter to the
[`/account/deactivate`](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-account-deactivate)
Client-Server API endpoint will be added, called `erase`, which is a boolean
that specifies whether the homeserver MUST attempt to erase all personal
data pertaining to the user off of the homeserver and as much of the rest of
the federation as it can.

Example request:

```
POST /_matrix/client/r0/account/deactivate

{
  "auth": {
    "type": "example.type.foo",
    "session": "xxxxx",
    "example_credential": "verypoorsharedsecret"
  },
  "erase": true
}
```

Example response:

```
{
  "id_server_unbind_result": "success",
  "erased": true
}
```

The `erased` field in the response is to allow the client to know whether the
erasure was successful in relation to the deactivation. At this time the
author is unsure about this due to:

* Non-clarity to the client about whether this means erasure was successful on
  the user's homeserver, or across the global federation
* Whether we should just fail the request entirely if local user erase was
  unsuccessful

A call to this endpoint from the user kicks off the erasure flow. From this
point, we would like to communicate the erasure request to:

* Other homeservers 
* Application services
* Identity Servers
* Any other service in the matrix ecosystem

which may have data (e.g. messages) pertaining to this user.

Upon receiving this request, the homeserver should forward it to every
homeserver it believes could also contain that user's data. How it does so is
left as an implementation detail. Once it's decided, the request will be
communicated over a new Federation API, `/_matrix/federation/v1/user/erase`.

Example request:

```
POST /_matrix/federation/v1/user/erase

{
  "user_id": "@bob:example.com"
}
```

Example response:

```
{}
```

It should be noted here that erasure requests for a given user should only be
allowed from the homeserver the user belongs to. If this isn't the case, the
other homeserver should respond with a `403 M_FORBIDDEN`.

For all application services, a new API endpoint will be added on the
application service: `POST /_matrix/app/v1/users/erase`. It contains a
single, required field `user_id`, which is the user ID to erase identifying
data of.

Example request:

```
{
  "user_id": "@someone:example.com"
}
```

At this point, the application service SHOULD try to erase as much
identifying information about this user as possible. Upon successfully
acknowledging the request, the application service should return a `200 OK`
with an empty JSON body.

Example response:

```
{}
```

For identity servers... (is reusing unbind enough, or do we need a separate
endpoint to delete the db rows?).

## Potential issues

As we live in an open federation, other services have the right to refuse
erasure request. (XXX: Does this mean anything legally?). It is not the
responsibility of the user's homeserver to ensure absolutely that all data
about this user across the federation has been deleted, which is impossible.
It simply needs to make its best attempt to request data erasure from all
necessary sources.

## Alternatives

This proposal relies on sending a federation request to another homeserver
(ideally retrying for a while if the other homeserver is currently offline),
which could potentially fail if the other homeserver doesn't come back on for
a long time period.

Alternative solutions have been considered:

* homeservers could maintain a public list of Matrix IDs that other
  servers/services could poll periodically.

While this solves the problem with servers/ASes which are offline at the
point of the request, but instead gives us a "how often to poll" problem.
It's also slightly questionable to maintain a publicly-available list of
"everybody who has asked to be erased" - if nothing else, it seems counter to
the spirit of GDPR.

* An `m.room.erasure` state event could be sent that contains the erased user's
  Matrix ID.

This works and uses existing mechanisms for reliable communication, however
comes with the same awkward public-list scenario as the above solution, as
well as adds yet more state to large rooms, not to mention state event
permission considerations.


## Security considerations

Malicious server admins can send out erasure requests for their own users
across the federation. However users already include their own homeserver in
their trust model, so this is a non-issue.
