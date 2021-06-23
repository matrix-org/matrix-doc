# MSC3079: Low Bandwidth Client-Server API

The Client-Server API is not bandwidth efficient, relying on HTTP and human-readable JSON as a data
format. It is desirable to provide low bandwidth alternatives for mobile or low power devices. This
proposal specifies a CoAP/CBOR alternative to the existing HTTP/JSON API. This proposal
*will not replace* the existing HTTP/JSON APIs. Both protocols are expected to co-exist together.
This MSC has the potential to have a significant beneficial impact on mobile devices power
(and hence battery) consumption. It would also open up the possibility of the `/sync` API being used
in the background of mobile devices as a form of Matrix Push Notification, removing the need for
proprietary push systems such as GCM/APNS. Furthermore, it allows Matrix to run faster on
low bitrate links (e.g 1-5Kbps).

This proposal produces extremely low packet sizes of around 180 bytes to send a message,
and 150 bytes for the response. Keep alive idle traffic is around 88 bytes per heartbeat
interval (e.g per minute). 

## Proposal

The current Client-Server API stack, along with the proposed alternatives are as follows:
 - JSON -> CBOR
 - HTTP -> CoAP
 - HTTP long-polling -> CoAP OBSERVE (optional)
 - TLS/TCP -> DTLS/UDP

Media endpoints are not covered by this proposal. Clients will have to use the standard HTTP CS API to upload
or download files. This proposal covers everything under `/_matrix/client`.

The rest of this proposal breaks down each option and fleshes out the implementation/rationale.

### JSON -> CBOR

JSON is human-readable and not bandwidth efficient at all. It is extensible (you can add custom keys)
and this is a property which MUST be preserved. This makes static schema based data formats such as
Protocol Buffers inappropriate for use. CBOR is widely used and is standardised as
[RFC 8949: Concise Binary Object Representation](https://tools.ietf.org/html/rfc8949). Implementations
exist in [many languages](https://cbor.io/impls.html). Any valid JSON can be represented as CBOR with
[sensible representations](https://www.rfc-editor.org/rfc/rfc8949.html#name-converting-from-json-to-cbo).

This proposal goes beyond just "Use CBOR" however. This proposal also specifies integer keys which act
as shorthand for long string keys. This compresses data more efficiently. This shorthand may look similar
to:
```
{
  "custom_key": "value",
  8: 18572837543,
}
```
Where `8` is statically mapped to a string key e.g `origin_server_ts`. This means it is possible for
a key to be defined twice: once as a number and once as a string. If this happens, the string key
MUST be used. It is NOT required that keys which have integers are represented as such; the integer
mapping is entirely optional. String representations of numbers e.g `"8"` MUST NOT be expanded, and
should be treated literally. As JSON does not allow integer keys, this prevents any ambiguity when
converting from CBOR to JSON. The complete key enum list is in Appendix A and represents version 1
of the CBOR key mappings. Further versions are intended to be backwards compatible i.e. we only ever
add keys.

Clients MUST set the `Content-Type` header to `application/cbor` when sending CBOR objects.
Similarly, servers MUST set the `Content-Type` header to `application/cbor` when responding with CBOR
to requests. Servers MUST NOT respond to requests with `Content-Type: application/json` with CBOR,
unless the `Accept` header in the client's request includes `application/cbor`.

The following test object is represented in [Canonical CBOR](https://tools.ietf.org/html/rfc7049#section-3.9)
in order to make it useful (e.g keys are sorted). [Matrix does not allow IEEE floats.](https://spec.matrix.org/unstable/appendices/#canonical-json)

JSON:
```
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Hello World"
  },
  "sender": "@alice:localhost",
  "room_id": "!foo:localhost",
  "unsigned": {
    "bool_value": true,
    "null_value": null
  }
}
```

Intermediate:
```
{
  2: "m.room.message",
  3: {27: "Hello World", 28: "m.text"},
  5: "!foo:localhost",
  6: "@alice:localhost",
  9: {"bool_value": true, "null_value": null}
}
```

CBOR:
```
a5026e6d2e726f6f6d2e6d65737361676503a2181b6b48656c6c6f20576f726c64181c666d2e74657874056e21666f6f3a6c6f63616c686f7374067040616c6963653a6c6f63616c686f737409a26a626f6f6c5f76616c7565f56a6e756c6c5f76616c7565f6
```

### HTTP -> CoAP

CoAP is defined in [RFC 7252: Constrained Application Protocol](https://tools.ietf.org/html/rfc7252)
and is intended to be bandwidth efficient. It defines mappings to and from HTTP. Implementations exist
in [many languages](https://coap.technology/impls.html). This allows the existing HTTP CS API to be mapped
to CoAP request/responses.

This proposal goes beyond just "Use CoAP" however. This proposal also specifies single character path
enums which act as shorthand for certain commonly used CS API paths. This compresses data more efficiently.
This shorthand may look similar to:
```
/9/!7mqP7DYBUOmwAweF:localhost/m.room.message/$.AAABeH6obLU
```
which is the collapsed form of:
```
/_matrix/client/r0/rooms/!7mqP7DYBUOmwAweF:localhost/send/m.room.message/$.AAABeH6obLU
```
Where `9` is statically mapped to the path regexp `/_matrix/client/r0/rooms/{roomId}/send/{eventType}/{txnId}`.
The path parameters in the mapping should be read left to right to determine where they should exist in the
shortened form. In this example, the short mapping is `/9/{roomId}/{eventType}/{txnId}`. Paths which do
not have any path parameters only have one path segment e.g `/_matrix/client/r0/sync` is just `/7`.
This path mapping is optional, and servers MUST accept the full paths. The complete path enum list is in
Appendix B and represents version 1 of the CoAP path mappings. Further versions are intended to be backwards
compatible e.g we only ever add paths.

#### Access Tokens

CoAP defines many mappings but notably has no Option mapping for `Authorization` headers. This proposal marks
the option ID 256 as `Authorization` in accordance with the [CoAP Option Registry](https://tools.ietf.org/html/rfc7252#section-12.2)
which mandates that options IDs 0-255 are reserved for IETF review. This Option should have the same Critical,
UnSafe, NoCacheKey, Format and Length values as the `Uri-Query` Option. The `Authorization` value SHOULD omit
the "Bearer " prefix to save on bytes, though this is optional and servers MUST handle both with and without
the prefix.

In addition, this Option MAY be omitted on subsequent requests, in which case the server MUST use the last
used value for this Option. This reduces bandwidth usage by only sending the access token once per connection.
Upon establishing a new CoAP connection (determined by the underlying transport), the client MUST send the
Option again. If this Option is set on subsequent requests, servers MUST use the Option in the latest request
and discard the previously stored Option value. This makes this functionality optional from a client's perspective,
but required from a server's perspective.


### HTTP long-polling -> CoAP OBSERVE

*This feature is entirely optional. Clients can continue using HTTP long-polling with CoAP requests.*

The CS API currently relies on long-polling to retrieve new events from the server. This is bandwidth inefficient
as the background traffic is high when there are no events. This proposal allows the `/sync` endpoint to be observed
using [RFC 7641: CoAP OBSERVE](https://tools.ietf.org/html/rfc7641). The registration SHOULD be keyed off the tuple
of (access_token, coap token ID). This allows the same device to have multiple OBSERVE registrations. All pushed
events MUST be sent as Confirmable messages to ensure that the client received the events. The pushed events MUST
look identical to a normal `/sync` response, which includes the `next_batch` token. When the client disconnects and
reconnects with a new registration, they can use the `next_batch` token to resume where they left off. If a client
doesn't acknowledge an event despite multiple attempts to do so, the registration SHOULD be removed to avoid consuming
server resources and network bandwidth.

Clients MAY re-register with the `/sync` endpoint if they believe their registration was deleted e.g due to loss of
internet connectivity. Servers SHOULD retry sending events in the event of a re-register request, if the registration
is active but backing off. This ensures that servers proactively send events to the client in a timely manner.

Large `/sync` responses cannot be sent as a single message. In this case, RFC 7641 mandates that the client performs
a GET request to the resource (`/sync`) and performs blockwise transfers to retrieve the data. Servers MUST ensure
that the blockwise data returned from this request matches the data being pushed e.g by remembering which `/sync`
response was last pushed to the client.

### TLS/TCP -> DTLS/UDP

This proposal allows servers to listen on UDP ports for CoAP requests. It is recommended that the port listened
on matches the same TCP port for the same functionality, e.g port 8008/udp for the CS API. Management and configuration
of the DTLS connection is out of scope for this proposal.

CoAP requests MUST be supported on this UDP port.

DEFLATE is a compression algorithm which can further reduce bandwidth usage. Blanket compression
algorithms are vulnerable to the [CRIME attack](https://tools.ietf.org/html/rfc7525#section-3.3), so any
compression algorithm must be explicitly opt-in. DTLS connections MAY support DEFLATE as a
[compression method](https://tools.ietf.org/html/rfc3749#section-2.1), and should be negotiated in the TLS
handshake.

### Versioning

In order to aid discovery, servers MUST add an extra key to `/_matrix/client/r0/versions` which indicates
which low bandwidth features are supported on this server. This object looks like:
```
"m.low_bandwidth": {
  "dtls": 8008,            // advertise that this server runs a UDP listener for DTLS here.
  "cbor_enum_version": 1,  // which table is used for integer keys. This proposal is version 1. Omission indicates no support.
  "coap_enum_version": 1,  // which table is used for coap path enums. This proposal is version 1. Omission indicates no support.
  "observe": 1,            // Set to 1 if /sync supports OBSERVE. Omission indicates no support for OBSERVE.
}
```

Clients MAY negotiate which CBOR version to use with the server by sending an option ID 257 with a `uint` value (defined in
RFC 7252) set to the CBOR version requested. This value should be 'sticky' and remembered across requests for the lifetime
of the underlying connection. Absence of this option indicates no CBOR enum support in the client UNLESS the client sends
numeric keys in its request bodies, in which case Version 1 MUST be assumed. This negotiation is required so servers know
whether to push numeric CBOR keys to clients. It is not required for CoAP versions as these are always client-initiated.

### Summary of required features

Many features in this proposal are optional. The fundamental features required in order for a server to declare itself
as "low-bandwidth" in the `/versions` response are:
 - Accept `application/cbor`. CBOR integer keys are optional.
 - Accept CoAP requests with access token Option stickiness. CoAP path enums are optional.
 - Accept DTLS/UDP requests.

Servers which support low bandwidth can advertise this by the presence of the `m.low_bandwidth` key in the `/versions` response.

## Potential issues

Browsers are currently unsupported due to their inability to send UDP traffic.
[RFC 8323: CoAP over TCP, TLS, and WebSockets](https://tools.ietf.org/html/rfc8323) may provide a
way for browsers to participate over WebSockets but this is out of scope for this proposal.

DTLS operates over UDP which is "connectionless". This makes restarting connections after restarting the server difficult.
TCP has the concept of FIN packets, which let the client know that the connection they currently are using is dead and
should be terminated. UDP has no equivalent. For this reason, restarting the server will take up to the connection timeout
value for clients to detect a dead connection. This can be shortened by modifying DTLS to send `CloseNotify` alerts when
the UDP socket receives unrecognised data.

Matrix servers perform "remote echo", where messages a client send get returned in the `/sync` stream. Changing this
behaviour would invasively modify the behaviour of servers and clients. Clients and test suites often rely on this
remote echo to determine when the message has been fully processed in the server. Servers rely on incrementing sync
tokens for each new event. Suppressing remote echo would add extra complexity to handling sync streams. For these
reasons, the sync stream will remain as it is for now. In the future, low bandwidth modifications may be applied
to the sync stream, which will be negotiated when registering an OBSERVE request.

## Alternatives

HTTP/3 over QUIC (which is UDP) was considered but rejected due to large initial connection sizes, which
mandate 1200 bytes of padding.

## Security considerations

DTLS connections should have the same security guarantees as TLS connections. Weak ciphers should not be used.

If a DTLS connection is hijacked, an attacker can send requests without the need for an access token.

OBSERVE could potentially send encrypted traffic to addresses which, in the worst case scenario, are attacker
controlled. Without the DTLS session keys this traffic should remain secure.


## Unstable prefix

The `/versions` response should use `org.matrix.msc3079.low_bandwidth` instead of `m.low_bandwidth` whilst the proposal is in review.

### Appendix A: CBOR integer keys

This is version 1 of this table.

| Key Name | Integer |
|----------|---------|
|event_id|                    1|
|type|                        2|
|content|                     3|
|state_key|                   4|
|room_id|                     5|
|sender|                      6|
|user_id|                     7|
|origin_server_ts|            8|
|unsigned|                    9|
|prev_content|                10|
|state|                       11|
|timeline|                    12|
|events|                      13|
|limited|                     14|
|prev_batch|                  15|
|transaction_id|              16|
|age|                         17|
|redacted_because|            18|
|next_batch|                  19|
|presence|                    20|
|avatar_url|                  21|
|account_data|                22|
|rooms|                       23|
|join|                        24|
|membership|                  25|
|displayname|                 26|
|body|                        27|
|msgtype|                     28|
|format|                      29|
|formatted_body|              30|
|ephemeral|                   31|
|invite_state|                32|
|leave|                       33|
|third_party_invite|          34|
|is_direct|                   35|
|hashes|                      36|
|signatures|                  37|
|depth|                       38|
|prev_events|                 39|
|prev_state|                  40|
|auth_events|                 41|
|origin|                      42|
|creator|                     43|
|join_rule|                   44|
|history_visibility|          45|
|ban|                         46|
|events_default|              47|
|kick|                        48|
|redact|                      49|
|state_default|               50|
|users|                       51|
|users_default|               52|
|reason|                      53|
|visibility|                  54|
|room_alias_name|             55|
|name|                        56|
|topic|                       57|
|invite|                      58|
|invite_3pid|                 59|
|room_version|                60|
|creation_content|            61|
|initial_state|               62|
|preset|                      63|
|servers|                     64|
|identifier|                  65|
|user|                        66|
|medium|                      67|
|address|                     68|
|password|                    69|
|token|                       70|
|device_id|                   71|
|initial_device_display_name| 72|
|access_token|                73|
|home_server|                 74|
|well_known|                  75|
|base_url|                    76|
|device_lists|                77|
|to_device|                   78|
|peek|                        79|
|last_seen_ip|                80|
|display_name|                81|
|typing|                      82|
|last_seen_ts|                83|
|algorithm|                   84|
|sender_key|                  85|
|session_id|                  86|
|ciphertext|                  87|
|one_time_keys|               88|
|timeout|                     89|
|recent_rooms|                90|
|chunk|                       91|
|m.fully_read|                92|
|device_keys|                 93|
|failures|                    94|
|device_display_name|         95|
|prev_sender|                 96|
|replaces_state|              97|
|changed|                     98|
|unstable_features|           99|
|versions|                    100|
|devices|                     101|
|errcode|                     102|
|error|                       103|
|room_alias|                  104|

### Appendix B: CoAP Path Enums

This is version 1 of this table.

| Path Enum | Matrix Path Regexp |
|-----------|--------------------|
|0| /_matrix/client/versions|
|1| /_matrix/client/r0/login|
|2| /_matrix/client/r0/capabilities|
|3| /_matrix/client/r0/logout|
|4| /_matrix/client/r0/register|
|5| /_matrix/client/r0/user/{userId}/filter|
|6| /_matrix/client/r0/user/{userId}/filter/{filterId}|
|7| /_matrix/client/r0/sync|
|8| /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}|
|9| /_matrix/client/r0/rooms/{roomId}/send/{eventType}/{txnId}|
|A| /_matrix/client/r0/rooms/{roomId}/event/{eventId}|
|B| /_matrix/client/r0/rooms/{roomId}/state|
|C| /_matrix/client/r0/rooms/{roomId}/members|
|D| /_matrix/client/r0/rooms/{roomId}/joined_members|
|E| /_matrix/client/r0/rooms/{roomId}/messages|
|F| /_matrix/client/r0/rooms/{roomId}/redact/{eventId}/{txnId}|
|G| /_matrix/client/r0/createRoom|
|H| /_matrix/client/r0/directory/room/{roomAlias}|
|I| /_matrix/client/r0/joined_rooms|
|J| /_matrix/client/r0/rooms/{roomId}/invite|
|K| /_matrix/client/r0/rooms/{roomId}/join|
|L| /_matrix/client/r0/join/{roomIdOrAlias}|
|M| /_matrix/client/r0/rooms/{roomId}/leave|
|N| /_matrix/client/r0/rooms/{roomId}/forget|
|O| /_matrix/client/r0/rooms/{roomId}/kick|
|P| /_matrix/client/r0/rooms/{roomId}/ban|
|Q| /_matrix/client/r0/rooms/{roomId}/unban|
|R| /_matrix/client/r0/directory/list/room/{roomId}|
|S| /_matrix/client/r0/publicRooms|
|T| /_matrix/client/r0/user_directory/search|
|U| /_matrix/client/r0/profile/{userId}/displayname|
|V| /_matrix/client/r0/profile/{userId}/avatar_url|
|W| /_matrix/client/r0/profile/{userId}|
|X| /_matrix/client/r0/voip/turnServer|
|Y| /_matrix/client/r0/rooms/{roomId}/typing/{userId}|
|Z| /_matrix/client/r0/rooms/{roomId}/receipt/{receiptType}/{eventId}|
|a| /_matrix/client/r0/rooms/{roomId}/read_markers|
|b| /_matrix/client/r0/presence/{userId}/status|
|c| /_matrix/client/r0/sendToDevice/{eventType}/{txnId}|
|d| /_matrix/client/r0/devices|
|e| /_matrix/client/r0/devices/{deviceId}|
|f| /_matrix/client/r0/delete_devices|
|g| /_matrix/client/r0/keys/upload|
|h| /_matrix/client/r0/keys/query|
|i| /_matrix/client/r0/keys/claim|
|j| /_matrix/client/r0/keys/changes|
|k| /_matrix/client/r0/pushers|
|l| /_matrix/client/r0/pushers/set|
|m| /_matrix/client/r0/notifications|
|n| /_matrix/client/r0/pushrules/|
|o| /_matrix/client/r0/search|
|p| /_matrix/client/r0/user/{userId}/rooms/{roomId}/tags|
|q| /_matrix/client/r0/user/{userId}/rooms/{roomId}/tags/{tag}|
|r| /_matrix/client/r0/user/{userId}/account_data/{type}|
|s| /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/{type}|
|t| /_matrix/client/r0/rooms/{roomId}/context/{eventId}|
|u| /_matrix/client/r0/rooms/{roomId}/report/{eventId}|
