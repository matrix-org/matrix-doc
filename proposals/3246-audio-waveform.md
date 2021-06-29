# MSC3246: Audio waveforms (extensible events)

This is largely a placeholder MSC to describe how audio waveforms/events could work in an extensible
events world.

Proposals like [MSC3245 - Voice messages using extensible events](https://github.com/matrix-org/matrix-doc/pull/3245)
would make best use of this.

## Proposal

A `waveform` property is added to the `m.audio` event definition as an array of numbers to denote
amplitudes for the audio file. The array should have no less than 30 elements and no more than 120.
Clients might have to resample for their use case, and are encouraged to only use the information
as placeholder until the real waveform can be determined.

Due to floats not being allowed in events, the waveform should be rescaled to a range of integers
between zero and 1024, inclusive. This should allow for enough resolution to be maintained for
preview purposes. Values larger/smaller than those should be clamped.

The waveform is optional.

## Potential issues

TBD

## Alternatives

TBD

## Security considerations

TBD

## Unstable prefix

TBD (not currently needed)
