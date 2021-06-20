# MSC2772: Notifications for Jitsi Calls

Matrix supports conference calls in rooms througth the use of Jitsi widgets. A user receives
notifications when they receive a 1:1 VoIP call, but currently there are no notifications for
any widget being added to a room, including Jitsi widgets, so user are not notified when a
conference call starts.

## Proposal

This proposal adds the following predefined rules to the default underride rules:
```
{
    "rule_id": ".m.jitsi",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.widget",
        },
        {
            "kind": "event_match",
            "key": "content.type",
            "pattern": "m.jitsi",
        },
        {
            "kind": "event_match",
            "key": "state_key",
            "pattern": "*",
        },
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "highlight",
            "value": False,
        },
    ],
},
{
    "rule_id": ".m.jitsi_legacy1",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "im.vector.modular.widgets",
        },
        {
            "kind": "event_match",
            "key": "content.type",
            "pattern": "jitsi",
        },
        {
            "kind": "event_match",
            "key": "state_key",
            "pattern": "*",
        },
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "highlight",
            "value": False,
        },
    ],
},
{
    "rule_id": ".m.jitsi_legacy2",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "im.vector.modular.widgets",
        },
        {
            "kind": "event_match",
            "key": "content.type",
            "pattern": "m.jitsi",
        },
        {
            "kind": "event_match",
            "key": "state_key",
            "pattern": "*",
        },
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "highlight",
            "value": False,
        },
    ],
}
```

The three rules are necessary to cover the three possibilities of `type` and `state_key`: `jitsi`
vs `m.jitsi` and `im.vector.modular.widgets` vs `m.widget`. Clients should provide present all three
of these rules as single rule to the user and apply the same mdifications to each one of these rule
IDs (if a rule with that ID was sent by the server).

A future revision to the specification may remove the legacy rules.

## Potential issues

Having to have three separate rules is nonideal, but a limitation of the current push specification.

## Alternatives

Extensions could be defined to cause conference calls to 'ring' rather than trigger a standard
notification, or the actions could be defined to trigger an audible alert. More advanced conditions
could also be defined, for example, varying levels of notification depending on the number of
participants in the room.

## Security considerations

Implementors must ensure to implement the condition checking for a state event, else there would be
potential for this to be triggered by user without permission to send state events.

## Unstable prefix
In the unstable stage, the IDs for these rules are:
 * `.im.vector.jitsi`
 * `.im.vector.jitsi_legacy1`
 * `.im.vector.jitsi_legacy2`

Any client implementing support for these rules in the unstable phase should treat the stable and unstable
identifiers of each rule as the same rule.
