# Federation queries to aid with database recovery
The federated nature of Matrix requires each server participating in a room to
maintain a copy of its state. It also requires that state be made available to
other participating servers upon request. If a server loses its copy due to
hardware failure or corruption, this replication property can be employed as a
disaster recovery mechanism. Full restoration of all rooms in which a server
has membership can be achieved within the existing Matrix protocol if and only
if the server operator maintains a list of rooms such that it survives any
disaster.

This proposal assumes a server is recovering without any such room list. It
requires only that the operator know the hostname of at least one remote server
with mutual rooms (e.g. `t2bot.io` or `matrix.org`). Once rooms have been
restored with the initial server, other servers may be revealed and restoration
can occur recursively. It should be noted that if the recovering server is a
member of rooms whose servers are completely Hausdorff, knowledge of multiple
hostnames will be required for full recovery; for the purpose of this specific
proposal, such a concern is negligible.

## Proposal
Our result can be achieved with the addition of a `members` query type for the
existing `GET /_matrix/federation/v1/query/{queryType}` federation endpoint.
The response contains a list of `m.room.member` events which originated from
the requesting server. The responding server extracts these events from the
present state of all rooms.

### Request
A recovering server requests `GET /_matrix/federation/v1/query/members`.

* The query parameter `pdu_ids` modifies the response format: the response
  will contain an array of event ID strings rather than an array of event
  objects.

  > This parameter has practical use during a recursive recovery operation.
    When many servers are queried, it is likely that most of the response data
    will be redundant. The amount of new information learned with each response
    will asymptote away. This indirection provides greater efficiency for the
    algorithm to work at scale.
* The query parameter `limit_per_room=` specifies the maximum number of
  membership events to return per room. An undefined value, or a value of `0`,
  defaults to unlimited (all events). The responding server MAY reduce this
  value, but SHOULD NOT return more events than the specified value.

  > Note that if a limit is imposed, the selection for *which* member events
    are included in the response is implementation dependent.

  > This parameter is intended to enhance the efficiency of this endpoint in
    practice. For example, when a server bridges thousands of users we avoid
    receiving thousands of results for just one room in the response. It is
    likely the requesting server only requires one event to simply learn about
    the room, but we do not wish to complicate this proposal with some
    potentially faulty selection algorithm.

### Response
200: An array of `m.room.member` event objects (or an array of the corresponding
ID strings of those events) originating from the requesting server, found in the
present state of all rooms mutual to the responding server.

> The primary response is an array of events because they are signed by the
  requestor. Junk in the response can be immediately discarded, curtailing
  denial of service vectors. While the request can ask for event IDs only,
  modern IDs are hashes of the corresponding signed events, and we opine that
  with some basic development prudence this parameter's benefit is worthwhile.
