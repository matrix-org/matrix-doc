# MSC2871: Sending approved capabilities back to the widget

Under the [current spec for widgets](https://github.com/matrix-org/matrix-doc/pull/2764), the session
for a widget is established once the widget responds to the capabilities request from the client. The
widget isn't made aware of which capabilities it was actually approved for, in the case of a user
manually selecting which capabilities to approve, and doesn't know when this process is complete.

Some widgets need to know if they have a certain capability as early as possible so they can start
working in the client, such as a conference widget which might want to immediately set itself as
sticky to the screen. Under the current structure, the widget is forced to repeat the API request
until it succeeds, which is not great.

## Proposal

A new request is added to the `toWidget` API to tell the widget which capabilities it was approved
for. The request is acknowledged with an empty response by the widget. Here's an example:

```json
{
  "api": "toWidget",
  "requestId": "AAABBB",
  "widgetId": "CCCDDD",
  "action": "notify_capabilities",
  "data": {
    "requested": ["m.always_on_screen", "com.example.cap"],
    "approved": ["m.always_on_screen"]
  }
}
```

The `requested` array is to indicate what the client ultimately received for ease of debugging as well
as indicating to widget developers if there's any parsing errors with their capabilities. The `approved`
array is simply what the client is allowing the widget to have. This should be a subset or the entirety
of the `requested` array - widgets (generally speaking) should not be approved for capabilities they
did not request.

The session behaviour is unchanged by this MSC - once the widget requests capabilities the session is
established and thus the `notify_capabilities` can happen any time after that. This is largely a
backwards compatibility measure to ensure that existing widgets which expect sending capabilities to
mean that the widget can start making other requests.

The client can also hold off on sending the `notify_capabilities` action until it is fully ready for
the widget to continue bootstrapping. For example, if the client wanted a little bit of extra time to
prepare for a particular kind of widget, it would withhold the `notify_capabilities` action until it
was ready to further deal with the widget. The client should send it as soon as possible once it is
able to fill out the details of the request.

## Potential issues

None relevant. Worst case the widget responds with an error saying that it doesn't understand the
request, which clients should handle gracefully already.

## Alternatives

None relevant. Some widgets need to know when they are safe to make requests and others need to know
if they were approved for a given capability.

## Security considerations

As mentioned, widgets should not be receiving capabilities that they did not request.

## Unstable prefix

Until this MSC is in a release version of the specification, implementations can use the `org.matrix.msc2871`
version on `supported_versions` to detect support.
