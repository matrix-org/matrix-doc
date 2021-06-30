# MSC3052: Sample events

Sample events are intended as a generic representation of timing-sensitive and replayable exchange
of sample data. 

## Proposal

The sample event format is very simple. It consists of a JSON block with a sample metadata and data.

JSON part is formatted as follows:

```json
{
    "type": "m.samples",
    "content": {
        "sample.type": "audio/pcm",
        "sample.rate": 44100,
        "sample.duration" : 123.4567, 
        "sample.length" : undefined,
        "sample.width" : undefined,
        "sample.depth" : undefined,
        "sample.encoding" : "encoding",
        "sample.diachronic": true,
        "sample.synchronic": true,
        "samples" : "whatever_samples"
    }
}
```

`sample.type` is a MIME type, `sample.rate` is the sample rate in Hertz, `sample.duration` is
the duration of this sample event in seconds, `sample.length`, `sample.width` and `sample.depth`
are integers for positional data if exists. 

### Representation of samples within the event body

For JSON format, JSON-encoded (`string`) and URL-safe unpadded base64 (`base64`) should be
supported as a minimum. Base85 and other encodings may also be optionally supported.
For future binary formats such as CBOR as mentioned in MSC3079, it is preferred to have
a binary encoding that will allow the samples placed raw in the event body.

### Playback behaviour and restrictions

There are two parametres (`sample.diachronic` and `sample.synchronic`) that control playback
behaviour, named after the aspects they control (diachronic coupling, and synchronic coupling
of playback across multiple sample events):

`sample.diachronic`: Unless false, the clients encounter multiple sample events from others,
they shall align all the samples by timestamp and add the required amount of additional latency
required to keep the latency invariant true. The latency build-up and drop should be as gradual
as possible. Clients MUST NOT rescale or resample any of the sample events to compensate
for latency. Playing a combination of sample events of same type from different senders
with different sample rates is ill-formed, while combination of multiple sample events
of different type with different sample rates is implementation defined. Exact alignment algorithm
is implementation defined except for the constraints described above.

`sample.synchronic` : Unless false, the clients shall forbid synchronic scaling
of sample streams when multiple streams are multiplexed together (e.g., it is forbidden to
allow users to volume down a particular stream and keep other streams at full volume).

The default behaviour is designed to allow sample events to be used in any use case where
both high fidelity playback and reproducible persistence are required. Example use cases
include court-admissible recordings over distributed networks, internet of things with history-
admissible trail, interplanetary teleconferencing.

## Potential issues

Mistimed sample events can cause a client to hang forever by locking out on that specific sample event.

## Alternatives

* Have signalling on Matrix and actual data separately, which unfortunately means the samples
and the metadata possibly having different latency.

* Have sample events with `m.samples` as a subtype of `m.room.message` rather than an event type
of its own right (After all, sample events will just be message events with special client handling).
This would be essentially equivalent, minus the ability to moderate sample events.

* Have sample events as a type of [MSC1767 extensible events](https://github.com/matrix.org/matrix-doc/pull/1767).
Same issue as sample events as message subtypes.

## Security considerations

Ability to hijack sample streams to livelock by deliberately mis-timing sample events.

## Future ideas

* Special moderation semantics for sample events
* Minimum interoperability requirements for sample events that are desired to work in all clients

## Unstable prefix

Not implemented yet.
