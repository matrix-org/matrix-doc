# Signaling Errors at Bridges

Sometimes bridges just silently swallow messages and other events. This proposal
enables bridges to communicate that something went wrong and gives clients the
option to give feedback to their users. Clients are given the possibility to
retry a failed event and bridges can signal the success of the retry.

## Proposal

Bridges might come into a situation where there is nothing more they can do to
successfully deliver an event to the foreign network they are connected to. Then
they should be able to inform the originating room of the event about this
delivery error. The user in turn should be able to instruct the bridge to retry
sending the message that was presented him as failed; the bridge should have the
ability to mark an error as being revoked.

If [MSC 1410: Rich
Bridging](https://github.com/matrix-org/matrix-doc/issues/1410) is utilized for
this proposal it would additionally give the benefits of

- trimming the number of properties required in each bridge error event by
  separately providing these general infos about the bridge in the room state instead.
- not requiring users representing the bridge to have admin power levels
  (see [Rights management](#rights-management)).

### Bridge error event

This document proposes the addition of a new room event with type
`m.bridge_error`. It is sent by the bridge and references an event previously
sent in the same room, by that marking the original event as “failed to deliver”
for all users of a bridge. The new event type utilizes reference aggregations
([MSC
1849](https://github.com/matrix-org/matrix-doc/blob/matthew/msc1849/proposals/1849-aggregations.md#relation-types))
to establish the relation to the event its delivery it is marking as failed.
There is no need for a new endpoint as the existing `/send` endpoint will be
utilized.

Additional information contained in the event are the name of the bridged
network (e.g. “Discord” or “Telegram”) and a regex array¹ describing the
affected users (e.g. `@discord_.*:example.org`). This regex array should be
similar to the one any Application Service uses for marking its reserved user
namespace. By providing this information clients can inform their users who in
the room was affected by the error and for which network the error occurred.

*Those two fields will not be required if the variant with [MSC 1410: Rich
Bridging](https://github.com/matrix-org/matrix-doc/issues/1410) is adopted. In
this case the same information is stored alongside other bridge metadata in the
room state*

There are some common reasons why an error occurred. These are encoded in the
`reason` attribute and can contain the following types:

* `m.event_not_handled` Generic error type for when an event can not be handled
  by the bridge. It is used as a fallback when there is no other more specific
  reason.

* `m.event_too_old` A message will – with enough time passed – fall out of its
  original context. In this case the bridge might decide that the event is too
  old and emit this error.

* `m.foreign_network_error` The bridge was doing its job fine, but the foreign
  network permanently refused to handle the event.

* `m.unknown_event` The bridge is not able to handle events of this type. It is
  totally legitimate to “handle” an event by doing nothing and not throwing this
  error. It is at the discretion of the bridge author to find a good balance
  between informing the user and preventing unnecessary spam. Throwing this
  error only for some subtypes of an event is fine.

* `m.bridge_unavailable` The homeserver couldn't reach the bridge.

* `m.no_permission` The bridge wanted to handle an event, but didn't have the
  permission to do so.

The bridge error can provide a `time_to_permanent` field. If this field is
present it gives the time in milliseconds one has to wait before declaring the
bridge error as permanent. As long as an error is younger than this time, the
client can expect the possibility of the error being revoked. If a bridge error
is permanent, it should not be revoked anymore. In case this field is missing,
the error will never be considered permanent.

Notes:

- Nothing prevents multiple bridge error events to relate to the same event.
  This should be pretty common as a room can be bridged to more than one network
  at a time.

- A bridge might choose to handle bridge error events, but this should never
  result in emitting a new bridge error as this could lead to an endless
  recursion.

The need for this proposal arises from a gap between the Matrix network and
other foreign networks it bridges to. Matrix with its eventual consistency is
unique in having a message delivery guarantee. Because of this property there is
no need in the Matrix network itself to model the failure of message delivery.
This need only arises for interactions with foreign networks where message
delivery might fail. This proposal extends Matrix to be aware of these error
cases.

Additionally there might be some operational restrictions of bridges which might
make it necessary for them to refrain from handling an event, e.g. when hitting
memory limits. In this case the new event type can be used as well.

This is an example of how the new bridge error might look:

```
{
    "type": "m.bridge_error",
    "content": {
        "network: "Discord",
        "affected_users": ["@discord_.*:example.org"],
        "reason": "m.bridge_unavailable",
        "time_to_permanent": 900,
        "m.relationship": {
            "rel_type": "m.reference",
            "event_id": "$some:event.id"
        }
    }
}
```

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\
¹ Or similar – see [Security Considerations](#security-considerations)

### Retries and error revocation

Providing a way to retry a failed message delivery gives the sender control over
the importance of her message. An extra procedure for a retry is necessary as
the message might have been delivered to some users (those not on the bridge)
and this would produce duplicate messages for them.

A retry request is posted by the client to the room for all bridges to see it,
referencing the original event. By inspecting the sender of all related
`m.bridge_error` events, under all bridges the correct one can find out that it
is responsible. The responsible bridge re-fetches the original event and retries
to deliver it.

A successful retry should be communicated by revoking (not redacting) the
original error that made the retry necessary. Revocation is done by an event
with the type `m.bridge_error_revoke` which references the original event. The
error(s) having a sender of the same bridge as the revocation event are
considered revoked. Clients can show a revocation message e.g. as “Delivered to
Discord at 14:52.” besides the original event.

On an unsuccessful retry the bridge may edit the error's content to reflect the
new state, e.g. because the type of error changed or to communicate the new
time.

Example of the new retry events:

```
{
    "type": "m.bridge_retry",
    "content": {
        "m.relationship": {
            "rel_type": "m.reference",
            "event_id": "$original:event.id"
        }
    }
}
```

```
{
    "type": "m.bridge_error_revoke",
    "content": {
        "m.relationship": {
            "rel_type": "m.reference",
            "event_id": "$original:event.id"
        }
    }
}
```

Overview of the relations between the different event types:

```
                           m.references
 ________________     _____________________
|                |   |                     |
| Original Event |-+-|    Bridge Error     |
|________________| | |_____________________|
                   |  _____________________
                   | |                     |
                   +-|    Retry Request    |
                   | |_____________________|
                   |  _____________________
                   | |                     |
                   +-| Bridge Error Revoke |
                     |_____________________|
```

A retry might not make much sense for every kind of error e.g. retrying
`m.unknown_event` will probably result in the same error again. Clients may
choose to disable retry options for those cases, but it is not restricted
otherwise.

### Special case: Unavailable bridge

In the case the bridge is down or otherwise disconnected from the homeserver, it
naturally has no way to inform its users about the unavailability. In this case
the homeserver can stand in as an agent for the bridge and answer requests in
its absence.

For this to happen, the homeserver will send out a bridge error event in the
moment a transaction delivery to the bridge failed. The clients at this point
will start showing an error. When the bridge comes back online it will encounter
a higher-than-normal load as all events accumulated over the downtime are
flooding in. To handle this scenario well, the bridge will want to simply
discard all messages older than a given threshold and not bother with sending
any answer back.

By including a timeout in the `time_to_permanent` field of the event, the client
will know without further feedback from the homeserver or bridge when the
message won't be delivered anymore.

For those events still accepted by the bridge, the error must be revoked by a
`m.bridge_error_revoke` as described in the previous chapter.

**Note:** For this to work, the homeserver is required to impersonate a user of
the bridge as it has no agent of its own. The impersonated user would be the
bridge bot user or one of the virtual users in the bridge's namespace.

### Rights management

Only bridges should be allowed to send bridge errors and revocations.

Utilizing the rights system of the room provides a good approximation to this
behavior. It is fine to use it under the assumptions that

- `m.bridge_error` and `m.bridge_error_revoke` require admin power levels.
- there is always the bridge bot user or a virtual user in the bridge's
  namespace present in the room.
- at least one of those users possesses admin power level.
- all users with admin power levels are trusted.

In short, this requires giving bridges admin power levels in a room and trusting
them to restrict their actions to their own business. It is enough to have one
privileged bridge user in the room. In public rooms this is most commonly the
bridge bot user with admin power level available and in 1:1 conversations it is
the puppeted conversation partner which does generally have admin power levels
as well.

As long as the above assumptions are met, it is fine to not explicitly denote
bridges and bridge users as such and simply rely on the power levels for access
control to the new events.

An alternative for the above solution is the adoption of [MSC 1410: Rich
Bridging](https://github.com/matrix-org/matrix-doc/issues/1410). It stores
information about users affiliation to a bridge in the room state. Instead of
checking power levels of users, rich bridging can be utilized by checking the
room state and only allow valid representatives of the bridge to send bridge
errors and their revocations. This alternative has the advantage of not
requiring agents of the bridge to be powerful. They would be verifiable and
could be trusted without any restrictions regarding their power levels.

## Tradeoffs

Without this proposal, bridges could still inform users in a room that a
delivery failed by simply sending a plain message event from a bot account. This
possibility carries the disadvantage of conveying no special semantic meaning
with the consequence of clients not being able to adapt their presentation.

A fixed set of error types might be too restrictive to express every possible
condition. An alternative would be a free-form text for an error message. This
brings the problems of less semantic meaning and a requirement for
internationalization with it. In this proposal a generic error type is provided
for error cases not considered in this MSC.

The nature of a retry request from a client to the bridge lends it more to an
ephemeral type of transport than something permanent like a PDU, but it was
advised against it for The Spec doesn't make implementations of new EDU types
easy. Applications Services in general don't allow listening to EDUs, so further
changes to The Spec would be necessary before following the probably more
appropriate route here.

A new event type `m.bridge_error_revoke` is introduced for revoking a bridge
error. Alternatively it could be considered to redact the bridge error event,
which would eliminate the need for the revocation event and would make this
proposal a little simpler. The disadvantage of this approach is the missing
transparency and context of who had which information at which point in time.
This additional information should make for a better user experience.

## Potential issues

When the foreign network is not the cause of the error signaled but the bridge
itself (maybe under load), there might be an argument that responding to failed
messages increases the pressure.

## Security considerations

Sending a custom regex with an event might open the doors for attacking a
homeserver and/or a client by exposing a direct pathway to the complex code of a
regex parser. Additionally sending arbitrary complex regexes might make Matrix
more vulnerable to DoS attacks. To mitigate these risks it might be sensible to
only allow a more restricted subset of regular expressions by e.g. requiring a
maximal length or falling back to simple globbing.

When utilizing power levels instead of building on [MSC 1410: Rich
Bridging](https://github.com/matrix-org/matrix-doc/issues/1410) a malicious user
who has enough power to send `m.bridge_error` or `m.bridge_error_revoke` is able
to impersonate a bridge. She will be able to wrongly mark messages as failed to
deliver or revoke errors when they were not successfully retried.

## Conclusion

In this document an event is proposed for bridges to signal errors and a way to
retry and revoke those errors. The event informs the affected room about which
message errored for which reason; it gives information about the affected users
and the bridged network. By implementing the proposal Matrix users will get more
insight into the state of their (un)delivered messages and thus they will become
less frustrated.
