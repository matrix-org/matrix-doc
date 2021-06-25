# MSC2676: Message editing

Users may wish to edit previously sent messages, for example to correct typos.
This can be done by sending a new message with an indication that it replaces
the previously sent message.

This proposal is one in a series of proposals that defines a mechanism for
events to relate to each other.  Together, these proposals replace
[MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849).

* [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) defines a
  standard shape for indicating events which relate to other events.
* [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines APIs to
  let the server calculate the aggregations on behalf of the client, and so
  bundle the related events with the original event where appropriate.
* This proposal defines how users can edit messages using this mechanism.
* [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) defines how
  users can annotate events, such as reacting to events with emoji, using this
  mechanism.

## Proposal

A new `rel_type` of `m.replace` is defined for use with the `m.relates_to`
field as defined in
[MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674).  This is
intended primarily for handling edits, and lets you define an event which
replaces an existing event.  When aggregated (as in
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)), returns the
most recent replacement event (as determined by `origin_server_ts`). The
replacement event must contain an `m.new_content` which defines the replacement
content (allowing the normal `body` fields to be used for a fallback for
clients who do not understand replacement events).

For instance, an `m.room.message` which replaces an existing event looks like:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "s/foo/bar/",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello! My name is bar",
            "msgtype": "m.text"
        },
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id"
        }
    }
}
```

The `m.new_content` includes any fields that would normally be found in an
event's `content` field, such as `formatted_body`.  In addition, the `msgtype`
field need not be the same as in the original event.  For example, if a user
intended to send a message beginning with "/me", but their client sends an
`m.emote` event instead, they could edit the message to send be an `m.text`
event as they had originally intended.

Permalinks to edited events should capture the event ID that the sender is
viewing at that point (which might be an edit ID).  The client viewing the
permalink should resolve this ID to the source event ID, and then display the
most recent version of that event.

### Redactions

When a message using a `rel_type` of `m.replace` is redacted, it removes that
edit revision.

In the UI, the act of redacting an edited message in the timeline should
remove the message entirely from the timeline.  It can do this by redacting the
original msg, while ensuring that clients locally discard any edits to a
redacted message on receiving a redaction.

When a specific revision of an event is redacted, the client should manually
refresh the parent event via `/events` to grab whatever the replacement
revision is.

## Edge Cases

How do you handle racing edits?
 * The edits could form a DAG of relations for robustness.
    * Tie-break between forward DAG extremities based on origin_ts
    * this should be different from the target event_id in the relations, to
      make it easier to know what is being replaced.
    * hard to see who is responsible for linearising the DAG when receiving.
      Nasty for the client to do it, but the server would have to buffer,
      meaning relations could get stuck if an event in the DAG is unavailable.
 * ...or do we just always order by on origin_ts, and rely on a social problem
   for it not to be abused?
    * problem is that other relation types might well need a more robust way of
      ordering. XXX: can we think of any?
    * could add the DAG in later if it's really needed?
    * the abuse vector is for a malicious moderator to edit a message with origin_ts
      of MAX_INT. the mitigation is to redact such malicious messages, although this
      does mean the original message ends up being vandalised... :/
 * Conclusion: let's do it for origin_ts as a first cut, but use event shapes which
   could be switched to DAG in future is/as needed.  Good news is that it only
   affects the server implementation; the clients can trust the server to linearise
   correctly.

What can we edit?
 * Only non-state events for now.
 * We can't change event types, or anything else which is in an E2E payload
 * We can't change relation types either.

How do diffs work on edits if you are missing intermediary edits?
 * We just have to ensure that the UI for visualising diffs makes it clear
   that diffs could span multiple edits rather than strictly be per-edit-event.

What happens when we edit a reply?
 * We just send an m.replace which refers to the m.reference target; nothing
   special is needed.  i.e. you cannot change who the event is replying to.
 * The edited reply should ditch the fallback representation of the reply itself
   however from `m.new_content` (specifically the `<mx-reply>` tag in the
   HTML, and the chevron prefixed text in the plaintext which we don't know
   whether to parse as we don't know whether this is a reply or not), as we
   can assume that any client which can handle edits can also display replies
   natively.

   XXX: make Element do this

What power level do you need to be able to edit other people's messages, and how
does it fit in with fedeation event auth rules?
 * 50, by default?

    XXX: Synapse doesn't impose this currently - it lets anyone send an edit,
    but then filters them out of bundled data.

"Editing other people's messages is evil; we shouldn't allow it"
 * Sorry, we have to bridge with systems which support cross-user edits.
 * When it happens, we should make it super clear in the timeline that a message
   was edited by a specific user.
 * We do not recommend that native Matrix clients expose this as a feature.

## Future considerations

In future we may wish to consider ordering replacements (or relations in
general) via a DAG rather than using `origin_server_ts` to determine ordering -
particularly to mitigate potential abuse of edits applied by moderators.
Whatever, care must be taken by the server to ensure that if there are multiple
replacement events, the server must consistently choose the same one as all
other servers.
