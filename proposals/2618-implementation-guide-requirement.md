# MSC2618: Helping others with mandatory implementation guides

Thus far the spec has been a mix of implementation guide and documenting nuances with the individual
components of Matrix, which leads to confusion, lack of clarity, and excess information for typical
audiences.

To help fix this, the spec core team is separating the implementation notes from the spec to allow
the spec to document more precisely what the components do and to relieve the strain of understanding
from spec implementations.

## Proposal

The spec shall adopt a guide system which takes the shape of one or more "books" to document various
implementation details. The kind of information presented through this system is intended to have a
target audience of implementation authors (servers, clients, etc) who do not typically need to reference
the formal, nuanced, spec.

The tech used to publish these guides is not defined by this MSC as experimentation from the spec
core team is expected. The tech may be changed to better suit the intended audience.

Pre-existing spec components are to have their notes added/moved to the new guide format as appropriate.

Typically one or few people are responsible for converting MSCs into final spec to maintain voice
(and because the tooling is non-trivial to figure out), however there is currently no formal requirement
that it be any particular person, just that an MSC eventually goes to the spec. It is proposed that
the same person who writes the spec PR for an MSC be responsible for ensuring a guide is written prior
to the appropriate spec release. This isn't to say they have to write it (though they probably will),
just that they have a plan to ensure a guide is produced before the spec is released.

To assist with keeping the guides up to date with new MSCs/features, MSCs prior to landing in the
spec MUST document implementation considerations. This is not a requirement for FCP, however it is
expected that many of the considerations will be recorded prior to FCP due to the nature of requiring
an implementation before an MSC can enter FCP. The considerations shall be documented in the MSC's
proposal document and not on the GitHub PR so they can be retained in version control.

The considerations documented do not have to be a guide themselves, however there should be enough
detail to infer a guide from the notes. The following list format may work for many MSCs as an
example:

* The client should keep hitting `/sync` without delay, unless the server returns an error.
* When processing the sync response, clients should be aware that events do *not* have a `room_id` -
  the room ID is instead part of the response structure.
* The presence interactions take priority over other calls. See the presence guide for more information.
* Devices can receive messages, usually for encryption, which are received through sync. Once the
  server sends a device message, it will not be re-sent.
* Shorter timeouts are not recommended, though longer ones can be difficult to maintain due to network
  interruptions. Clients are recommended to use the default where possible.

Please note the example is incomplete and is only meant to be a demonstration of various ways to word
the considerations clients should make. A guide for this feature would likely take the points and
convert them to paragraphs, potentially merged into relevant guides rather than having a sync-specific
guide. For example, the "handling message events" guide might mention the `room_id` behaviour whereas
the e2ee guide mentions the `to_device` messages.

MSCs which are self-documenting, such as the small/tiny maintenance ones, or which do not affect the
spec featureset, like this one, do not need to have implementation considerations documented. However,
it would be greatly appreciated if the redundancy was present for the sake of clarity.

It is also proposed that a new "Implementation considerations" section be added to the proposal template.

## Potential issues

We could end up with two sources of truth, and neither being particularly good. If this happens, we
should fix that.

Existing MSCs will be missing all of this detail. Authors of those MSCs should make an attempt to
"upgrade" to this new process where possible.

## Alternatives

We sit in sadness for lack of documentation, leading to frustrated developers and abandoned implementations.

## Security considerations

We could receive spam or malicious contributions to our guides. Standard oversight by the spec core team
is expected to ensure the quality of the guides is held to an appropriate level.

## Implementation considerations

Anyone who plans on implementing an MSC should be prepared to document their issues for other implementations
to consider. This may add time to the development of a feature, however the greater ecosystem will benefit
more from the issues being recorded. Likewise, MSC authors should be made aware when their MSC is being
implemented and be prepared to document any common questions they receive as considerations.

## Unstable prefix

This is a spec process proposal, therefore no unstable prefix is required. MSCs are encouraged to use
this new process even before it lands in the official process as it should greatly increase understanding
and clarity for an MSC.
