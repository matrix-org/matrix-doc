# MSC2589: Improving replies

Currently replies in the spec require clients to parse HTML and/or plain text in order to accurately
represent the event. This fallback also introduces a number of limitations preventing clients from
typically being able to reply to non-text events, such as state events or images.

This proposal alters the requirements for replies such that they can be expanded to cover any event
type, and be easier for clients to render.

For context, the current spec is extensively documented here: https://matrix.org/docs/spec/client_server/r0.6.1#rich-replies

This fixes https://github.com/matrix-org/matrix-doc/issues/1541 and would technically address
https://github.com/matrix-org/matrix-doc/issues/1661 as well due to not defining a strict format.

## Proposal

Firstly, building off the concepts of [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849)
the relationship between events in the context of replies changes to be:

```json
{
  "m.relationship": {
    "rel_type": "m.reference",
    "event_id": "$example"
  }
}
```

The fallback for replies is simply replaced by a best effort clause: clients SHOULD do their
best to provide context of what happened in the `body` and `formatted_body` for clients which
do not support replies. This could take the form of a simple blockquote, similar to quoting a
message.

Instead of having to parse the fallback to get the reply, clients MUST send a `reply_body`
(and optionally a `reply_formatted_body`) in the event content to represent what the user is
replying with.

In an example, if someone were to send a message like "Version 1.1.0 is out!" and another were
to reply to it, the reply's content would look like this:

```json
{
  "body": "> Version 1.1.0 is out!\n\nAwesome, thanks for the hard work!",
  "format": "org.matrix.custom.html",
  "formatted_body":"<blockquote>Version 1.1.0 is out!</blockquote><p>Awesome, thanks for the hard work!</p>",
  "reply_body": "Awesome, thanks for the hard work!",
  "reply_fomatted_body": "<p>Awesome, thanks for the hard work!</p>",
  "m.relationship": {
    "rel_type": "m.reference",
    "event_id": "$example"
  }
}
```

The `format` field describes the `reply_formatted_body` format. The requirement for replies to
be HTML-formatted is also dropped: a plain text reply (no `format`) is completely acceptable.

## Potential issues

Events will be larger as a result, though typical messaging scenarios hardly get anywhere near the
event size limit.

There is also an opportunity for the fallback and the `reply_*` fields to desync, though this is
largely believed to be a client bug rather than a fault of the spec.

Some events, like images, cannot be represented easily as text. Clients could show something like
"> regarding Bob's image: release-timeline.png" instead.

## Alternatives

We could ditch the idea of a fallback entirely, leaving clients which don't support the feature
in the dust. This is a viable option for a number of use cases (as the reply and the event are
typically within moments of each other), however many replies that existing users make are done
so with no referencing context. For example, "does anyone know how to fix this?" means nothing if
the original event's context isn't presented. This is largely an issue for bridges and other simple
clients, though many projects which realize the reply fallback is not perfect tend to take action
to support replies properly.

## Security considerations

https://github.com/matrix-org/matrix-doc/issues/1654 is still not fixed as part of this.

## Unstable prefix

Clients should use `org.matrix.msc2589` in place of `m.*` within this MSC. For example,
`m.relationship` becomes `org.matrix.msc2589.relationship` while this MSC has not been included in
a spec release.
