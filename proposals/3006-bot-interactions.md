# MSC3006: Bot Interactions

Bots are currently only possible in IRC style. They are entirely text based and not interactive like, for example, Telegram bots.
This is trying to solve that issue by using a similar backwards compatible way like the one in Telegram.

This is highly inspired by https://core.telegram.org/bots#keyboards and is trying to allow similar types 
of keyboards for bots to allow more "fancy" bots while keeping full backwards compatibility.

## Proposal

The proposal is to have multiple interaction events. Which tell the client what kind of interactions the 
bot has and the client replies with a specific format on that.

_Note: a deeper explanation of the events will be below the interaction flow_

### Interaction Flow

1. The bot joins a room and sends a state event containing information about possible interactions:

```json
{
  "type": "m.bot.interactions",
  "state_key": "@faq_bot:example.matrix",
  "content": {
    "command_prefix": "!",
    "interactions": [
      {
        "type": "m.interaction.command",
        "description": "Shows the help of the FAQ Bot",
        "name": "help"
      },
      {
        "type": "m.interaction.button",
        "description": "Search question",
        "name": "Search"
      }
    ]
  }
}
```

2. The clients shows a button to open the commands list and/or a button to open the custom keyboard

3. The user clicks on for example the help command one.

4. The client sends an event of type `m.room.message` and msgtype `m.text`. This allows us to have fallback for free while 
having typed commands when client and bot support it.

```json
{
  "content": {
    "body": "!help",
    "msgtype": "m.text",
    "m.interaction.command": {
      "command": "help",
      "target": "@faq_bot:example.matrix"
    }
  },
  "type": "m.room.message"
}
```

5. The Bot responds with a request for the client to display a separate custom keyboard for the next stage of 
this command

```json
{
  "content": {
    "event_id": "$random_id123",
    "interactions": [
      {
        "type": "m.interaction.button",
        "description": "The Search command",
        "name": "Search"
      }
    ]
  },
  "type": "m.interaction.stage.start"
}
```

6. The bot now directly shows the new custom keyboard, indicating that the user currently is in a stage of the previous command.
Additionally a way of exiting that stage should be available.

7a. The user selects the exit way and the client now sends a stage end event and returns to normal chat operation.

```json
{
  "content": {
    "event_id": "$random_id123"
  },
  "type": "m.interaction.stage.end"
}
```

7b. If the user clicks the new button the client sends the command as in step 4 with additionally mentioning the `stage_id` under the 
`m.interaction.command` object. The bot after that can react either with a new stage or with the same `m.interaction.stage.end` 
event to indicate the end of a interaction flow.

#### Flow as a graphic

```
                           +----------------------------+
                           |                            |
                           |    User sends a command    |
                           |                            |
                           +---------------|------------+
                                           |
                                           |
                                           |
                                           |
                                           |
                                           |
                                           |
                          +----------------v--------------+
                          |                               |
                          |     Bot instructs client      |
                          |     to show a submenu of      |                                          +-------------------------------------------+
+------------------------>+     buttons.                  |       User exits the command flow        |                                           |
|                         |                               +----------------------------------------->+   Client sends a stage.end event.         |
|                         |     Starting a new "stage"    |                                          |                                           |
|                         |                               |                                          |   This indicates a flow end to the bot.   |
|                         +----------------|----|---------+                                          |                                           |
|                                          |    |                                                    +-------------------------------------------+
|                                          |    |
|                                          |    |
|                                          |    |
|                                          |    |
|                                          |    |
|                                          |    |
|                                          |    |
|                                          |    |                                          +---------------------------------------------+
|                                          |    |   Bot doesn't have another submenu       |                                             |
|                                          |    +----------------------------------------->+   Bot sends a stage.end event.              |
|                                          |                                               |                                             |
|                                          |                                               |   This indicated a flow end to the client.  |
|                                          |                                               |                                             |
|                                          |                                               +---------------------------------------------+
|  User selects an option and bot          |
|  has a new submenu.                      |
|  Another stage.start is sent by the bot  |
+-------------------------------------<----+

```


### Event Specification

#### m.bot.interactions

A state event defining the possible entry actions a bot has. It does not list any stage specific actions.
It is used to allow clients to display a custom keyboard and a list of command based on the defined data.

The `state_key` should be the mxid of the bot adding that event.

The `command_prefix` is used to support fallback for clients not supporting the MSC and is used to generate a irc style
bot message as fallback. (See "Fallback" section for Details).

The interactions array defines all supported entry actions of a bot, Those can be either of type: `m.interaction.command`
or `m.interaction.button`,

Example:

```json
{
  "type": "m.bot.interactions",
  "state_key": "@faq_bot:example.matrix",
  "content": {
    "command_prefix": "!",
    "interactions": [
      {
        "type": "m.interaction.command",
        "description": "Shows the help of the FAQ Bot",
        "name": "help"
      },
      {
        "type": "m.interaction.button",
        "description": "Search question",
        "name": "Search"
      }
    ]
  }
}
```

#### Interaction event types

Both `m.interaction.command` and `m.interaction.button` are required to be an object consisting of:

* Its `type`
* A useful `description` which might be used to be displayed to the user
* A `name` which is used for displaying in the UI. Be aware this is also used as lowercase for the fallback!

#### `m.room.message` extension with `m.interaction.command`

Each message that was sent using selecting either a button or command must have an additional object with the key `m.interaction.command` 
besides the body of that event.

The `target` field is required to distinguish between bots in a room. It is required at all time to contain the mxid of the bot that is meant.
This is required because there might be multiple bots with the same command.

Example:

```json
"m.interaction.command": {
  "command": "help",
  "target": "@faq_bot:example.matrix"
}
```

#### `m.interaction.stage.start`

This event indicates a new stage being entered.

The `event_id` is supposed to reference the event that was the start of the last event. So this might initially be the initial command message a user sent.

The `interactions` array is the same format as in the state event. It indicates new action specific to the current stage. 
The client should indicate that this is currently a stage of the initially started command. It should show also show the interactions the bot now added
as well as a way to abort the stage immediately. (See flow example for details)

The bot which is currently starting a stage should be identified by the sender field of the event which contains the bot mxid.

This event should be ignored when the user not started a command or the user has not previously received a stage start event. 
This can happen either because of abusive bots or because someone else started a command. Possible ways to check this are:

* Track the commands locally in the client
* Check for a `m.room.message` event with `m.interaction.command` and the `sender` matching the logged in user.

Benefit of the second option is that this works across multiple used clients.

Example:

```json
{
  "content": {
    "event_id": "$random_id123",
    "interactions": [
      {
        "type": "m.interaction.button",
        "description": "The Search command",
        "name": "Search"
      }
    ]
  },
  "type": "m.interaction.stage.start"
}
```

#### `m.interaction.stage.end`

This event indicates a flow end.

The `event_id` is supposed to reference the event that was the start of the last event. It is not supposed to be the initial command.

This event can be sent by both the client as well as the bot. 
If a client sends the event the bot should think of this as if the user aborted the current action entirely.
If a bot sends the event the client should think of this as having completed a flow fully.

This event should be ignored when the user has not started a command or the user has not previously received a stage start event. 
This can happen either because of abusive bots or because someone else started a command. Possible ways to check this are:

* Track the commands locally in the client
* Check for a `m.room.message` event with `m.interaction.command` and the `sender` matching the logged in user.

Benefit of the second option is that this works across multiple used clients.

Example:

```json
{
  "content": {
    "event_id": "$random_id123"
  },
  "type": "m.interaction.stage.end"
}
```

## What is `m.interaction.button`?

This type is meant to be like Telegram's custom keyboard feature. It is used to display a button in the UI which behaves like a custom keyboard with fixed functions.
It is however in this MSC not meant to support inline buttons on events but those in theory can be done by reusing this type.

## How are stages meant to work

Imagine stages as submenus. They are indicating the next step in a greater action. 

If a stage start is sent the user moves into the next decision tree of a menu. If a stage end happens the user gets back to the top of this decision tree.
Stage end should not be treated as a back button.


## Fallback

The fallback is done by making this a transparent change to the message event. It only adds metadata to the event instead of proposing a new message event.
This brings the benefit that the fallback works in any existing client without needing to change the clients code. This means that user without the 
MSC implemented in their client still can fully follow the conversation without missing out events.

## Other neccesarry changes to make this even work

To make this even work this needs an addition to the default room powerlevels. The `m.bot.interactions` state event type MUST be able to be set by
the rooms default Powerlevel as bots usually are just regular users and not moderators of the room.

## Potential issues

* Priority of stages is not defined if 2 commands happen at the same time
* Multiple users using multiple bots in a group is currently not handled directly. The MSC only demands to ignore stages if the user not started the command itself.

## Alternatives

* MSC2929 - This seems to solve parts of this as well but doesn't seem to specify custom keyboards
* A full form based approach where a bot can define layouts - In a discussion with multiple client developers at #matrix-client-developers:matrix.org 
this was being decided difficult or even dangerous as bots or abusive users might do harm with that and in general it seems too hard to implement.

## Security considerations

* This wasn't thought with e2ee in mind yet. It would need to be tried if it still works with being fully encrypted.
* It might leak metadata if it is not encrypted

## Unstable prefix

`dev.nordgedanken.msc3006.` shall be used as a prefix.

e.g.: `m.bot.interactions` becomes `dev.nordgedanken.msc3006.bot.interactions`
