# Proposal for self-destructing messages

It's useful for users to be able to send sensitive messages within a
conversation which should be removed after the target user(s) has read them.
This can be achieved today by the sender redacting the message after the
receipient(s) have read them, but this is a tedious manual process. This
proposal provides a way of automating this process.

Originally [MSC1763](https://github.com/matrix-org/matrix-doc/pull/1763)
attempted to solve this by applying retention limits on a per-message basis
and purging expired messages from the server; in practice this approach is
flawed because purging messages fragments the DAG, breaking back-pagination
and potentially causing performance problems.  Also, the ability to set an
expiration timestamp relative to the send (rather than read) time is not of
obvious value.  Therefore the concept of self-destructing messsages was
split out into this independent proposal.

## Proposal

Users can specify that a message should self-destruct by adding one or more of
the following fields to any event's content:

`m.self_destruct`:
  the duration in milliseconds after which the participating servers should
  redact this event on behalf of the sender, after seeing an explicit read
  receipt delivered for the message from all users in the room. Must be null
  or an integer in range [0, 2<sup>53</sup>-1]. If absent, or null, this
  behaviour does not take effect.

`m.self_destruct_after`:
  the timestamp in milliseconds since the epoch after which participating
  servers should redact this event on behalf of the sender. Must be null
  or an integer in range [0, 2<sup>53</sup>-1]. If absent, or null, this
  behaviour does not take effect.

Clients and servers MUST send explicit read receipts per-message for
self-destructing messages (rather than for the most recently read message,
as is the normal operation), so that messages can be destructed as requested.

The `m.self_destruct` fields are not preserved over redaction (and
self-destructing messages may be redacted to speed up the self-destruct
process if desired).

The `m.self_destruct` fields must be ignored on `m.redaction`events, given it
should be impossible to revert a redaction.

E2E encrypted messages must store the `m.self_destruct` fields outside of the
encrypted contents of the message, given the server needs to be able to act on
it.

Senders may edit the `m.self_destruct` fields in order to retrospectively
change the intended lifetime of a message.  Each new `m.replaces` event should
be considered to replace the self-destruction information (if any) on the
original, and restart the destruction timer.  On destruction, the original
event (and all `m.replaces` variants of it) should be redacted.

## Server-side behaviour

When a client sends a message with `m.self_destruct` information, the servers
participating in a room should start monitoring the room for read receipts for
the event in question.

Once a given server has received a read receipt for this message from a member
in the room (other than the sender), then the message's self-destruct timer
should be started for that user.  Once the timer is complete, the server
should redact the event from that member's perspective, and send the user a
synthetic `m.redaction` event in the room to the reader's clients on behalf of
the sender.

The synthetic redaction event should contain an `m.synthetic: true` flag on
the reaction's content to show the client that it is synthetic and used for
implementing self-destruction rather than actually sent from the claimed
client.

For `m.self_destruct_after`, the server should redact the event and send a
synthetic redaction once the server's localtime overtakes the timestamp given
by `m.self_destruct_after`. The server should only perform the redaction once.

## Client-side behaviour

Clients should display self-destructing events in a clearly distinguished
manner in the timeline.  Details of the lifespan can be shown on demand
however, although a visible countdown is recommended.

Clients should locally remove `m.self_destruct` events as if they have been
redacted N milliseconds after first attempting to send the read receipt for the
message in question.  The synthetic redaction event sent by the local server
then acts as a fallback for clients which fail to implement special UI for
self-destructing messages.

Clients should locally remove `m.self_destruct_after` events when the local
timestamp exceeds the timestamp indicated in the `m.self_destruct_after`
field.

Clients should warn the sender that self-destruction is based entirely on good
faith, and other servers and clients cannot be guaranteed to uphold it.
Typical text could be:

	"Warning: recipients may not honour disappearing messages".

We recommend exposing the feature in UX as "disappearing messages" rather than
"self-destructing messages", as self-destruction implies a reliability and
permenance that the feature does not in practice provide.

Other possible user-friendly wording might include:
 * Ephemeral messages (which feels even less reliably destructive than
   'disappearing', but may be too obscure a word for a wide audience)
 * Vanishing messages (which implies they reliably vanish)
 * Vanishable messages (which is clunky, but more implies that it's an intent
   rather than a guarantee)
 * Evanescent messages (which is too obscure, but implies that it's a message
   which /can/ vanish, rather than that it /will/)
 * Fleeting messages (which is again quite an obscure word)
 * Transient messages (too techie)
 * Temporary messages (could work)
 * Short-term messages

## Threat model

Any proposals around coordinating deletion of data (e.g. this,
[MSC1763](https://github.com/matrix-org/matrix-doc/issues/1763),
[MSC2278](https://github.com/matrix-org/matrix-doc/issues/2278)) are sensitive
because there is of course no way to stop a malicious server or client or user
ignoring the deletion and somehow retaining the data. (We consider any attempt
at trying to use DRM to do so as futile).

This MSC is intended to:

 * Give a strong commitment to users on trusted clients and servers that
   message data will not be persisted on Matrix servers and clients beyond the
   requested timeframe.  This is useful for legal purposes in rooms which span
   only trusted (e.g. private federated) servers, to enforce data retention
   behaviour.

 * Give a weak commitment to users on untrusted clients and servers (e.g.
   arbitary users on the public Matrix network) that message data may not be
   persisted beyond the requested timeframe.  This should be adequate for
   unimportant disappearing messages (e.g. a casual fleeting message which is so
   unimportant or of such shortlived relevance that it is not worthy of being put
   in the timeline).  It is **not** adequate for attempting to ensure that
   sensitive content is deleted after reading for legal or security purposes.

 * Help server admins manage diskspace by letting users dictate retention
   lifetime per message.

## Tradeoffs

We could purge rather than redact destructed messages from the DB, but that
would fragment the DAG so we don't do that.

We could have the sending server send an explicit redaction event on behalf of
the sender rather than synthesise a redaction on the various participating
servers.  However, this would clog up the DAG with a redundant event, and also
introduce unreliability if the sending server is unavailable or delayed.  It
would  also result in all users redacting the message the same time. Therefore
synthetic per-user redaction events (which are only for backwards
compatibility anyway) feel like the lesser evil.

## Issues

We should probably ignore missing read receipts from bots when deciding
whether to self-destruct.  This is blocked on having a good way to identify
bots.  [MSC1206](https://github.com/matrix-org/matrix-doc/pull/1206) provides
one possible way, as does
[MSC2199](https://github.com/matrix-org/matrix-doc/pull/2199) (important v.
unimportant users in immutable DMs).

The behaviour for rooms with more than 2 participants ends up being a bit
strange. The client (and server) starts the expiry countdown on the message as
soon as the participant has read it.  This means that someone can look over
the shoulder of another user to see the content again.  This is probably a
feature rather than a bug(?)

## Security considerations

There's scope for abuse where users can send obnoxious self-destructing messages
into a room.

One solution for this could be for server implementations to implement a
quarantine mode which initially marks redacted events as quarantined for N days
before deleting them entirely, allowing server admins to address abuse concerns.
This is of course true for redactions in general.

## Conclusion

This provides a simple and pragmatic way of automating the process of manually
redacting sensitive messages once the recipients have read them.
