# MSC2855 - Server Initiated Clear Cache & Reload

Matrix application state is synchronized to clients via repeated requests to [GET
/_matrix/client/r0/sync](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-r0-sync)
in the form of an event-loop. Clients obtain a `next_batch` token in each response
to be used as the `since` parameter in the next request. These responses form
asymmetric updates to a client's state machine: every update causally
happens-after the prior update regardless of the `since` token. The only exception
to this API's causality happens when no `since` token is provided at all. In this
mode commonly known as "initial sync" a client expects a response which does not
build upon prior states conveyed with other `since` tokens: the client's state
machine can start from scratch.

The Matrix protocol and its client implementations are not infallible. Development
errors and bugs in real-world dynamic network software -- a reality which must not
be dismissed when considering even the most ideal circumstances -- can often
result in a desynchronization of a client's state from that of the server. Many
clients, bots, SDK's etc, employ recovery functionality which discards the current
state, followed by an "initial sync" operation. Often this functionality is even
invoked by a human.

Servers, and the infrastructure for their deployment, are not infallible either.
In a typical disaster-recovery scenario, perhaps *any* disaster-recovery scenario,
some recent data at the server will be lost. For example, the last 24 hours of
data restored from an industry standard 21-day magnetic backup solution. In even
lesser cases, as little as a few *seconds* of data may be lost. When this happens,
all `since` tokens (including client state itself) are effectively invalid. This
is problematic to several ends.

All clients attached to a server do not *know* the server has recovered from a
disaster. While the server can respond with an error for an invalid `since` token,
client implementations tend to panic and/or retry the same exact invalidated token
infinitely. When and if a server does provide a reply to what *should* be a
rejected `since` token a client will silently and incorrectly apply updates to its
malformed state.

### Proposal

This MSC proposes a mechanism be standardized within the sync API to force a
client to perform an initial-sync as its next request.

1. (Realistic) An error code could be devised, such as `M_BAD_SINCE_PARAM`,
although unclear at this time which HTTP error code it would ride on. Supporting
clients will recognize this to invoke the functionality.

2. (Idealistic) If the server simply fails to supply a `next_batch` in the
response it indicates to the client that there is no `since` parameter on the next
request and the client should prepare (clear) its state machine to handle that
response accordingly. This is not backward-compatible and will almost certainly
break existing software. It could be possible if an additional capability
parameter was provided by the client in the request parameters and/or query
string.
