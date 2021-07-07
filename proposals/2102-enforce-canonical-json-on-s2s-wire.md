# MSC2102 - Enforce Canonical JSON on the wire for the S2S API

## Background

Currently the S2S API uses plain JSON as a data format on the wire, considering
that we already need to convert to Canonical JSON for signing, it would make
for an overall improvement if we simply enforced Canonical JSON on the wire at
all times.

## Benefits

* It makes implementation of a zero-copy Matrix homeserver easier. This way we
can receive, process and store the data from the wire without mutating it.
Avoiding copies makes better use of the CPU cache.

* It makes for smaller data on the wire, Canonical JSON would
use less network bandwidth to transfer.

## Potential issues

* Encoding into Canonical JSON means that we must sort the keys, this can result
in a performance hit if the software is not designed to provide keys pre-sorted
to the Canonical JSON encoder. However, the impact of this can be made null if
software is designed with that aspect in mind.

## Conclusion

While we should transition to a different transport such as Flatbuffers,
Protobuf or CBOR in the future, using Canonical JSON in the mean time would
improve the situation significantly with minimal engineering time.
Using a canonical form for any other wire data format also yields the same
benefits, a similar strategy even when using CBOR is also to be considered.
Flatbuffers already adopt this canonical form strategy as an optimization.
