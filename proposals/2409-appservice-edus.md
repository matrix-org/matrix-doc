# MSC2409: Proposal to send EDUs to appservices

*Node: This proposal is a continuation of [MSC1888](https://github.com/matrix-org/matrix-doc/pull/1888)
and deprecates that one.*

The [appservice /transactions API](https://matrix.org/docs/spec/application_service/r0.1.2#put-matrix-app-v1-transactions-txnid)
currently supports pushing PDU events (regular message and state events)
however it doesn't provison for EDU events (typing, presence and more). This means that bridges cannot
react to Matrix users who send any typing or presence information in a room the service is part of.

There is an interest amongst the community to have equal bridging on both sides of a bridge, so that
read reciepts and typing notifications can be seen on the remote side. To that end, this proposal
specifies how these can be pushed to an appservice.

## Proposal

### Changes to the registration file

In order that appservices don't get flooded with EDUs, appservices have to opt-in to receive them by
setting `push_ephemeral` to true. A registration file could look like following:

```yaml
id: "IRC Bridge"
url: "http://127.0.0.1:1234"
as_token: "30c05ae90a248a4188e620216fa72e349803310ec83e2a77b34fe90be6081f46"
hs_token: "312df522183efd404ec1cd22d2ffa4bbc76a8c1ccf541dd692eef281356bb74e"
sender_localpart: "_irc_bot"
# We want to receive EDUs
push_ephemeral: true
namespaces:
  users:
    - exclusive: true
      regex: "@_irc_bridge_.*"
  aliases:
    - exclusive: false
      regex: "#_irc_bridge_.*"
  rooms: []
```

### Changes to the /transactions/ API

The `PUT /_matrix/app/v1/transactions/{txnId}` API currently supports sending PDUs
via the `events` array.

```json
{
  "events": [
    {
      "content": {
        "membership": "join",
        "avatar_url": "mxc://domain.com/SEsfnsuifSDFSSEF#auto",
        "displayname": "Alice Margatroid"
      },
      "type": "m.room.member",
      "event_id": "$143273582443PhrSn:domain.com",
      "room_id": "!jEsUZKDJdhlrceRyVU:domain.com",
      "sender": "@example:domain.com",
      "origin_server_ts": 1432735824653,
      "unsigned": {
        "age": 1234
      },
      "state_key": "@alice:domain.com"
    }
  ]
}
```

This proposal would extend the `PUT /_matrix/app/v1/transactions/` endpoint to include a new key
`ephemeral` to behave similar to the various sections of the CS API `/sync` endpoint.

```json
{
  "ephemeral": [
    {
      "type": "m.typing",
      "room_id": "!jEsUZKDJdhlrceRyVU:domain.com",
      "content": {
        "user_ids": [
          "@alice:example.com"
        ]
      }
    },
    {
      "type": "m.receipt",
      "room_id": "!jEsUZKDJdhlrceRyVU:domain.com",
      "content": {
        "$1435641916114394fHBLK:matrix.org": {
          "m.read": {
            "@rikj:jki.re": {
              "ts": 1436451550453
            }
          }
        }
      }
    }
  ],
  "events": [
    // ...
  ]
}
```

The reason for a new key rather than bundling the events into `events` is that
existing appservices may mistake them for PDUs and could cause undefined behaviour.
While `events` may now be a somewhat misleading name, this is an acceptable tradeoff.

`to-device` messages are a bit special as they are aimed at a particular user/device ID
combo. These events are annotated by the server with a `to_device_id` and `to_user_id`
field at the top level of the EDU for transport to the appservice:

```json5
{
  "type": "m.new_device",
  "sender": "@alice:example.com",
  "to_user_id": "@_irc_bob:example.org",
  "to_device_id": "ABCDEF123",
  "content": {
    "device_id": "XYZABCDE",
    "rooms": ["!726s6s6q:example.com"]
  }
}
```

Note that the EDU is otherwise formatted as it would for client-server API transport.

### Expectations of when an EDU should be pushed to an appservice

It is not clear at face value what should be pushed to an appservice. Appservices claim
namespaces of users which registers "interest" in the rooms where those users reside, as
well as claiming namespaces of rooms for explicit interest. However, not all EDUs are
associated with a single room (presence, etc).

If the EDU is capable of being associated to a particular room, it should be sent to the
appservice under the same rules as regular events (interest in the room means sending it).
For EDUs which are not associated with a particular room, the appservice receives the EDU
if it contextually *would* apply. For example, a presence update for a user an appservice
shares a room with (or is under the appservice's namespace) would be sent to the appservice.

To-device messages for devices belonging to the appservice's user namespaces should always
be sent.

## Potential issues

Determining which EDUs to transmit to the appservice could lead to quite some overhead on the
homeservers side. Additionally, more network traffic is produced, potentially straining the local
network and the appservice more. As such, appservices have to opt-in to receive EDUs.

## Security considerations

The homeserver needs to accuratley determine which EDUs to send to the appservice, as to not leak
any metadata about users. Particularly `m.presence` could be tricky, as no `room_id` is present in
that EDU.

## Unstable prefix

In the transaction body, instead of `ephemeral`, `de.sorunome.msc2409.ephemeral` is used.

In the registration file, instead of `push_ephemeral`, `de.sorunome.msc2409.push_ephemeral` is used.
