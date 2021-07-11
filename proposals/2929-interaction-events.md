# MSC2929: Interaction events

Interaction events are intended to create a standardised way for bots or other third party applications
to interact with other users. IRC, Telegram, Discord solve this using slash commands in the user side.

## Proposal

There are many possibilble subtypes of interaction events that could be used, under `m.room.interaction`
umbrella type. Precise subtypes and response flows are left implementation defined in the client side.
Servers are not expected to aggregate multiple interaction events into a single interaction event.

There are three basic fields, however, implementations are allowed to arbitrarily add more fields:
* itype, modelled after msgtype of `m.room.message`, but exact types are implementation defined
* body, where the request body would be contained
* target, the expected responding user

An interaction initiation example:
```
{
  "type": "m.room.interaction",
  "content": {
    "itype": "m.command",
    "body": "help",
    "target": "@example:example.com"
  },
  "sender": "@matrix:matrix.org"
}
```

Although the example contains a text command, a menu or some other means of sending interactions
are also allowed.

Interactions are allowed to be registered for push notifications to allow for lightweight
interaction listeners. In that case, the registration follows a flow quite similar to room events
notification flow, with differences outlined below:

* Empty room target means interaction registrand wants to listen to interaction events targeting
that user from ALL rooms from the homeserver that the registrand is from.
* It is allowed to register for a specific subtype of interaction, just like for a specific
subtype of a message.
* Interactions registered to registrand's profile room means that interaction is allowed to be
initiated from anywhere.
* Interactions registered to rooms of rooms, such as extensible profiles or spaces, means
all rooms pointed by room pointers in such rooms are also covered for notification.
* Interactions registered with this flow should not push whole room state when triggered.

It is ill-formed to register for a push notification of any interaction in a room that has
end-to-end encryption enabled.

Redacting an interaction event shall not undo the effect caused by event that has been redacted.
This is intentional as interactions are allowed to create irreversible side effects outside Matrix.
Interactions should be responded by `target` users if and only if they understand the interaction
body. Response target is left implementation defined, however, here are the recommendations of
the author of the proposal:

* For global commands and similar, use the extensible profile room of the responder as target.
* For interactions that act on the room state, use the said room as target.
* For interactions that act on a particular user, use a 1:1 room with said room as target.

Presentation of interactions to users are left implementation defined.

## Potential issues

Interaction notifications with E2EE is deliberately disallowed.

## Alternatives

* Just using `m.room.message` type of text messages: Some clients choke when additional fields
* Having each bot create own event type for interactions: Which is entirely possible given
the extensible nature of Matrix, however, this will constrain the support of such events to
those particular clients.

## Security considerations

No issues foreseen.

## Unstable prefix

No implementations yet.
