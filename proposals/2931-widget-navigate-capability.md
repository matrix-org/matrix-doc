# MSC2931: Widget navigate permission

[Widgets](https://github.com/matrix-org/matrix-doc/pull/2764) currently have some capability to
affect how a client operates, though given the embedded nature of widgets it is desirable to have
even more functionality.

Widgets are currently expected to have significantly increased interaction with the client (as shown
by [MSC2762 - Send/receive events](https://github.com/matrix-org/matrix-doc/pull/2762) and
[MSC2876 - Read events](https://github.com/matrix-org/matrix-doc/pull/2876)), and as such it's a
natural extension to give widgets an option to route the user to another room or visit a permalink.
This sort of extension would be useful for directing support queries to the right room, or implementing
scoreboard widgets for polls/messages in a room with permalinks to the messages.

## Proposal

A new capability, `m.navigate`, is introduced to gate a `navigate` request/response over the widget API.
The `navigate` action takes one parameter, `uri`, in its `data` - this is the matrix.to (or in future
Matrix URI scheme) URI the client should honour. The request is acknowledged with an empty response body.

Example request, using the standardized format:

```json5
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "navigate",
  "data": {
    "uri": "https://matrix.to/#/!room:example.org/$event?via=example.org"
  }
}
```

Example response:

*Note*: A standardized response is a complete copy of the request with an added `response` field. In
this case, the response is just an acknowledgement of receipt and is thus empty.

```json5
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "navigate",
  "data": {
    "uri": "https://matrix.to/#/!room:example.org/$event?via=example.org"
  },
  "response": {}
}
```

As with all capabilities, clients SHOULD prompt the user to approve the widget's use of the navigate
action before allowing it. The navigate action is only valid once the session has been established
(after capabilities are exchanged, essentially).

The client can reject a widget's navigate action, even if approved by the capability, on any grounds
it deems reasonable such as considering permalinks to other rooms being too great of a security risk.
This is done with the standardized error response. Clients should reject the request if they don't
support the feature at all, such as navigating to user profiles.

## Potential issues

This might be giving widgets too much power or helping set a precedent that widgets should have
tightly integrated features with the client. Ideally, widgets gain more power without sacrificing
privacy and security - the capabilities system is meant to prevent this.

## Alternatives

None appear relevant. The idea here is to be as supportive as possible using existing technologies.
[Prior work](https://github.com/matrix-org/matrix-react-sdk/pull/5385) in this area has been done in
Element Web by limiting the request to only viewing rooms - since that work it's become apparent that
more general handling of matrix.to links is needed, and the security risk is less concerning now that
the feature has been used in practice.

## Security considerations

Widgets can do all sorts of things like spam the client with requests to navigate somewhere or direct
the user to an abusive room/user/event - clients are expected to handle rate limiting, and the abusive
content direction is generally considered a social problem rather than a technical one for this MSC.
Widgets should only be added by trusted members of a room (moderators and admins, typically) and thus
is is generally expected that one wouldn't add this variety of malicious widget to a room. Other attacks
of a similar nature are made irrelevant by the same argument.

## Unstable prefix

Implementations should use `org.matrix.msc2931.navigate` as the capability and action while this MSC
is not in a released version of the spec. Implementations should also look for/expose `org.matrix.msc2931`
as a supported version over the Widget API.
