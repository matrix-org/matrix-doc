# Add a default push rule to ignore m.reaction events

Reactions are considered "metadata" that annotates an existing event and thus
they should not by default trigger notifications. (See
[MSC1849](https://github.com/matrix-org/matrix-doc/blob/matthew/msc1849/proposals/1849-aggregations.md#event-format)
for the reaction event format.)

This is especially important for rooms that may be set with a room-specific rule
to notify, as they will trigger notifications for every reaction and it's tricky
to clear them as well. See https://github.com/vector-im/riot-web/issues/10208
for details.

## Proposal

A new default override rule is to be added that ignores reaction events:

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

## Tradeoffs

We could instead allow notifications for reactions in some cases (the current
state) but then modify each client with complex heuristics to clear them by
advancing the read receipt. This would be more involved than for regular messages
because reaction events may target any event in the timeline, so there's no
guarantee that a new reaction event targets something that's currently displayed
to the user. By going with the push rule above, client developers won't have to
deal with this issue.
