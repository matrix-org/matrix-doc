# MSC2487: Proposal to add filtering to Appservices
Currently appservices receive all their designated traffic, this includes echo-backs from themselves.
[As discussed before](https://github.com/matrix-org/matrix-doc/issues/1306) this might be undesired
behaviour. Additionally, with [MSC2409](https://github.com/matrix-org/matrix-doc/pull/2409) appservices
would receive significatnly more data. It seems benificial for performance that it is possible to
filter out which events should be received and which ones should not be received.

## Proposal
It is proposed to add a `filter` object to the registration file of an application service. This
`filter` object would have the exact same definition as the [Client-Server filtering API](https://matrix.org/docs/spec/client_server/latest#filtering).
The homeserver is expected that, if present, the filter is considered and events are filtered accordingly,
prior to sending them to the appservice.

An example registration file with a filter could look like this:

```yaml
id: "IRC Bridge"
url: "http://127.0.0.1:1234"
as_token: "30c05ae90a248a4188e620216fa72e349803310ec83e2a77b34fe90be6081f46"
hs_token: "312df522183efd404ec1cd22d2ffa4bbc76a8c1ccf541dd692eef281356bb74e"
sender_localpart: "_irc_bot" # Will result in @_irc_bot:example.org
namespaces:
  users:
    - exclusive: true
      regex: "@_irc_bridge_.*"
  aliases:
    - exclusive: false
      regex: "#_irc_bridge_.*"
  rooms: []
filter:
  room:
    state:
      types:
        - "m.room.*"
      not_rooms:
        - "!726s6s6q:example.com"
    timeline:
      limit: 10
      types:
        - "m.room.message"
      not_rooms:
        - "!726s6s6q:example.com"
      not_senders:
        - "@spam:example.com"
    ephemeral:
      types:
        - "m.receipt"
        - "m.typing"
      not_rooms:
        - "!726s6s6q:example.com"
      not_senders:
        - "@spam:example.com"
  presence:
    types:
      - "m.presence"
    not_senders:
      - "@alice:example.com"
  event_format: "client"
  event_fields:
    - "type"
    - "content"
    - "sender"
```

As the appservice filtering re-uses the Client-Server API future updates to that filtering API also
updates the appservices one accordingly, e.g. [MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840).

## Potential issues
The homeserver has to add filters to the appservice traffic. This is additional computation time, which
could increase the load. However, as filters generally mean a reduce in network traffic, there is
probably a net performance increase.

## Alternatives
Instead of re-using the filter API of the Client-Server API a new one could be made. However, as the
one in the Client-Server API is very flexible, it seems natural to re-use that one, and if additional
filter types are needed update the one, single filter API.

## Security considerations
As filtering only reduces the amount of things sent to ASs, there are no additional security considerations.
