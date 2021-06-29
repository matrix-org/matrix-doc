# MSC3009: Websocket transport for client <--> widget communications

If a widget wishes to speak with a client (or a client with a widget) then the implementation must
support postmessage as a capability, however not all scenarios for widgets make this possible. For
example, mobile apps and thinly wrapped widgets may not have enough JavaScript available to handle
the postmessage API.

*Note*: A thinly wrapped widget is one which is in a theoretical web view which disconnects the widget
from the client, for clients which cannot reasonably support a webview or similar. This is primarly
a solution for desktop clients, which puts the actual client and widget in different processes (the
desktop app running on its own with the widget running in a web browser after being 'popped out').

## Proposal

A websocket transport is defined in addition to the existing postmessage API support. This alternative
transport is opt-in by the client for the widget to handle. The API over postmessage is quite simply
the same as the postmessage API but with the added implicit behaviour that `waitForIframeLoad` is `false`
(this causes the client to wait for the widget to reach out to the client instead of the client
assuming the widget has loaded).

Because there would be two transports available, clients need to know which ones are available on
the widget, and the widget should not be required to implement them all. This proposal opens up an
opportunity for custom transports through a namespaced array of transports being listed on the standardized
widget definition:

```json5
{
  "type": "m.custom",
  "url": "http://localhost:8082#?widgetId=$matrix_widget_id&transport=$matrix_widget_transport",
  "name": "Widget Debugger",
  "avatar_url": "mxc://t2bot.io/c977fc5396241194e426e6eb9da64f025f813f1b",
  "data": {
    "title": "Widget testing"
  },
  "creatorUserId": "@travis:localhost",
  "id": "debugger_test",

  // This is the only added field.
  "transports": [
    "m.postmessage",
    "m.websockets"
  ]
}
```

If the `transports` array is empty, undefined, or the wrong data type then the client will assume that
the widget definition meant `["m.postmessage"]` for a value. If the array contains no known transports
to communicate with the widget, the client will assume the widget supports `m.postmessage` as a baseline.
This means `m.postmessage` remains the bare minimum every widget must support.

Prior to rendering the widget, the client picks the transport and spins up any applicable servers (websocket
receivers, etc) for the widget to communicate with. The client communicates the transport it chose with
an available `$matrix_widget_transport` template variable.

When the `m.websockets` transport is chosen, a `$matrix_websocket_uri` template variable is made available
by the client containing the `ws://` URI for the widget to connect to. Because the widget is expected to
make first contact, the client should already be listening and not try to connect to the widget.

## Rationale for websockets

Websockets are bidirectional and about as easy as HTTP to set up and deploy in modern applications. Most
use cases will see local clients spinning up servers and therefore the complexities of corporate firewalls
should not apply.

However, using websockets means that the widget cannot be contacted and is assumed to reach out to the client
first. This could potentially leave the client in an unknown state where it is waiting for the widget to reach
out, but the widget died or refuses to do so. Reconnection attempts by the widget may also be confusing to
the client (client restarts but widget doesn't, or local network issues) - **this has undefined behaviour
under this MSC currently.**

## Potential issues

Web clients (and widgets) will not be able to create websocket servers to listen for requests from widgets,
making this MSC targeted specifically at desktop/mobile clients which are typically more able to do so.
Web clients in particular are likely to need their own alternative transport for cases when the widget
is popped out of the client's context, such as in a new tab.

This MSC also introduced capabilities for arbitrary alternative transports. This isn't necessarily seen
as a bad thing, though could lead to fragmentation among the widget authoring community. This MSC attempts
to mitigate that fragmentation by maintaining a baseline transport.

There is also a question if this is even needed: if [MSC3008 - Scoped access](https://github.com/matrix-org/matrix-doc/pull/3008)
were to be accepted, the only remaining functionality would be the capabilities API (for which few capabilities
are useful in this use case) and other smaller client manipulation MSCs. Given the widget is separated from
the client, it may not be desirable to support [MSC2931 - matrix.to navigation](https://github.com/matrix-org/matrix-doc/pull/2931)
over this alternative transport, for example. Similarly, there is nothing to pin to the screen and therefore
the widget's attempts to request an "always on screen" capability would be for naught.

## Alternatives

Regular HTTP might also work, as would Server-Sent Events, though these are inherently one-way or require
excessive resources to make two-way. Other efficient transports are not easily available on all platforms,
such as lower level TCP/UDP-based transports.

## Security considerations

There is a high likelihood that when a client spins up a websocket server that it'll be bound to localhost
without TLS. This could be problematic if widgets are transferring sensitive information over the API
which could be intercepted by local processes. This is akin to a malicious browser extension listening for
postmessage requests on `*`, however.

## Unstable prefix

The `transports` array becomes `org.matrix.msc3009.transports` while this MSC is not considered stable. The
template variables `$matrix_widget_transport` and `$matrix_websocket_uri` become `$org.matrix.msc3009.widget_transport`
and `$org.matrix.msc3009.websocket_uri` respectively.

The transports become `org.matrix.msc3009.postmessage` and `org.matrix.msc3009.websockets`. Communication
over either transport is not required to be namespaced in any particular way, however any unstable actions
over the widget API must be appropriately prefixed.
