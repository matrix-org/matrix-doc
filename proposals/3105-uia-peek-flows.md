# MSC3105: Previewing user-interactive flows

*This proposal deals with [User-Interactive Authentication](https://matrix.org/docs/spec/client_server/r0.6.1#user-interactive-authentication-api)
or UIA for short.*

Clients typically want to show inline authentication UI for certain account operations, but need
to know what flows to expect from the server before showing the UI. Usually this means the client
will make a request to the server assuming that the server will have some flows, although this is
not always the case for a variety of reasons (such as the server's internal authentication policies).
In these cases, the client will have made a request to the server and the server will have fulfilled
that request because no specific authentication was needed, leaving the client stuck in a position
where it was unable to present confirmation UI.

This proposal introduces a peek/preview mechanism so the client can be reasonably sure about what
flows, if any, the server would present if the real request were to be made. This proposal does not
incorporate a system to guarantee the flows for the real request given the server is highly unlikely
to change the flows in the (milli)seconds following the preview attempt.

## Proposal

When a UIA-supported endpoint is approached with an `OPTIONS` request the server would respond with
its intention regarding authentication for that endpoint. If the server intends to return flows the
client/user should follow, it would do so with the normal 401 UIA response. If the server intends
no flows (ie: no authentication required), the server would reply with a 401 UIA response with an
empty `flows` array. In both cases, the `session` field can (and should) be omitted: the server is
not supposed to be modifying/creating resources during an `OPTIONS` request and therefore a session
should not be reserved. 

Servers are not required to predict the outcome of an `OPTIONS` request which also specifies a
`session` field - UIA does not lend itself to being able to determine if the flows would change and
thus is not expected to produce a sensible result. These secondary `OPTIONS` requests would most
likely be automatic preflight checks done by web browsers anyhow.

Servers should also note that most reverse proxies and libraries do *not* automatically add CORS
headers to error responses like 401. System administrators may have to be instructed to explicitly
add CORS headers to all requests, as per the [information in the spec](https://matrix.org/docs/spec/client_server/r0.6.1#web-browser-clients).

Clients should be able to parse this `OPTIONS` response body to make a determination about what
to do next, which may include just trying the request for real. Depending on the client's tolerance
to risk (specifically regarding the possibility of the flows changing), the client might choose
to take another approach.

As a worked example, here's what a client might do when the user clicks a 'Deactivate my account'
button:

1. `OPTIONS /_matrix/client/r0/account/deactivate` request to the server.
2. Server responds with `flows: []` (no authentication needed).
3. Client asks the user for confirmation on deactivation.
4. `POST /_matrix/client/r0/account/deactivate` request to the server.
5. Server deactivates the account.

If the flows were to change at step 4, the client would likely show a "Enter your password to
continue" or similar dialog. This UX could be considered subpar, though would be necessary in
this example. Similarly, if the server did respond with flows on step 2 then the client might
opt to jump to step 4 as inline UI for the user to confirm with ("Please confirm you'd like to
deactivate your account by entering your password").

Servers should consider always requiring a form of authentication for "dangerous" endpoints like
account deactivation, given the client might assume the flows will be presented to them. Clients
are cautioned that servers *might not* require authentication on said "dangerous" endpoints.

## Potential issues

The `OPTIONS` approach is not great because it shouldn't allow a state change, therefore no `session`
to "reserve" the flows for a future, real, request. We could go against the HTTP spec and allow
a `session` to be reserved, although this might be too uncomfortable for some server implementations
which want to remain pure to the HTTP specification.

Web browser clients in particular are likely to send 2 `OPTIONS` requests instead of just one: the
first would be the code-invoked one to discover the flows, and the second would be a built-in preflight
check. Considering the endpoint is fairly easily calculated by the server, this is not perceived to
be an issue. 

Some HTTP libraries may treat the 401 on the `OPTIONS` request as an exception, therefore refusing
to expose the response body. These libraries are somewhat rare, and are questionably useful for use
against APIs like the ones Matrix provides given the API's utilization of error codes throughout.

## Alternatives

Instead of using `OPTIONS`, we could use a `noop=true` query string parameter or similar to denote
that no action should be taken. This is less backwards compatible, and therefore less safe, as an 
option but would allow us to define an amount of custom functionality like reserving a `session`.
See the "unstable prefix" section for more information on backwards compatibility.

We could also completely replace UIA with some other system that either has built-in previewing
of similar constructs, or no need to perform auth in this way. This is not considered feasible by
this proposal in the timespan it intends to land within.

## Security considerations

Servers should ratelimit `OPTIONS` requests no different than they would other requests, which they
should already be doing given the web browser preflight checks. There is no perceived reason why the
client would need to hammer on an `OPTIONS` request, other than to be a nuisance.

"Dangerous" endpoints should be handled with care, as already mentioned.

## Unstable prefix

While this MSC is not in a released version of the specification, servers should expose an 
[unstable flag](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-versions) of 
`org.matrix.msc3105` to denote that this functionality is available. This is because namespacing
the HTTP method is a non-starter for a proposal like this, and putting the whole API under `/unstable`
does not seem sensible.

Servers without the feature flag (older versions) can still be approached with the `OPTIONS` request,
and in some cases might even reply with useful information already required by this proposal. Clients
should treat lack of information (200 OK instead of 401, missing fields, etc) as though the flows are
unknown. In these cases, clients should consider assuming the server will require no authentication for
maximum safety.
