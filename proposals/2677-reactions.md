# MSC2677: Annotations and Reactions

Users sometimes wish to respond to a message using emojis.  When such responses
are grouped visually below the message being reacted to, this provides a
(visually) light-weight way for users to react to messages.

This proposal is one in a series of proposals that defines a mechanism for
events to relate to each other.  Together, these proposals replace
[MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849).

* [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) defines a
  standard shape for indicating events which relate to other events.
* [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines APIs to
  let the server calculate the aggregations on behalf of the client, and so
  bundle the related events with the original event where appropriate.
* [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676) defines how
  users can edit messages using this mechanism.
* This proposal defines how users can annotate events, such as reacting to
  events with emoji, using this mechanism.

## Proposal

A new `rel_type` of `m.annotation` is defined for use with the `m.relates_to`
field as defined in
[MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674).  This `rel_type`
is intended primarily for handling emoji reactions, these lets you define an
event which annotates an existing event.  The annotations are typically
presented alongside the event in the timeline.  When used, the `m.relates_to`
field also contains a `key` that indicates the annotation being applied.  For
example, when reacting with emojis, the `key` contains the emoji being used.
When aggregated (as in
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)), it groups
events together based on their `key` and returns a `count`.  Another
usage of an annotation is e.g. for bots, who could use annotations to report
the success/failure or progress of a command.

The `type` of the annotating event is not taken into account when aggregating
as that would prevent accurate server aggregation in end-to-end encrypted rooms.

Given this, annotations of any event type should be accepted as a valid reaction,
but a new message type `m.reaction` is suggested to indicate that a user is reacting
to a message.

For example, an `m.reaction` event which annotates an existing event with a 👍
looks like:

```json
{
    "type": "m.reaction",
    "content": {
        "m.relates_to": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    }
}
```

When sending emoji reactions, the `key` field should include the colourful
variation-16 when applicable.

### Push rules

Since reactions are considered "metadata" that annotate an existing event, they
should not by default trigger notifications.  Thus a new default override rule
is to be added that ignores reaction events:

```json
{
    "rule_id": ".m.rule.reaction",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.reaction"
        }
    ],
    "actions": [
        "dont_notify"
    ]
}
```

### Server support

When an annotation event is sent to clients via `/sync`, a new field
`annotation_count` is provided in the `unsigned` field of the event, calculated
by the server to provide the current absolute count of the given annotation key
as of that point of the event, to avoid the client having to accurately track
the absolute value itself.

  XXX: is this implemented in Synapse yet?

For instance, an incremental sync might include the following:

```json
{
    "type": "m.reaction",
    "sender": "@matthew:matrix.org",
    "content": {
        "m.relates_to": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    },
    "unsigned": {
        "annotation_count": 1234,
    }
}
```

...to indicate that Matthew just thumbsupped a given event, bringing the current
total to 1234 thumbsups.

#### Bundled relations

When annotations are bundled according to the [Bundled relations section of
MSC2675](https://github.com/uhoreg/matrix-doc/blob/aggregations-helpers/proposals/2675-aggregations-server.md#bundled-relations),
the aggregated value in the bundle provides the `type` of the relation event,
the aggregation `key`, the `origin_server_ts` of the first reaction to that
event, and the `count` of the number of annotations of that `type` and `key`
which reference that event.

For instance, the below example shows an event with five bundled relations:
three thumbsup reaction annotations, and two thumbsdown reaction annotations.

```json
{
    ...,
    "unsigned": {
        "m.relations": {
            "m.annotation": {
                "chunk": [
                  {
                      "key": "👍",
                      "origin_server_ts": 1562763768320,
                      "count": 3
                  },
                  {
                      "key": "👎",
                      "origin_server_ts": 1562763768320,
                      "count": 2
                  }
                ],
                "limited": false,
                "count": 2
            }
        }
    }
}
```

  XXX: is the example correct?

### Redactions

When a message using a `rel_type` of `m.annotation` is redacted, this removes
the annotation from the message.

## Edge Cases

How do you stop people reacting more than once with the same key?
 1. You error with 400 (M_INVALID_REL_TYPE) if they try to react twice with the same key, locally
 2. You flatten duplicate reactions received over federation from the same user
    when calculating your local aggregations
 3. You don't pass duplicate reactions received over federation to your local user.
 4. XXX: does synapse do 2 & 3 yet?

Can you [edit](https://github.com/matrix-org-matrix-doc/pull/2676) a reaction?
 * It feels reasonable to say "if you want to edit a reaction, redact it and resend".
   `rel_type` is immutable, much like `type`.

Can you react to a reaction?
 * Yes, at the protocol level.  But you shouldn't expect clients to do anything
   useful with it.

What happens when you react to an edit?
 * You should be able to, but the reaction should be attributed to the edit (or
   its contents) rather than the message as a whole.
 * Edits gather their own reactions, and the clients should display
   the reactions on the most recent edit.
   * This provides a social pressure to get your edits in quickly before there
     are many reactions, otherwise the reactions will get lost.
   * And it avoids us randomly aggregating reactions to potentially very
     different contents of messages.

Which message types are reactable?
 * Any. But perhaps we should provide some UI best practice guidelines:
  * `m.room.message` must be reactable
  * `m.sticker` too
  * ...but anything else may not be rendered.

## Alternatives

### Extended annotation use case

In future it might be useful to be able to annotate events with more
information, some examples include:

  * Annotate commit/PR notification messages with their associated CI state, e.g.
    pending/passed/failed.
  * If a user issues a command to a bot, e.g. `!deploy-site` the bot could
    annotate that event with current state, like "acknowledged",
    "redeploying...", "success", "failed", etc.
  * Other use cases...?

However, this doesn't really work with the proposed grouping, as the aggregation
key wouldn't contain the right information needed to display it (unlike for
reactions).

One way to potentially support this is to include the events (or a subset of the
event) when grouping, so that clients have enough information to render them.
However this dramatically inceases the size of the parent event if we bundle the
full events inside, even if limit the number we bundle in. To reduce the
overhead the annotation event could include a `m.result` field which gets
included.

This would look something like the following, where the annotation is:

```json
{
  "type": "m.bot_command_response",
  "content": {
    "m.result": {
      "state": "success",
    },
    "m.relates_to": {
      "type": "m.annotation",
      "key": ""
    }
  }
}
```

and gets bundled into an event like:

```json
{
  "unsigned": {
    "m.relations": {
      "m.annotation": [
        {
          "type": "m.bot_command_response",
          "key": "",
          "count": 1,
          "chunk": [
            {
              "m.result": {
                "state": "success",
              },
            }
          ],
          "limited": false,
        }
      ]
    }
  }
}
```

This is something that could be added later on. A few issues with this are:

  * How does this work with E2EE? How do we encrypt the `m.result`?
  * We would end up including old annotations that had been superceded, should
    these be done via edits instead?

## Security considerations

Clients should render reactions that have a long `key` field in a sensible
manner. For example, clients can elide overly-long reactions.

If using reactions for upvoting/downvoting purposes we would almost certainly want to anonymise the
reactor, at least from other users if not server admins, to avoid retribution problems.
This gives an unfair advantage to people who run their own servers however and
can cheat and deanonymise (and publish) reactor details.  In practice, reactions may
not be best used for upvote/downvote as at the unbundled level they are intrinsically
private data.

Or in a MSC1228 world... we could let users join the room under an anonymous
persona from a big public server in order to vote?  However, such anonymous personae
would lack any reputation data.
