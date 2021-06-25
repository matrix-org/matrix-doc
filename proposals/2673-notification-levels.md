# MSC2673: Notification Levels

## Problem

The current push rules system is complicated (there are many different layers
and it's hard to add new rules, because other rules might already match and
early-return. It also doesn't allow device-dependent changes, so when you want
notifications sounds for one room on your laptop, your phone will play sounds
as well (unless if you count turning off notification sounds altogether, which
is not always wanted)


## Proposal

For each message a homeserver receives, it calculates the notification level
for each user that should receive that message. The level is a number between
0-10. 0 means low importance, 10 means high importance. If the level is above
0, it is pushed to the user's devices. Each device then maps the level to the
actions that should happen. One set of these mappings is called a "notification
profile". The user's account data always contains one profile called "default",
but it's also possible to create new profiles for different devices (one
profile can be used by multiple devices), for example "mobile".

The default contents of the "default" profile look like this:
- 0: No actions
- 2: Increase notification count
- 4: Show notification
- 6: Play notification sound
- 8: Highlight message

If a message with a notification level of 6 arrives, the device with this
profile should show the notification and play a sound (increasing the
notification count is handled on the server).


### How does the server figure out notification levels?

Similar to push_rules, there's a notification_rules event. It's a list of
`NotificationRule`s. Each NotificationRule object can be one of X kinds:

- Room: Manipulate notification level based if the room_id of the message
  matches
- Sender: Manipulate notification level based if the user_id of the sender
  matches
- Content: Manipulate notification level based if a substring of the content
  matches
- DisplayName: Manipulate notification level based if the content contains the
  user's displayname

Each of these kinds contains the fields it needs for matching in addition to
`up_to`, `max` and `rule_id`. `up_to` specifies the highest power level this
rule can trigger and `max` sets a limit on the notification level the message
ends up with, if the rule is triggered.

The server can figure out what notification level a message has, by looking at
all triggered rules and finding the highest `up_to` value and then subtracting,
so that the notification level is not above a `max` of a triggered rule.


## Problems

- Custom notification sounds, color or other options. Maybe this can be solved
  by additional fields in the NotificationRule objects, where the higher
  `up_to` means higher priority.

- Same problems as with power levels. It's impossible to take away actions as
  the notification level increases, so highlighting messages will always make
  them increase the notification count and play a sound for example.
