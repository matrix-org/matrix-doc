# MSC3077: Support for multi-stream VoIP

This MSC proposes a method for differentiating WebRTC streams from each other.

[MSC2746](https://github.com/matrix-org/matrix-doc/pull/2746) has improved VoIP
immeasurably. Yet, there is still no clear way to handle things such as
screen-sharing.

The simplest possible implementation of VoIP call upgrades would assume that any
new incoming stream would replace the old one. This solution works, but problems
start to appear with the introduction of screen-sharing. There is no way to know
which one of the already existing incoming streams (user-media and
screen-sharing) should a new incoming stream replace. Further, if conferencing
using an SFU (as suggested in
[MSC2359](https://github.com/matrix-org/matrix-doc/pull/2359)) were implemented
there would be no way to know from which user a stream is coming from.
Therefore, a way to differentiate streams from each other is needed.

## Proposal

This MSC proposes adding an `sdp_stream_metadata` field to the events containing
a session description i.e.:

+ `m.call.invite`
+ `m.call.answer`
+ `m.call.negotiate`

The `sdp_stream_metadata` field is an object in which each key is one stream
`id` in the session description. The values are of `SDPStreamMetadata` type and
have the following fields:

+ `purpose` - a string indicating the purpose of the stream. For compatibility
  between clients values `m.usermedia` and `m.screenshare` are defined.
  `m.usermedia` is the stream that contains the webcam and microphone tracks.
  `m.screenshare` is then the stream with the screen-sharing tracks.

### Example

```JSON
{
    "type": "m.call.invite",
    "room_id": "!roomId",
    "content": {
        "call_id": "1414213562373095",
        "invitee": "@bob:matrix.org",
        "party_id": "1732050807568877",
        "lifetime": "60000",
        "capabilities": {
            "m.call.transferee": true,
        },
        "offer": {
            "sdp": "...",
            "type": "offer",
        },
        "sdp_stream_metadata": {
            "271828182845": {
                "purpose": "m.screenshare",
            },
            "314159265358": {
                "purpose": "m.usermedia",
            },
        },
        "version": "1",
    },
}
```

### Edge cases

+ There should _never_ be more than one `SDPStreamMetadata` in
  `sdp_stream_metadata` with the same `purpose`.
+ If an incoming stream is not described, in `sdp_stream_metadata`, it should be
  ignored.
+ If a stream has `purpose` of an unknown type (i.e. not `m.usermedia` or
  `m.screenshare`), it should be ignored.

### Backwards compatibility

During the initial invite and answer exchange clients find out if the field
`sdp_stream_metadata` is missing. If it is not present in the event sent by the
oponent, the client should ignore any new incoming streams (i.e. it should use
the first one) and it shouldn't send more than one stream.

## Alternatives

Setting the stream `id`s to custom values had been considered. Though this is
possible on some platforms, it is not in browsers. That is because the `id`
property of `MediaStream` is _read-only_ as the [MDN Documentation
states](https://developer.mozilla.org/en-US/docs/Web/API/MediaStream/id).
Similar is true for SDP attributes.

This proposal is also more practical for cases where more complex metadata is
needed. For conferencing, a `user_id` field could be added to
`SDPStreamMetadata`.

## Unstable prefix

During development, the following fields should be used:

|Release                     |Development                                    |
|----------------------------|-----------------------------------------------|
|`sdp_stream_metadata`       |`org.matrix.msc3077.sdp_stream_metadata`       |
|`m.call.sdp_stream_metadata`|`org.matrix.msc3077.call.sdp_stream_metadata`  |

## Potential issues

None that I can think of.

## Security considerations

None that I can think of.
