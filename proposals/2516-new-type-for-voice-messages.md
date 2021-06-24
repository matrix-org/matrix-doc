# Add a separate message type for voice messages

In the matrix spec right now, there is a message type `m.audio` for audio files.
In other messaging apps, there is also a special type for voice memos,
since they carry a different meaning and inflict different behaviour.
This MSC calls for the introduction of an `m.voice` message type.

Even if it's not the primary mode of communication for nerds,
voice memos are very important to a lot of users of modern instant messaging services.
In order to provide awesome voice messages, they need to be treated differently from generic audio files.

For example, WhatsApp renders them differently, to highlight that they are a way of communication.
WhatsApp also always force-downloads them, because like a text message,
they should be available to consume as early as possible.
This lets the recipient know at a glance that they are being expected
to listen to the voice messages now, instead of later.

The presentation of voice messages should reinforce the authenticity
and potential urgency of the audio content.

## Proposal

I propose to introduce a new message type `m.voice` with the same
contents as `m.audio`.
Voice messages MUST be OGG files, Opus encoded. Other files can be 
sent as `m.audio`or `m.file`.

### Related links:
- [A long-standing issue on Riot Web that calls for voice messages
](https://github.com/vector-im/riot-web/issues/1358)
- [An earlier proposal to send m.typing-like status codes when recording
](https://github.com/matrix-org/matrix-doc/pull/310)
- [Telegram API for voice messages
](https://core.telegram.org/bots/api#sendvoice)

## Potential issues

Introducing a new message type means that client developers will have to
do work to implement it, or their users won't be able to use the feature.

## Alternatives

Alternatively, a flag `voice = true` or `type = "voice"` could be created inside of the `m.audio` event.
I'm not sure what the more canonical way of doing things would be here.

This alternative version (extending the m.audio message type) has the benefit
that it comes with backwards compatibility for free. However, we should keep
types as simple as possible.

There is also #1767 (display hints) which tackles the same issue more generally,
but it is not ready, and voice messages should come first.

## Security considerations

@uhoreg offers:
> Auto-downloading of files (if clients follow WhatsApp's example) sounds
like it could be a security issue. (e.g. DoS by using up users' bandwidth,
could cause malicious content to be automatically downloaded)

This could be solved by having clients handle auto-download responsibly,
e.g. only auto-download voice messages from trusted contacts.

## Unstable prefix

While this MSC is not considered a stable part of the specification,
implementations should use `org.matrix.msc2516.voice` in place of `m.voice`.
