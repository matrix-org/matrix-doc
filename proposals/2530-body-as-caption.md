# Body field as media caption

This is an alternative to [MSC2529](https://github.com/matrix-org/matrix-doc/pull/2529).

## Proposal

This proposal defines a new field `filename` and allows the `format` and
`formatted_body` fields (from `m.text`) for all media msgtypes (`m.image`,
`m.audio`, `m.video`, `m.file`).

If the `filename` field is present in a media message, clients should treat
`body` as a caption instead of a file name. The `formatted_body` field should
also be supported and work the same way as they do in `m.text` messages.

The current spec is inconsistent with how `body` should be handled, but in
practice, clients (or at least Riot) use it as the file name. Therefore, this
proposal suggests that clients should treat `body` as the file name if the
`filename` field is not present.

## Comparison to MSC2529

While this approach isn't backwards-compatible like MSC2529, it's simpler to
implement as it doesn't require handling relations.

Implementing relation-based captions would be especially difficult for bridges.
It would require either waiting a predefined amount of time for the caption to
come through, or editing the message on the target platform (if edits are
supported).

Additionally, some clients already render the body (as a file name), so the
new-style caption would already be visible in those cases.

The format proposed by MSC2529 would also make it technically possible to use
other message types without changing the format of the events, which is not
possible with this proposal.

## Potential issues

The spec for `m.file` already defines a `filename` field, but the spec also
says `body` should contain the file name. This means old `m.file` messages
could be misinterpreted to contain a caption, even though it's just the file
name. To avoid this problem, we could require that `body` and `filename` must
be different for `body` to be interpreted as a caption.

Like MSC2529, this would be obsoleted by [extensible events](https://github.com/matrix-org/matrix-doc/pull/1767).
In my opinion, unless extensible events are planned to be pushed through in the
near future, we shouldn't block basic features like captions on extensible
events hopefully eventually happening.
