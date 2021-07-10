# MSC2848: Globally unique event IDs

Currently the client-server API and server-server API disagree on the deprecation of the `GET /event/:eventId`
endpoint, which has lead to confusion and concern among the core team and wider community. The endpoint
currently implies that event IDs are globally unique, which although may be true, is not optimal
for storage mechanics of all homeservers.

Event IDs are considered globally unique in Matrix currently regardless of this MSC due to how
Synapse treats events and Synapse's position in shaping the early specification for Matrix. This
MSC doesn't change how event IDs are globally unique, but does change how they are fetched over
federation for a more consistent and versatile API.

Some modern server implementations, like Dendrite, are looking to run a process/database per-room
instead of a model like Synapse where (usually) one process handles all rooms. The merits of this
architecture are somewhat up for discussion, however this MSC aims to make architectures like
Dendrite's more possible given the prevalence of the room ID always being nearby to an event ID.

Prior to this MSC the spec core team had a discussion regarding whether or not event IDs are globally
unique and largely concluded that they are for the reasons given in the second paragraph above: due
to Synapse's position while the spec was being developed and Synapse's architecture design, event IDs
are implicitly globally unique. A question remains as to whether or not it is valid to continue
offering a `GET /event/:eventId` endpoint over federation (and thus the client-server API) to expose
this detail or to create a new endpoint which better represents how events are expected to be contained
within a room (for a more RESTful API).

The spec core team's prior discussion ultimately lead to [matrix-doc#2779](https://github.com/matrix-org/matrix-doc/issues/2779)
which did not really have enough information to it. After clarifying aspects of the problem space on
the issue and in [#matrix-spec:matrix.org](https://matrix.to/#/#matrix-spec:matrix.org), this MSC was
created to create a discussion around the GET endpoint's validity in Matrix.

## Proposal

In short, this MSC introduces a new federation endpoint `GET /_matrix/federation/v1/room/:roomId/event/:eventId`
which replaces the existing [`GET /_matrix/federation/v1/event/:eventId`](https://matrix.org/docs/spec/server_server/r0.1.4#get-matrix-federation-v1-event-eventid)
endpoint. The response and request parameters are largely the same with the following addition:
If the event ID is not in the room, or the room is not known to the server, a 404 `M_NOT_FOUND`
error is returned.

The existing `GET /event/:eventId` endpoint is to be deprecated and discouraged from use.

The global uniqueness of event IDs does not change under this proposal - event IDs must still be
globally unique in all current room versions (1 through 6). Room versions 3 and newer implicitly
accomplish this as the event ID is the reference hash of the event itself, which includes the
room ID. Version 1 and 2 rooms are namespaced to the server and have a localpart whose format
is decided upon by the implementation. All that changes with this proposal is how the events
are accessed over federation.

The requirement to keep event IDs unique might cause issues for servers like Dendrite in v1 and
v2 rooms as they might not be able to guarantee global uniqueness within their namespace. A
potential solution for these implementations is to calculate a partial reference hash of the
event (ie: before the `event_id` field is added to the event) and then use the result in the
event ID's localpart. The server would still have to recalculate the hash once the event ID is
added to the event, however this would be a safe way of guaranteeing uniquness, at least within
the namespace. Other solutions include appending a worker ID or using an ID generating service
in the software stack.

For backwards compatibility, if the server returns a failing HTTP status code without a reasonable
error code (`M_NOT_FOUND`, `M_FORBIDDEN`, etc) on the newly proposed endpoint, the server should retry
the request with the deprecated endpoint.

The debate to keep `GET /event/:eventId` as-is has some very strong arguments to it, however.
For instance, it allows permalinks (as proposed by [MSC2644](https://github.com/matrix-org/matrix-doc/pull/2644))
to be shorter and more understandable, particularly if Matrix moves to a model where the room ID
becomes unbearably large for users to pass around. [MSC2695](https://github.com/matrix-org/matrix-doc/pull/2695)
is a proposal which supports MSC2644 in its endeavour for using event IDs in place of room IDs,
and is the opposite to what this MSC suggests - instead of replacing the federation endpoint,
MSC2695 de-deprecates the client-server endpoint and enhances it to allow for better chances at
finding the event over federation.

Another argument for keeping the `GET /event/:eventId` endpoint as it stands is one of resource
cost and bandwidth: by not having to include a room ID in the request, the request is using less
bytes over the wire. If [MSC1228](https://github.com/matrix-org/matrix-doc/pull/1228) or
[MSC2787](https://github.com/matrix-org/matrix-doc/pull/2787) (if modified slightly) were to be
adopted, room IDs could have a potential for being significantly longer as well, further benefiting
the bandwidth argument.

The final prevalent argument for keeping the `GET /event/:eventId` endpoint untouched is one of
potential future capacity: though all room events (events which receive an event ID) are implicitly
dumped into a room, it may be desirable to break this pattern in a future proposal. No practical
use cases have been brought to the attention of the author to explain what that future proposal might
look like.

This MSC's answers to the above 3 arguments aren't particularly strong, but it does at least have answers:

For the permalink shortness concern, MSC2644 could define an encoding format that shortens the overall
length of the permalink or use an alternative structure entirely. Encoding would still have its
drawbacks due to the complexity of identifiers, and an alternative structure feels a bit hypocritical
for this MSC to suggest given it is currently suggesting to eliminate the easiest and simplest answer.
In any case, the alternative solution could be to embed a URL shortener into Matrix as suggested around
[this comment](https://github.com/matrix-org/matrix-doc/pull/2848/files#r518192302) on an earlier
version of this MSC.

On bandwidth: yes, there would be a higher cost with this MSC due to including the room ID in the
request parameters. Typically this sort of argument would be countered by saying it's making the system
no worse (which is true), however the justification for making a system no worse instead of better
tends to fall apart quickly. This MSC does not have an immediate answer against the bandwidth concern
and favours API consistency and usability, discussed later.

The final argument regarding future-proofing the API for a possibility of roomless events somewhat
writes itself into a corner - by not having a strong use case, it's hard to determine how valid the
concern is. This MSC keeps event IDs as globally unique despite the API change though, which should
allow for a return of the `GET /event/:eventId` endpoint if needed once a use case arises.

This MSC's core argument for replacing the `GET /event/:eventId` endpoint is one of consistency and
familiarity within Matrix: all other endpoints in the server-server and client-server APIs already
reference event IDs alongside their respective room IDs. This goes as far as referencing the two
identifiers together in events/systems like room upgrades and read receipts. The single example, aside
from the contested endpoint itself, where this convention is not true is in the `m.in_reply_to` format.
However, the specification for that `event_id` field also says the referenced event *should* belong
to the same room as the event being sent, but doesn't have to be.

Matrix roughly follows the principles of REST where it can, and this new endpoint would be in line with
that. The client-server API already has the equivilant endpoint, which implicitly maps the event to a
room - the federation API can (and should, in this MSC's view) do the same.

Introducing this new endpoint also assists server implementations like Dendrite which are looking to
route traffic to the best possible process/database for efficient lookups. This is done implicitly
by including the room ID in the endpoint. Server implementations more similar to Synapse should have
no performance impact from using this new endpoint either - they can still easily find the event ID
then do a quick check to make sure it belongs to the room requested before completing the request.

Finally, because the server should always know which room ID it expects a given event to be in, it
should be able to populate the request over federation with the details. When a server is validating
an event or has just called `/state_ids`, it knows which room ID to expect and thus can supply it.

## Potential issues

See above - the issues with this proposal are mixed in with the proposal body itself to help justify
and walk through the concerns and suggest ways to combat them. Some additional issues/concerns with
this proposal are also discussed in the Alternatives section below.

## Alternatives

There are a few alternatives to this MSC. The most obvious of which is MSC2695 as the complete opposite
to what this MSC proposes - it's described in detail in the Proposal section above.

A risk of this proposal is that new homeserver implementations may assume that events always belong
to rooms and thus ignore all the warning signs about event IDs being globally unique. This wouldn't
be a detectable issue in v3+ rooms, but could be an issue for that implementation if they decide to
implement v1 or v2. A potential alternative to this MSC that solves that problem, aside from MSC2695,
would be to drop the global uniqueness of event IDs entirely and declare they are in fact bound to
a specific room. In practice this would negatively affect Synapse as it then has to change its database
schema, and would remove the possibility for future use cases where events with IDs aren't associated
with a particular room. It may be entirely reasonable to do this, though, as it would reduce developer
confusion and help keep a more familiar model of events being in rooms.

Another alternative would be to go a step further than MSC2695 and fix/deprecate all the APIs which
reference event IDs alongside room IDs, thus making them truly globally unique. This would reinforce
a potential use case for events with IDs existing outside rooms, and would blatantly indicate to new
server implementations that the event IDs are globally unique.

Both of these suggestions are a bit on the extreme side however. We may be able to solve the potential
problem of misunderstanding the global uniqueness rule with implementation guides, warnings in the spec,
and other supporting documentation.

## Security considerations

All the existing security considerations are covered by importing the behaviour of the existing endpoints,
with the added restrictions for the added parameters.

## Unstable prefix

The federation API can be awkward to detect support for unstable features, however if a server wishes
to try anyways it can use `org.matrix.msc2848` as the unstable prefix. This makes the new endpoint
`GET /_matrix/federation/unstable/org.matrix.msc2848/room/:roomId/event/:eventId` during the pre-spec
era of this MSC.
