# MSC3245: Voice messages (using extensible events)

Voice messages are a useful way to quickly send a message to someone without having to use the more
awkward keyboard. Typically short in length, voice messages can be sent as annotated audio files
to recipients.

More information about voice messages and what they can be used for can be found on
[MSC2516 - Voice messages via msgtype](https://github.com/matrix-org/matrix-doc/pull/2516). This
MSC inherits a lot of the beliefs and usecases of that MSC, but instead packages the event contents
a bit differently. Specifically, this makes use of
[MSC1767 - Extensible Events](https://github.com/matrix-org/matrix-doc/pull/1767).

## Proposal

Much like MSC2516, voice messages are defined as OGG files, encoded with Opus, using relatively sane
settings for voice recordings. This proposal does not define specific settings for clients to use,
but does strongly recommend reducing file size without losing audio quality as much as possible. Some
sample settings are:

* Sample rate: 48kHz
* Bitrate: 24kbps
* Mono (single channel)
* Appropriate complexity and resample quality for the platform.
* Encoder application: 2048 (voice, default is typically 2049 as audio). This doesn't have any signficant
  impact on the resulting recording.

We use Opus to be compatible with other messaging platforms, particularly the ones that can be bridged
easily to Matrix. This proposal aims to avoid having bridges (and to a degree, clients) transcode
voice messages as that would liekly push voice messages further away from the "faster communication"
use case. Bridges are already needing to do processing on the events and can see seconds worth of latency:
an extra couple seconds to re-encode a voice message would not be helping that.

No maximum duration is specified, however clients are encouraged not to send long-running recordings
as they might be rejected/ignored on the receiving end for file size reasons. Typically, this should
be less than 5 minutes worth of audio.

MSC1767 is used to package the voice message up in an annotated event format. Readers of this proposal
are encouraged to [read the MSC](https://github.com/matrix-org/matrix-doc/pull/1767) prior to commenting
or parsing this MSC's use of Extensible Events.

An example voice message would be:

```json5
{
  "type": "m.voice",
  "content": {
    "m.text": "Voice message",
    "m.file": {
      "size": 7992,
      "name": "Voice message.ogg",
      "mimetype": "audio/ogg",
      "url": "mxc://example.org/abcdef"
    },
    "m.audio": {
      "duration": 6541,
      "waveform": [0, 256, /*...*/ 1024] // https://github.com/matrix-org/matrix-doc/pull/3246
    },
    "m.voice": {}
  },
  // other fields required by the spec, but not important here
}
```

Of particular note is that the `m.voice` event definition is empty. This is because fundamentally the event
is an audio event, which means looking at the `m.audio` and `m.file` event bodies for relevant information
about the audio clip. The `m.voice` type is simply used to annotate the event for clients which would like
to render voice messages differently to regular audio files. Clients which don't do anything special for
voice messages can treat `m.voice` as effectively unknown during rendering, likely falling on the `m.audio`
definition instead.

This proposal suggests that the textual fallback be "Voice message" for moderately sensical push/desktop/email
notifications. Note that MSC1767 supports internationalization, which clients should make use of as needed.

## Potential issues

The `m.voice` identifier could probably conflict, as `m.audio` could conflict as well. We may be interested in
discussing `m.message.voice` or similar instead, though likely at MSC1767 rather than this proposal.

This also annotates events with an empty object and potentially a lot of extra information. This is considered
to be an issue for MSC1767 to consider rather than this MSC, as this MSC is simply saying to create audio events
with some sort of voice message type.

## Alternatives

As mentioned, [MSC2516](https://github.com/matrix-org/matrix-doc/pull/2516) exists to make voice messages a
dedicated `msgtype`, which would work in the near term. There's additionally discussion on that MSC on whether
or not a flag within the event would be more appropriate than a `msgtype`. This proposal believes that both a
`msgtype` and flag within the `content` would accomplish the same thing as this MSC, however that the fallback
scenarios are less desirable. Flags in the `content` are subject to extensive proliferation if accepted, making
it harder to migrate to event formats like Extensible Events. Dedicated message types have the issue of not all
clients handling unknown message types the same way. Some clients would render it as a plain file upload while
many others would simply ignore the message entirely. This is not great representation for an audio message.
This proposal counters both problems by using Extensible Events out of the box, which results in clients being
able to render whatever they can, which will typically be either the voice message or an audio event, and fall
back accordingly to the not-great representations if they need to.

## Security considerations

Voice messages by nature are human voices being sent over the internet. This can be used for malicious purposes
outside the control of Matrix: users are cautioned to not send voice messages to untrusted places, such as large
public rooms or unknown individuals.

As with all media events, clients should be wary that the contained file is actually an audio file. Playing JPEGs
or executables over the user's speakers are unlikely to go down very well.

Voice messages are likely best used in encrypted rooms due to the high liklihood that the members of the room are
trusted, and the user's voice is not uploaded plainly to the media repo. Typically, this will be DMs or other
forms of private chats in most clients.

## Transitional event format

As mentioned on MSC1767, the Extensible Events format can be mixed in with the existing specification for message
events. For as long as MSC1767's transitional period is in place, the following would represent a voice message:

```json5
{
  "type": "m.room.message",  // Changed!
  "content": {
    "body": "Voice message",
    "msgtype": "m.audio", // To preserve semantic meaning
    "url": "mxc://example.org/abcdef",
    "info": {
      "duration": 6541,
      "mimetype": "audio/ogg",
      "size": 7992
    },

    // All of this is otherwise unchanged.
    "m.text": "Voice message",
    "m.file": {
      "size": 7992,
      "name": "Voice message.ogg",
      "url": "mxc://example.org/abcdef",
      "mimetype": "audio/ogg"
    },
    "m.audio": {
      "duration": 6541,
      "waveform": [0, 256, /*...*/ 1024]
    },

    // This can still be used to identify an audio message from a voice message,
    // even with the fallback of `msgtype: m.audio`
    "m.voice": {}
  },
  // other fields required by the spec, but not important here
}
```

## Unstable prefix

While this MSC is not considered stable implementations should use the following guidelines:

* Use MSC1767's unstable prefix and migration strategy where possible.
* Use `org.matrix.msc3245` in place of `m.voice`.
* Carefully send events which match the example given below. This is to make other implementations easier to
  write.

Example event (using all the unstable prefixing rules):

```json5
{
  "type": "m.room.message",
  "content": {
    "body": "Voice message",
    "msgtype": "m.audio",
    "url": "mxc://example.org/abcdef",
    "info": {
      "duration": 6541,
      "mimetype": "audio/ogg",
      "size": 7992
    },
    "org.matrix.msc1767.text": "Voice message",
    "org.matrix.msc1767.file": {
      "size": 7992,
      "name": "Voice message.ogg",
      "url": "mxc://example.org/abcdef",
      "mimetype": "audio/ogg"
    },
    "org.matrix.msc1767.audio": {
      "duration": 6541,
      "waveform": [0, 256, /*...*/ 1024]
    },

    // This can still be used to identify an audio message from a voice message,
    // even with the fallback of `msgtype: m.audio`
    "org.matrix.msc3245.voice": {}
  },
  // other fields required by the spec, but not important here
}
```

Client implementations should note that instead of `org.matrix.msc3245.voice` there are wild events using
`org.matrix.msc2516.voice` as a precursor experiment to this MSC. The MSC2516 namespace is not considered
correct, though clients may wish to handle it the same.

## Dependent MSCs

This MSC requires [MSC1767 - Extensible Events](https://github.com/matrix-org/matrix-doc/pull/1767) in order
to make the most sense in the specification.
