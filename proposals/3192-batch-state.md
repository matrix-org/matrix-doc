# MSC3192: Batch state endpoint

It is desired to potentially dump a bunch of state into a room  in one go. This
is useful to:

* Kick (or ban) many users at once.
* Invite many users at once.
* Add many rooms to a [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) Space.
* Bulk-insert [MSC2313](https://github.com/matrix-org/matrix-doc/pull/2313)-style reputation data.

## Proposal

A new endpoint is added to send multiple state events to a room in a single request.

This endpoint is authenticated and rate-limited.

`PUT /_matrix/client/r0/rooms/{roomId}/batch_state/{txnId}`

Example request:

```json
[
  {
      "event_type": "m.room.membership",
      "state_key": "@alice:example.com",
      "content": {
          "membership": "join",
          "avatar_url": "mxc://localhost/SEsfnsuifSDFSSEF",
          "displayname": "Alice Margatroid"
      }
  }
]
```

Example response:

```json
[
  "$YUwRidLecu:example.com"
]
```

This API extends the [current ways to push state into a room](https://matrix.org/docs/spec/client_server/latest#sending-events-to-a-room)
by allowing for multiple events for differing state keys to be created with a single API call.

Path parameters:

* `room_id`: **Required.** The room to set the state in
* `txnId`: **Required.** The transaction ID for this state update. Clients should
  generate an ID unique across requests with the same access token; it will be
  used by the server to ensure idempotency of requests.

The body of the request should be an ordered array of objects with the following
keys:

* `event_type`: **Required.** A string. The type of event to send.
* `state_key`: A string. The state_key for the state to send. Defaults to the
  empty string.
* `content`: **Required.** The content object of the event; the fields in this object will vary
  depending  on the type of event. See [Room Events](https://matrix.org/docs/spec/client_server/latest#room-events)
  for the `m.` event specification.

At most 50 events can be included in the request body.<sup id="a1">[1](#f1)</sup>

The body of the response will contain an array of the created event IDs. If an
event cannot be created then `null` will be returned in its place.

Error responses:

* Status code 400: No events were successfully sent.
* Status code 403: The sender doesn't have permission to send the event(s) into
  the room.

This also updates the previous definition to note that
`PUT /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}` should be
rate-limited.

## Potential issues

Handling a partial batch of state updates could lead to unexpected behavior, but
should not be worse than the current situation (where each state event must be
sent individually).

## Alternatives

### Request body

A request body consisting of nested objects with event types and state keys as the
keys pointed to their content was considered, but it seemed not in the style of
other Matrix APIs. This alternative would look something like:

```json
{
    "m.room.member": {
        "@alice:example.com": {
            "membership": "join",
            "avatar_url": "mxc://localhost/SEsfnsuifSDFSSEF",
            "displayname": "Alice Margatroid"
        }
    }
}
```

### Atomic requests

Handling the request atomically and returning an error if any of the state events
cannot be created for some reason could be nicer. (See [a similar discussion](https://github.com/matrix-org/synapse/issues/7543)
involving the federation API: `/_matrix/federation/v1/send/{txnId}`.)

### Batch inserting state and messages

The [MSC2716](https://github.com/matrix-org/matrix-doc/pull/2716): Incrementally
importing history into existing rooms has need to insert both state and messages
at the same time. This is used to insert messages plus their auth state at the
same time.

It is possible this API could be expanded to cover that use-case, but given the
current specialization needed to handle MSC2716 there does not exist an
example use-case for handling both state and messages at the same time.

## Security considerations

The main risk of this endpoint is a denial of service attack (against a server
directly or an amplification attack by using a server to spam over federation).

An example scenario would be:

* An unprivileged user creates a public chatroom; has PL 100
* Persuades loads of people into it (e.g. via spam or invite-spam, which should
  have other mitigations in place)
* Starts looping creating `m.space.*` (or any other state) events en bulk
* Causes loads of PDUs to be pushed over federation, as well as loads of state
  resolution due to the rapidly churning state of the room.

This is no more amplification than any other federation traffic, but it makes it
easier for a single unsophisticated user to create a large amount of federation
traffic, getting their local homeserver into trouble, without them having to run
a malicious homeserver themselves.

However, other than consuming resources, there's no particular benefit in doing
so, and there are other similar attacks (e.g. uploading lots of large files into
a room and encouraging folks to click on them; or joining many large rooms in
quick succession).

Note that, by default, you already have to be a room admin to set arbitrary state
events in the first place, so the only risk here is of room admins going rogue.
You could argue this is just one of many ways an admin could go rogue, and would
need to be dealt with by the server admin on the server where they reside (by
deactivation or puppetting them to self-demote).

The benefits of this API outweigh the risks. Server admins can always put some
monitoring alerts in place to check if they have rogue admins who are
bulk-spamming rooms with state events - and freeze users who do so. It is also
recommended to have a low rate-limit on this endpoint.

There are some measures in the API design which attempt to mitigate some of the
risk.

Limiting each call to a single event type and ensuring that each event type /
state key pair only appears a single time should reduce state resolution churn
to a degree.

Limiting the number of state events in a single API call to match what can be
done by an abusive sever over federation should offer a level of security as
well.

## Unstable prefix

During development of this feature it will be available at an unstable endpoint:

`/_matrix/client/unstable/org.matrix.mscxxxx/rooms/{roomId}/batch_state/{txnId}`

## Footnotes

<a id="f1"/>[1]: This matches the [maximum of 50 PDUs](https://matrix.org/docs/spec/server_server/latest#put-matrix-federation-v1-send-txnid)
that can be in a federation transaction. [↩](#a1)
