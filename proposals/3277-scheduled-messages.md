# MSC3277: Scheduled messages

## Introduction

It's sometimes useful to schedule messages so that recipients will read them
at a point in the future rather than immediately.  Use cases include:

 * Not wanting to disturb the recipient(s) out-of-hours
 * Wanting to remind yourself or others of some information in future
 * Releasing embargoed information at a given time.

This is a simplified proposal derived from Travis' [original draft](https://docs.google.com/document/d/1vFbQuCnCNURBRs4_zukxiKLW_p2Ka7Ogo42oahpXnz4),
which aims to incorporate all the feedback gathered there.

## Proposal

A new query parameter, `at`, is added to the [/send](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-send-eventtype-txnid)
and [PUT /state](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-state-eventtype-statekey)
endpoints to indicate when the origin server should aim to send the event
(milliseconds since the unix epoch). The message is added to the room DAG
when the sender creates the event, and is immediately relayed to the sender's
devices (as a remote echo) but not the other members in the room.

It is then effectively soft-failed until the scheduled `at` time (or as close
to it as the server can manage), when it is then re-authed and relayed as
normal to all room members (both local and remote, including the sender).
Scheduled events are sent out over over federation at this point rather than
creation time in order to minimise embargo leaks.  If the event can't be
re-authed (e.g. due to the sender no longer being in the room, or no longer
has sufficient PL to send the event) then the event is soft-failed.  As such,
the event effectively appears as if it had been received over federation
after a federation delay.  This means all event types can be scheduled in
this manner, including state events.  Normal event ID and redaction behaviour
applies.  

The server must set the `origin_server_ts` of the message is set to be its
`at` time, given in practice this is the label used for clients to display
the intended delivery timestamp of a message.  It must also set `scheduled:
true` on the event (not the contents) in order to let servers know to treat
it differently for history visibility purposes, and so the sender's clients
all know that it's scheduled.  The recipients can then also see the message
is scheduled. (A future MSC may define how to suppress this field from
recipients if desired).

For rooms with non-shared history visibility, servers must special-case the
visibility of scheduled events based on the membership of the room at the
scheduled time, rather than based on its DAG position (which reflects the
creation time).

The sender's clients will want to track the unsent scheduled messages in its
various rooms, such that the sender can cancel them by redacting them, or
edit them (optionally redacting earlier versions <sup id="a1">[1]
(#f1)</sup>, providing private drafting).  We propose using the same
mechanism as for tracking 'starred'(aka 'favourited' or 'flagged') messages,
to avoid sprouting two different APIs for almost identical functionality.
This is deferred to a future MSC.

## Encryption considerations

In an E2EE room, the sending client must distribute the megolm session used to
encrypt the scheduled message immediately to the devices currently in the
room. We then rely on the normal mechanisms used to share megolm keys with
new devices (i.e. keyshare requests; online key backup; MSC3061-style sharing
room keys for past messages) to avoid the messages being undecryptable by
future devices.

The megolm session must be a one-off used just for this scheduled message
(meaning that as it's shared for future participants in the room, it only exposes
the session used to encrypt that particular message rather than any surrounding
non-scheduled ones).

Sender's clients may optionally attempt to wake themselves up at the deadline
in order to re-share the megolm session to the current participants in the
room (and/or be available to respond to keyshare reqs), in order to reduce
the risk of UISIs.

MSC3061-style 'sharing room keys for past messages' will need to special-case
history visibility rules for scheduled messages. Therefore we need to know
which sessions are for scheduled messages, and include them when sharing keys
with new users/devices... but stop once the scheduled message has been
received.  Therefore we add a `m.forward_until: timestamp` field to the
`m.room_key` to-device message to indicate the session's lifetime. The
timestamp should be that of the scheduled event; users who join the room
after that timestamp should not be able to read the message.

E2EE implementations must not discard 'unused' megolm sessions for scheduled
messages (i.e. megolm sessions with `m.forward_until` fields), given they may
be shared long in advance of the scheduled message.

## Possible issues

A risk is that E2EE key distribution mechanisms which rely on clients seeing
an undecryptable message (i.e. keyshare reqs) will not take effect until the
scheduled message is sent - by which point clients which could service the
keyshare reqs will be more likely to be absent due to the passage of time.
One mitigation to this could be to relax the rules on who can service the
keyshare request and let any device in the room share to the newcomer if they
believe the newcomer should be entitled to decrypt the message. This
introduces the attack that a malicious server admin could add a fake
user/device to their local copy of a room, and could use this to exfiltrate
keys from bystanders - but this may be an acceptable tradeoff to improve
the chances of the message being decryptable in the distant future.
Alternatively, MLS may solve this(??)

Another problem is that because we share E2EE to users at msg authoring time, if
users subsequently leave the room, they will still have the keys to read the
scheduled message when it's revealed.  This is probably inevitable.  Clients could
try to solve it by redacting the scheduled message and resending it with a new megolm
session whenever they spot that users (or devices?) have left the room.

## Example

```
PUT /_matrix/client/r0/rooms/!wherever:example.com/send/m.room.message/123?at=1636197454551
{
  "body": "a note to my future self",
  "msgtype": "m.text"
}
```

...would result in the origin server sending the following event to room
recipients at Sat Nov 6 10:17:34 2021 UTC (assuming the event still passed
auth checks):

```json
{
  "content": {
    "body": "a note to my future self",
    "msgtype": "m.text"
  },
  "origin_server_ts": 1636197454551,
  "sender": "@matthew:matrix.org",
  "type": "m.room.message",
  "unsigned": {
    "age": 391
  },
  "event_id": "$FC9MwqLPBzRl1AzLi-qOJbdYeMJFzugORlF6yPJkyII",
  "room_id": "!xYvNcQPhnkzdUmYczI:matrix.org"
}
```

N.B. there's nothing interesting in this event other than its
`origin_server_ts` being set to the `at` parameter, and obviously being
sent out at the scheduled time.

## Alternatives

The origin server could queue the message with a fake event ID and only
attempt to add it to the DAG when it's time to send.  This two-phase commit
complicates the implementation significantly - although it does provide a
slightly simpler solution to the history visibility problem and the problem
of needing to be in a room to cancel your scheduled messages.

Alternatively, the scheduled messages could queue on the receiving client
(thus letting users choose to see them at their leisure).  However, this
kills the "embargo" use case, and complicates the implementation as receiving
clients have to be able to filter for scheduled events and generally shifts
complexity to clients, which is always undesirable as there way more clients
than servers and we want clients to be as simple as possible.

Separately, there's a trade-off between whether you send the queued message
out over federation at the time it's created or at the scheduled time.  If
you send at create-time, it means that the origin server doesn't need to
still be running at the scheduled time. On the other hand, it means that you
are much more likely to break embargos, as one-person homeservers will get
the message ahead of schedule.  We've gone for the more privacy preserving
option (send over federation at the scheduled time).  Plus it acts as an
incentive for people to keep the origin server running ;P. <sup id="a2">[2]
(#f2)</sup>

Another alternative would be to use an API shape where you put a field on the
event contents (e.g. `m.pts` for presentation timestamp) to tell servers and
clients alike that a given message is scheduled.  However, this ends up with
two timestamps on the event (confusing), complicates E2EE further
(don't encrypt the `m.pts`), and makes it harder to hide from recipients
whether a message was scheduled.  So we've stuck with `?at=`.

We could avoid all the e2ee and history visibility problems if the sending
user simply queued the message in their clients until it was ready to send.
However, this of course means they have to keep an always on client somewhere
to send the message at the right time, which feels fragile (or encourages a
longlived serverside client/bot to be run, which could put E2EE at risk).

## Security considerations

This MSC allows for spammers to potentially pre-plan their attacks for
off-peak hours when the moderators may not be present. It also potentially
allows a user to stack up a large number of pending events which all get sent
throughout the day as a disruption attempt. Servers should impose harsh
limits to the number of events a user may schedule, such as a maximum of N
pending events per room (where N < ~5), to reduce the potential for abuse
while still maintaining an amount of usability for common scenarios.

Users could also try to schedule many events at once or schedule such that
they all get sent at once - servers should apply rate limiting on both the
scheduling and sending sides to limit the user’s ability to spam a room.

There's a risk that an attacker could DoS a user with fake megolm sessions
for scheduled messages which never arrive.  This could be mitigated in the
receiving client by enforcing similar limits to those on the server (e.g.
if you receive more than N megolm sessions for scheduled messages from 
a given user in the room, the client could warn and discard them).

This proposal relies on absolute timestamps, and so for it to work sensibly
servers need to have an accurate (e.g. NTP-synced) clock.

## Unstable prefix

Implementations should use `org.matrix.msc3277.at` in place of the at query
parameter, and expose/look for `org.matrix.msc3277` in the
unstable_features` of `/versions` while this MSC is not in a released
version of the spec.

## Footnotes

<a id="f1"/>[1]: A smart server could stop earlier redacted drafts ever
being sent to the destination servers by placing new drafts as siblings
to the old drafts in the DAG rather than as children.  This means that
recipients wouldn't be able to see that the scheduled message was
drafted.  This is a bit of an overenthusiastic optimisation though.

<a id="f2"/>[2]: For P2P, it's likely that the origin server/client will not
be online at the designated time, so we'll want to special-case scheduled
messages for P2P such that they are queued on a privacy-preserving relay
server of some kind rather than queuing on the origin server/client.