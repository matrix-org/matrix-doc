# Proposal to allow room moderators to view redacted event content
## Problem
Currently if a user deletes a message, most clients will immediately forget the
content and spec-compliant server implementations will stop serving the content
to anyone. This instant deletion means that users could potentially send
messages that aren't allowed, and redact them before a moderator sees them.

Most servers don't remove the content from the database immediately (e.g.
Synapse defaults to removing after 7 days), one reason being moderation of
content that the server admins don't want to allow. However, room moderators
don't have any way to access that content, unless they happen to have their own
server.

## Proposal
The proposed solution is extending the `GET /rooms/{roomId}/event/{eventId}`
endpoint with a query parameter called `include_unredacted_content`. Clients
can request the server to include content even if the event has been redacted
by setting the parameter value to `true`.

### Server behavior
Servers MUST check that the requester has a power level higher than or equal to
the `redact` power level in the room.

* If the requester doesn't have permission to view the event in general (e.g.
  not participating in the room), the server retuns a `M_NOT_FOUND` error the
  same way it did before this proposal.
* If the requester doesn't have sufficient power level to view redacted events,
  the server returns a standard error response with the `M_FORBIDDEN` code.
* If the requester has all the necessary privileges to view the content, but
  the server does not have the unredacted content, the server should return one
  of the following error codes:
  * `M_UNREDACTED_CONTENT_DELETED`: The server has deleted the content from its
    database. The server may optionally include a `m.content_keep_ms` key in
    the error that specifies how long it keeps unredacted content.
  * `M_UNREDACTED_CONTENT_NOT_RECEIVED`: The server never received the
    un-redacted content (this can happen if federation is slow and the event
    was redacted before it reached the server)

### Client behavior
Clients should still always remove content when receiving a redaction event,
but if the user has sufficient power, the client may show a button to re-fetch
and display the redacted event content.

### Implementation notes
Some server implementations have implementation-specific concepts of "server
admins". Such servers should allow server admins to bypass the power level
checks involved in viewing redacted events. However, like other similar
implementation details, there won't be any standard way for clients to
determine if they can view a redacted message through server admin privileges.

## Alternatives
### Separate key in power levels
Instead of reusing the `redact` power level, a new key could be introduced.
A new key would have the advantage of allowing more precise control. However,
it would have to be added to the event authorization rules, as otherwise
anyone with enough power to send `m.room.power_levels` could change the level
for the new key, even if it required a higher level than what the user has.

## Potential issues
* Servers aren't required to keep redacted content for any time, and it would
  be rather confusing UX if the show redacted content button in clients never
  worked.
* If a server doesn't get the event before it's redacted, the server may never
  get the unredacted content.

## Unstable prefix
While this MSC is not in a released version of the spec, implementations should
use `net.maunium.msc2815.include_redacted_content` as the query parameter name,
and `net.maunium.msc2815.content_keep_ms` in the error response. The error
codes should use `NET.MAUNIUM.MSC2815` as a prefix instead of `M`.

Additionally, servers should advertise support using the `net.maunium.msc2815`
flag in `unstable_features` in the `/versions` endpoint.
