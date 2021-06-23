# Proposal for inline widgets

We already have widgets for rooms (stored in room state) and account-specific widgets
(stored in account data), however we do not have a way for widgets which are only
relevant for as long as the message is visible. Inline widgets would be an option
for rich embedding of content within the timeline, such as polls, buttons, and
better embeds for things like videos.

There are three common use cases which this proposal addresses:
1. Embedding fully-functional HTML apps into the timeline (video embeds, etc).
2. Native poll support for Matrix.
3. Native hint buttons for users to click (for menu-based bot navigation).

Other use cases are excluded from this proposal, but may fit into the first given
the arbitrary web application support.


## Proposal

This proposal is heavily insipired by:
* [MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236) - Original Widget API
* [MSC1485](https://github.com/matrix-org/matrix-doc/issues/1485) - Hint buttons on messages
* [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849) - Reactions/Aggregations

MSC1236 is largely untouched by this proposal, however this proposal borrows the structure
and behaviour of widgets to better define what an inline widget does.

MSC1485 in particular is obsoleted by this proposal and presented as polls/bot buttons
instead. Some of the features of MSC1485 (like images on buttons) have not been included
here for simplicity - MSC1485 or a future proposal is more than welcome to introduce those
features, and this proposal should accomodate future expansion in those areas.

MSC1849 is used to define the relationship of a button press to an event, similar to how
MSC1485 did the relationship but instead using MSC1849's topology for the linking.

#### Inline Widgets (use case 1)

These widgets are rendered in the timeline just like any other message, and have a structure
very similar to room widgets. An inline widget is an `m.room.message` with a `msgtype` of
`m.widget`, as shown:

```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.widget",
        "body": "https://www.youtube.com/watch?v=a4L94Rsg_nM",
        "widget_url": "https://www.youtube.com/embed/a4L94Rsg_nM",
        "waitForIframeLoad": true,
        "type": "m.video",
        "name": "YouTube",
        "data": {
            "title": "Matrix Live S03E25",
            "url": "https://www.youtube.com/watch?v=a4L94Rsg_nM"
        }
    }
}
```

Note that the `creatorUserId` and `id` fields from room/account widgets are not
included - these can be easily inferred from the `sender` and `event_id` of the event
itself.

Just like room/account widgets, inline widgets support templating. Inline widgets
should also not rely on the `$matrix_user_id` being trusted and instead should seek
to authenticate the user somehow else.

**Note**: the `url` field was not chosen for widgets because some clients, servers,
and bots rely on its presence to identify events which contain `mxc` URIs. In order
to avoid confusion, we prefix the field with `widget_`.

Still like room/account widgets, inline widgets have access to the same Widget API
from MSC1236. They also should be sandboxed, and prevented from manipulating the
client outside of the client's control.

Clients SHOULD limit the maximum height and width of inline widgets to prevent
large portions of the timeline being inaccessible to users. Scrollbars are encouraged
for long/large content.

#### Polls and Bot Buttons (use cases 2 & 3)

Technically speaking, these are not widgets in and of themselves, however they
behave very similar to how a dedicated widget would. For this reason, they are
proposed here.

Just like widgets, clients should limit the dimensions of polls and bot buttons.
Buttons in particular should be length-limited to prevent their text being too
long.

Polls and bot buttons do not inherit the Widget API as there is nothing for them
to inherit. Clients are responsible for managing permissions, if required.

Polls and bot buttons are `m.room.message` events with a `msgtype` of `m.options`,
as shown:

```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.options",
        "body": "[Poll] What is your favourite food?\n1. Pizza\n2. Ice Cream",
        "type": "m.poll",
        "label": "What is your favourite food?",
        "options": [
            {
                "label": "Pizza",
                "value": "1. Pizza"
            },
            {
                "label": "Ice Cream",
                "value": "2. Ice Cream"
            }
        ]
    }
}
```
```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.options",
        "body": "What would you like to do?\n1. Create Github issue\n2. Search Github\n3. Logout",
        "type": "m.buttons",
        "label": "What would you like to do?",
        "options": [
            {
                "label": "Create Github issue",
                "value": "1. Create Github issue"
            },
            {
                "label": "Search Github",
                "value": "2. Search Github"
            },
            {
                "label": "Logout",
                "value": "3. Logout"
            }
        ]
    }
}
```

Polls (identified by a `content.type` of `m.poll`) have special behaviour:
* Clients should render results on the original event.
  * If not rendering the results on the original event, clients should show
    responses in the timeline like any other message.
* Clients should allow the user to change their answer.
* Clients should consider a user's most recent (by `origin_server_ts`) response as their
  current answer. Previous answers are considered void.
* Applications which send polls (bots, bridges, etc) should react to unlinked messages
  which match the appropriate button as a fallback. For example, if someone sent the
  message "Pizza" without the appropriate relation, the application should still consider
  it. Clients are not expected to do this, but should if possible.

Plain buttons (identified by a `content.type` of `m.buttons`) are expected to be used
by bots and similar applications which do not need exactly 1 answer from the user. Like
polls, applications are expected to consider events without the appropriate relationship
as responses to the question posed.

Clients SHOULD render the buttons where possible, or otherwise fall back to the `m.text`
behaviour for a message (the default in most clients). When rendering the buttons, clients
MUST present the buttons in the order defined by `content.options` with the optional
`content.label` being rendered above the buttons. Clients MUST display the option's
`label` as the button's display value, and when the button is clicked clients MUST send
an event to the room resembling the following:
```
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.response",
        "body": "3. Logout",
        "m.relates_to": {
            "rel_type": "m.response",
            "event_id": "$options_event_id",
            "option": 2
        }
    }
}
```
The `body` of the message MUST be the `value` of the option being chosen, and the relationship
MUST reference the original poll/bot buttons event. The relationship's `option` value
is the index of the option which was clicked, counting from zero.

For polls in particular, it may be important to close the poll after some time. This
can only be done by the original poll sender (clients MUST ignore attempts to close
polls sent by other users), and takes the form of a simple relationship:
```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.poll_closed",
        "body": "I no longer care what your favourite food is",
        "m.relates_to": {
            "rel_type": "m.close",
            "event_id": "$options_event_id"
        }
    }
}
```
The `body` in this event is for fallback purposes and should at a minimum be the string
"poll closed".

Clients SHOULD NOT consider responses after the close event (by `origin_server_ts`) as
valid responses. Non-polls cannot be closed, instead applications are expected to handle
cases of late replies or redact the original event.

Clients SHOULD validate that the `option` in the relationship is a valid option, and
ignore the response if invalid. The user's last valid response is to be used for the
purposes of tallying the votes, if there is any.


## Potential issues

This proposal is potentially limited in what polls/options can be presented to a user
without the use of a full-blown inline widget (therefore requiring a web server). Previous
drafts of this proposal supported an extended set of Matrix HTML to offer forms to users
which could then be used to render polls and similar functionality without the integration
asking the question requiring a web server. The complexity with that approach was that
it relied on HTML, which some clients cannot or will not support. The approach additionally
opened up the client to several XSS and similar security vulnerabilities due to the complex
nature of untrusted user-provided HTML being rendered in the client.

Future proposals may wish to consider how to represent other form controls like checkboxes
and radio buttons, however this proposal is intentionally not expanding into this area.
Potentially, a `type` can be introduced to each option which tells the client how to
render it (ie: `m.checkbox` or similar).

This proposal additionally takes the stance of backwards compatibility, further extending
the life of `msgtype`. In other proposals it has been proposed that new event types be
introduced instead of using `msgtype`, however this results in clients not being able to
render the events correctly. Until [MSC1767 - Extensible events](https://github.com/matrix-org/matrix-doc/pull/1767)
is implemented, this proposal aims for maximum compatibility with all clients while
also introducing new functionality. This is done in 2 primary ways:
1. Widgets have a fallback `body` of the widget URL so at worst people can click the
   visit the widget manually in older clients.
2. Polls and bot buttons have the entire sequence using the fallback `body` so that
   older clients can still participate in the discussion.


## Security considerations

Allowing arbitrary embeds opens up a spam vector for auto-playing videos, scare content,
and similar spam. Clients should do their best to avoid these kinds of attacks, such as
by blocking the widget from loading until the user accepts the widget.

Polls should not be used for important matters like voting for presidents or cabinet members.

#### A note about encryption

Per the current spec, `m.relates_to` is not encrypted. This does mean that the user's
act of picking an option (or closing a poll) is exposed as metadata. However, the options
themselves (including the question) are encrypted, therefore not exposing which option
the user picked - just that an option was picked.


## Alternative solutions

There are two possible alternatives to cover use cases 2 & 3 which are of relevance:

#### Introducing more widget types instead of event types

The relationship/threading behaviour for polls/buttons is a bit complicated and subject
to error. Instead of over-specifying new msgtypes, we could introduce a `m.poll` or
`m.form` widget with a `data` object which lists API endpoints for clients to call when
they want to render the widget natively.

The widget spec already supports clients ignoring the widget's URL and rendering a
native component, such as how the Riot mobile clients handle Jitsi integration. We would
just have to supply a `data` object which could be used by clients.

A roughly formed `m.poll` widget could look like:
```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.widget",
        "body": "Poll: What is your favourite food?",
        "widget_url": "https://example.org/polls/1234.html",
        "waitForIframeLoad": true,
        "type": "m.poll",
        "name": "Poll",
        "data": {
            "title": "Favourite Food",
            "optionsApi": "https://example.org/api/polls/1234/options",
            "submitApi": "https://example.org/api/polls/1234/submit"
        }
    }
}
```

The `optionsApi` and `submitApi` schema would need to be specified as well.

#### Extended Matrix HTML for inline widgets

As alluded to earlier in this proposal, inline HTML could be used instead of the
`widget_url` field. In the interest of preserving the historical record more cleanly,
the entire previous draft is included here.

An inline HTML widget would take the following form, noting the use of `widget_html`
instead of `widget_url` to define the widget:
```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.widget",
        "body": "Poll: What is your favourite food?",
        "widget_html": "<button data-mx-action='sendText' data-mx-value='Ice Cream'>Ice Cream</button><button data-mx-action='sendText' data-mx-value='Pizza'>Pizza</button>",
        "waitForIframeLoad": true,
        "type": "m.custom",
        "name": "Poll",
        "data": {
            "title": "Favourite Food"
        }
    }
}
```

Events should only contain a `widget_url` or a `widget_html`, however when both are
specified clients should prefer to use the `widget_url`.

Inline HTML widgets inherit all behaviour of inline widgets above.

The HTML supported by `widget_html` is the same HTML set supported by Matrix
already (see paramgraphs under [m.room.message types](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-message-msgtypes))
with a few additions:
* `button` is allowed with the `data-mx-action`,`data-mx-value`, and `name` attributes.
* `select` is allowed with the `name` attribute.
* `option` (under `select`) is allowed with the `value` and `selected` attributes.
* `input` is allowed with types `radio`, `checkbox`, `text`, and `password`. Inputs
  can additionally have `placeholder`, `value`, `checked`, and `name` as attributes.
* `form` is allowed with the `data-mx-event-type` attribute.
* `label` is allowed.

The attributes have special meanings:
* `data-mx-action` can be one of `m.send_text`, `m.send_notice`, or `m.send_hidden`.
  Because the attribute is only applicable to buttons, when the button is clicked
  the action occurs through the Widget postMessage API:
  * `m.send_text`: Sends the `data-mx-value` as an `m.text` room message.
  * `m.send_notice`: Sends the `data-mx-value` as an `m.notice` room message.
  * `m.send_hidden`: Sends the `data-mx-value` as an `m.room.hidden` event in the
    `body` field of the `content`.

  When buttons do not have this field, they should be assumed to be submit buttons
  for the parent `form`, if present.
* `data-mx-event-type` is the type of event to send when the form is submitted. The
  event's content will be a mapping of all the `name` attributes for form elements
  (`select` and `input`) in the form, with the added `m.form_name` for the `form`'s
  `name` and `m.button_name` for the `button`'s `name` which was clicked. For example,
  the following HTML:
  ```html
  <form data-mx-event-type="org.example.poll_response" name="favourite_food">
      <select name="preset">
          <option value="Ice Cream" selected>Ice Cream</option>
          <option value="Pizza">Pizza</option>
      </select>
      <input type="text" placeholder="Other" name="other">
      <label>
        <input type="checkbox" name="certified" value="yes" checked>
        I certify this is my favourite food.
      </label>

      <p>
        Second favourite food:
        <label><input type="radio" name="second_favourite" value="Ice Cream" checked> Ice Cream</label>
        <label><input type="radio" name="second_favourite" value="Pizza"> Pizza</label>
        <label><input type="radio" name="second_favourite" value="Chips"> Chips</label>
      </p>
      <button name="submit">Submit</button>
  </form>
  ```
  would produce the following event when the submit button was pressed:
  ```json
  {
      "type": "org.example.poll_response",
      "content": {
          "m.form_name": "favourite_food",
          "m.button_name": "submit",
          "preset": "Ice Cream",
          "other": "Doughnuts",
          "certified": "yes",
          "second_favourite": "Ice Cream"
      }
  }
  ```

  If no form `name` is specified, `m.form_name` is not included. Likewise for the
  button pressed. `m.form_name` and `m.button_name` SHOULD be added last to avoid
  forms overwriting the values (although doing so wouldn't cause problems anyways).

  For radio buttons, checkboxes, and selects: if no option is selected then the
  value is not included in the event. Empty textboxes are included as empty strings.

  Note that no validation is permitted by the HTML: the use of `widget_html` is
  not meant to be fully-featured. More advanced use cases are expected to be
  handled by `widget_url` instead, as it is not under the same limitations.

When handling `widget_html`, clients SHOULD wrap the HTML in their own local
wrapper. For example, a client may embed an iframe with a URL of
`/widget_html.html?html=...` for sandboxing.

In order to allow the widget to send custom/non-standardized events, a new postMessage
API needs to be considered. In MSC1236 there is a `fromWidget` action for `send_event`,
however in practice this action was never implemented. Instead, the action was
implemented as the event type to send (`fromWidget` action of `m.sticker`, for example).
This proposal re-introduces `send_event` with an altered payload to better suit custom
events:
```json
{
    "api": "fromWidget",
    "action": "send_event",
    "widgetId": "ID_GOES_HERE",
    "event_type": "org.example.poll_response",
    "event_content": {...}
}
```

This proposal does not support sending state events through this action. To negotiate
sending of the event type, the widget would request the event type prefixed with the
string `"m.send."` as the capability. For example, the widget would request the
`m.send.org.example.poll_response` capability in the above examples.
