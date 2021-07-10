# MSC3005: Streaming Federation Events

Currently, Matrix Federation works via
[transactions](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v1-send-txnid),
encapsulating queued PDUs and EDUs and sending them through individual HTTP requests.

This system can be slow or otherwise resource-intensive in a number of ways, through how each
transaction request is largely the same (except content and maybe `txn` ), and how each goes through
the entire HTTP request chain for every single transaction, which can hamper Time-To-Deliver over federation.

## Proposal

The proposal as thus is to then standardize a full-duplex streaming convention, to be used with
matrix federation. This is optionally implementable, and the scope of this document is not to define
specific ways to implement this stream (such as WebSockets, TCP/TLS, or other specific
bi-directional network channels)

This proposal, and the Federation Stream, assumes a full-duplex framed binary "pipeline", over which any kind
of data is streamed in-order, with framing available to both consuming ends.

The Federation Stream is intended as a faster-yet-compatible carrier alternative to
`/federation/v1/send`, and is thus intended to not receive exclusive features that also aren't able
to be used in HTTP-REST format, that pertain to the basic way federation is done, and aren't
executable with `v1/send`. (Until a day comes where Federation Streaming is the primary way of
federation-event-sending).

Federation Streams are **unidirectional by default**, meaning that events are sent only by the
side that initiated the stream ("requesting side", see [glossary](#glossary)), though this can be
changed with [a proposed extension](#proposed-extensions).

### Basic Frame

The basic frame of the stream consists of 1 leading byte, and then a payload.

That first byte denotes the [opcode](#opcodes), effectively a `u8`/`uint8`/`byte`.

The remaining payload is defined per opcode, with formatting defined per-connection (see
[opcodes](#opcodes) and [`hello`](#hello) below).

### Handshake

Upon establishing a federation streaming connection, the requesting side needs to first send a
[`hello`](#hello) frame denoting various possible options it supports, and to propose several
options (and possible extensions) to start working with.

The responding side will send a [`greetings`](#greetings) frame, after which actual data can be sent
over the connection, the greetings frame will contain accepted options and extensions to use on the
connection.

#### Front-loading

The hello-greetings handshake can be front-loaded when using other protocols to upgrade to a stream,
such as HTTP-to-WebSocket. The definition of how these protocols encode front-loading is out of
scope of this document, but the following can be a recommendation;

> In the specific example of HTTP-to-WS, the `hello` frame's options can be encoded in the GET/POST
> request via it's body, or via it's headers. The server can respond the `greetings` frame in
> returning headers (in which the same response also performs a connection upgrade with `101`).

Again, the above is an example, is not a definition that this spec enforces, but merely an
illustration of how front-loading could work.

### Opcodes

#### Control Frames

Control frames denote a change, notification, or other event happening on the current stream, these
should be processed synchronously (i.e. as soon as possible).

The opcode prefix is `0xF~`.

##### Hello

`opcode: 0xF1`

The `Hello` frame contains all information used to define how the following connection will behave.

The payload of the `Hello` frame MUST be encoded in UTF-8 `JSON`. This is for compatibility purposes,
and makes it's easier for implementations to always fall-back to simple methods, yet switch to
faster formatting when possible.

|   Field   | Description                  | Type                    | Omit default        |
| :-------: | ---------------------------- | ----------------------- | ------------------- |
|   `fmt`   | Standard format support      | `array[integer]`        | `[0]`               |
| `fmt_ext` | Extended (custom) formatting | `array[string]`         | `[]`                |
|   `ext`   | Extension settings           | `object{string: value}` | `{}`                |
| `origin`  | Origin server domain         | `string`                | (cannot be omitted) |

If a field is missing from the JSON, the omit default must be assumed (with the exception of
`origin`, which is required.)

`fmt` is defined as an array of integers, of which, the requester signals which [payload
formats](#defined-payload-formats) it supports. Payload format `0` MUST always be supported.

`fmt_ext` is defined as an array of strings, these strings should take the form of
java-domain-notation, such as `org.erlang.etf.v1`. These strings define custom-domain format
standards to be defined by any third-party as they wish, stability and complete isn't guaranteed by
this proposal.

`ext` is an object of strings to "free `value`s", meaning it's key-value value can take on the form of any value of
[object notation](#object-notation). The string should take the form of java-domain-notation, such
as `m.p2p.pipelining`. Values are for possible extension support, and actual sent settings should
only be perceived active after the `Greetings` frame.

`origin` is analogous to the `origin` field in
[`v1/send`](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v1-send-txnid),
denoting what `server_name` the requesting side has.

##### Greetings

`opcode: 0xF2`

The `Greetings` frame contains information the responding side would want to use for the rest of the
Stream.

Like the `Hello` frame, it is also encoded in UTF-8 `JSON`, and only after this frame has been
received by the requesting side, should frame payload formatting be considered altered or freely
defined.

|    Field     | Description                        | Type                     | Omit default        |
| :----------: | ---------------------------------- | ------------------------ | ------------------- |
|    `fmt`     | Chosen format                      | `integer | string`       | (Cannot be omitted) |
|    `ext`     | Echoed extension settings          | `object{string: value}`  | `{}`                |
| `ext_op_map` | Mapped extension-frames-to-opcodes | `object{string: string}` | `{}`                |

If a field is missing from the JSON, the omit default must be assumed (with the exception of `fmt`)

`fmt` must either be a `string` or `integer`, this is to make formatting acknowledgement explicit.
If `integer`, one of the [defined payload formats](#defined-payload-formats) is chosen for the
Stream. If `string`, one of the previously-proposed extended formatting (in the `Hello` frame) must
be used.

`ext` is an object of "free values" as defined in the `Hello` frame, this is a "roger-roger"
echo-and-acknowledgement field, the responding side populates this field from the `Hello` frame,
after checking compatibility with registered extensions. The settings in here are final, and should
be assumed to be the actual extension settings this Stream will now be operating under.

`ext_op_map` is an object of string keys to string values. The keys must be the uppercase hex byte
value of the opcode about to be mapped (e.g. `"E0"`). The values should be java-domain-notation of
the extension frame type to be mapped to this opcode for this session (e.g. `m.p2p.pipeline`).

##### Heartbeat Request

`opcode: 0xF5`

Either side can send a heartbeat request, which then must be answered by a corresponding [heartbeat
response](#heartbeat-response).

Exact semantics when a heartbeat should be considered timed out are out of scope for this document,
but a grace period of minimal 10 seconds should at least be generally accepted.

The payload body must be a random `integer` as nonce, to prevent collisions.

##### Heartbeat Response

`opcode: 0xF6`

To be sent by the other side after receiving a [Heartbeat Request](#heartbeat-request).

The payload body must be the received `integer` of the heartbeat request frame.

##### Goodbye

`opcode: 0xFF`

To be sent by either side to close the Stream gracefully, this should immediately close the
Stream once the other side echoes this frame.

Any more frames should not be sent by the receiving end of this frame, yet it is possible (due to
latency, or due to flushing) that this might happen.

The payload body must be `null`.

#### Time Synchronization Frames

*TODO: make echo-response protocol able to weather some network conditions, time sync should at
least ping-pong 2 times and compare latency each time, keep ping-ponging to reduce doubt and jitter
if necessary, fed traffic should be calmed or paused during this sequence*

*Utilize 2 RTTs (A-B-A-B) to get average latency, then calculate TS offsets (with received TS value
and half of tested averaged RTT latency value)*

*opcode prefix: `0x1~`*

#### Data Frames

Data frames contain the most central information for federation; PDUs and EDUs. These can be
processed asynchronously.

The opcode prefix is `0x0~`.

##### PDU

`opcode: 0x00`

For a PDU to be sent to the other side, to be responded with with a [`PDU Ack`](#pdu-ack).

The payload data must be a free `object` value exact to the objects as defined in the `"pdus"` array [in
the `v1/send` spec](https://matrix.org/docs/spec/server_server/latest#put-matrix-federation-v1-send-txnid).

##### PDU Ack

`opcode: 0x02`

Acknowledges the PDU sent from the other side.

The payload data must be a `string` value of the "ID of the PDU" as defined [in the `v1/send` spec,
under "PDU processing
results"](https://matrix.org/docs/spec/server_server/latest#put-matrix-federation-v1-send-txnid).

If this is not received by the sending server, the PDU frame must be considered not received, and may be
sent again, or must be sent again after re-establishing the Stream.

##### EDU

`opcode: 0x03`

For an EDU to be sent to the other side, to be responded with with an [`EDU Ack`](#edu-ack).

The payload data must be a free `object` value to the definition of the "Ephemeral Data Unit" in [in
the `v1/send`
spec](https://matrix.org/docs/spec/server_server/latest#put-matrix-federation-v1-send-txnid), with
one caveat; an additional `nonce` field is added, with type `integer`, this `nonce` must be unique
over the course of the entire Federation Stream's lifetime, for the side that sends these nonces.

For clarity, here is the full abridged definition of an EDU, all fields required;

|   Field    | Type      | Description                                                 |
| :--------: | --------- | ----------------------------------------------------------- |
| `edu_type` | `string`  | The type of ephemeral message.                              |
| `content`  | `object`  | The content of the ephemeral message.                       |
|  `nonce`   | `integer` | The unique nonce to the ephemeral message, for this Stream. |

##### EDU Ack

`opcode: 0x04`

Acknowledges the EDU sent from the other side.

The payload must be a `integer` value of the `EDU::nonce` field received.

##### EDU Nonce Vacuum

`opcode: 0x0A`

Because EDU nonces must be unique over the course of the entire Federation Stream's lifetime, it
could possibly build up memory pressure to track thousands of nonces on both sides of the connection
for uniqueness.

This Frame aims to vacuum entire swaths of nonces from the other side's memory.

The payload data is an `object`, defined as following, all fields required;

|  Field  | Type      | Description                       |
| :-----: | --------- | --------------------------------- |
| `start` | `integer` | Start of the range to be vacuumed |
|  `end`  | `integer` | End of the range to be vacuumed.  |

When received, all EDU nonce values inside the (inclusive) range between both integer values must be
perceived as usable by the sender again (from the receiver's perspective).

##### Error

`opcode: 0x0F`

Acknowledges the PDU sent from the other side with an error.

The payload must be an `array`, sized with 2 `value`s, defining each as follows;

First value; a `string` responding to the specific PDU event being responded to.

Second value; a free `value` detailing the error of processing this EDU. It should probably be a
`string`, or an `object` with an `"error"` key, but this is not absolutely required.

How server implementations react to PDU errors is out of scope for this proposal.

### Defined Payload Formats

This document does not define additional payload formats other than `0`, which is UTF-8 `JSON`-formatting
for every payload.

Formatting must only affect the payload.

#### Object Notation

Every payload format must be able to support basic object notation, which is redefined here for
clarity's sake:

> 2 Structures;
> - `object` (key-value)
> - `array` (of values)
>
> 5 Values;
> - `string`
> - `integer`
> - `float`
> - `boolean`
> - `null`

2 important distinctions from plain JSON; `float` and `integer` are different values, and are explicitly defined
instead of being folded into JSON's ambiguous `number`. `null` is a seperate value here, for
correctness' sake when a field or a value can be multiple things (e.g. `integer | null`).

For the purposes of this document, a `value` can be any of above (both structures and values).

### Extensions

Extensions to the Federation Stream can be defined (through `Hello/Greetings`), but must never
interfere with;

- The first byte leading in a frame.
- Opcodes laid out in this proposal.
- ["Standard" defined formatting](#defined-payload-formats).

#### Proposed Extensions

Here are some proposed extensions, the `Hello/Greetings::ext` setting values per these extension
strings are immediately denoted after it's name.

`m.heartbeat.interval`: `integer`, The time in milliseconds the expected heartbeat interval should
be. The requesting side should send heartbeat requests as close to this timeout as possible. For the
responding side, when a heartbeat interval of 1.5x has passed, it should send a heartbeat request.

`m.heartbeat.retries`: `integer`, The amount of unanswered heartbeat requests have to exist before
the connection is deemed dead.

`m.heartbeat.timeout`: `integer`, The time in milliseconds before a heartbeat request "times out"
for one side, this is symbolic, as it is still possible for the other side to respond to a
"timed-out" heartbeat.

`m.federation.bidirectional`: `boolean`, If the requesting side of the Federation Stream is able to
receive pushed events from the Responding Side, obviously `false` if omitted.

##### Possible future extensions

This is an idea-bucket for future proposals, nothing here is applicable directly to this proposal,
but should inform it's possible use-case, and how freely its definitions should be.

- Sequencing, being able to stop and resume Streams per last or newly generated sequence number (to
  switch between federation workers)

#### Opcode Extensions

The Bytes reserved for opcode extensions are `0xA0`-`0xEF`.

Extensions can possibly define frames of their own, these are proposed during `Hello`, and mapped
during `Greetings`, for this, 79 different byte-values can be used.

### Glossary

"Requesting side", this is the side that initiates the Federation Stream, and is consequently the
side to send a [`Hello`](#hello) frame.

"Responding side", this is the side that receives the initiation for the Federation stream, this
side must respond to a `Hello` frame with a [`Greetings`](#greetings) frame.

"Nonce", while in british english slang meaning something much more different, for this document,
it means (per wikipedia);

> In cryptography, a nonce is an arbitrary number that can be used just once in a cryptographic
> communication. [...] It is often a random or pseudo-random number issued in an authentication
> protocol to ensure that old communications cannot be reused in replay attacks.

Nonces are there to ensure an event isn't possible to be duplicated.

### Optimizations

An optimization strategy might be this: when sending an event out of nowhere to a server, it'll
likely be less intensive (for a one-time event) to utilize `v1/send`, however, when a server detects
it is sending a few events per hour to that server, it should try to find ways to establish a
Federation Stream, to lower the overhead for future events.

The tradeoff between establishing a Federation Stream immediately and "just" utilizing `v1/send`
should be researched and weighed for every individual implementation, and there is no one singular
optimization strategy that may be possible, and this proposal does not try to restrict these
possibilities, only suggest and guide them.

## Imposed requirements on the underlying connection

As mentioned before, the Federation Stream (and this proposal) assumes that the underlying transport
on which it sends frames is *framed*, this means that either side consumes a chunk of data at a
time, which in this case is the opcode and it's corresponding payload.

This was done to deduplicate behaviour from possible underlying transports, where some of which are
capable of providing a framing mechanism by itself to the application side.

However, some transports will or aren't able to provide a framed consumption interface to specific
applications, these issues are intended to be hashed out in future proposals at a time, but for now,
here are a few advisories to those proposals.

(Please note that "payload" here means the entire frame of opcode + internal payload)

- When using terminating byte sequences (such as NULL, `0x00`), take extra care, as the payload or
  opcode could carry these bytes with them internally.

  This method is *NOT RECOMMENDED*, due to aforementioned potential of those byte-sequences existing
  in payload or opcode, which then have to be escaped, and un-escaped before serving to the stream
  handler.

- When leading with an amount of bytes that signify payload size, assume that the payload size can
  possibly be the max of a 4-byte `uint` (i.e. `u32`).

  The rationale of this is that a 2-byte payload size (`u16`) is too small for some possible event
  sizes (64 KB), as the current soft-assumed limit is one megabyte.

  A 3-byte payload size header, while relatively right for assumed payload size (~16 MB), is awkward
  for platforms to deal with, as casting a 3-byte integer to a 4-byte `uint32` can be a footgun to
  implement.

- Alternatively, using a VarInt as leading payload size is recommended, given that guardrails exist
  to assure that a malicious actor cannot perform exploits such as buffer overruns, or send
  Denial-of-Service attacks by making the server allocate an arbitrarily large buffer, sanity checks
  should exist in these cases.

## Potential issues

Not all servers could implement this, so support must never be primarily assumed, a server must be
able to fall back to `v1/send`.

In the form of a multi-process matrix server, architectural design should be considered when
thinking about supporting [`m.federation.bidirectional`](#proposed-extensions), as this would
convert the requesting side into a federation receiver as well, as bidirectional support is only
known when the stream is already established, maybe either a "prodding" federation endpoint should
be added to get pre-requisite knowledge about bidirectional Federation Stream support, or the
requesting side must pipeline received data via another connection a federation receiver.

## Alternatives

**WebTransport**: A [new draft standard](https://w3c.github.io/webtransport/) in progress,
abstracting network interfaces, making it easier for user-facing applications to build APIs on top
of networking APIs.

This proposal is out of scope for defining specific mechanisms or transports over which to work out
Federation Streams, the same applies to direct TCP/TLS of WebSockets, while examples may be made
that include these mechanics, this proposal does not specify how these would work.

WebTransport *can* be complementary to future proposals detailing how exactly Federation Streams must
or could be established.

**HTTP/2**: A new HTTP paradigm, utilizing one connection, multiplexing streams that handle HTTP
requests with compressed headers in binary.

HTTP2 offers many optimization strategies, and has some interesting potential applications in
parallelizing federation transactions, but eventually, the best optimization is simply to eliminate
the HTTP request router-matching stack through which all those requests must eventually go through.

**Do Nothing**: Do Nothing, keep the current HTTP-`v1/send` mechanic.

While a viable option, and keeping as a reliable always-existing fallback, this is not fast, as
a direct connection would be able to overcome time and processing between receiving a payload for a PDU/EDU,
due to how directly it's IO could be delivered to application code that handles it, decreasing latency.

## Concerns and Questions

`Hello` defines an `origin` field, just like `v1/send`, but with the (potential) support for
bidirectionality, how would the other server send an `origin` back? Via changed `Greetings::ext`
(`m.federation.origin`) settings?

## Security considerations

None that aren't already applicable to `v1/send`.

## Unstable prefix

For experimental implementations of this spec, `ws:/federation/unstable/nl.jboi.msc3005/stream` should
be used. While it is out of scope for this document to define an exact endpoint, this could be used
for implementation testing purposes.
