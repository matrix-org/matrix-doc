## Introduction

Currently, Matrix clients use long polling to get the latest state from the server,
it becomes an issue when you have a lot of clients because:
* homeserver needs to process a lot of requests, which by the way may return nothing
* it affects network bandwidth, each time client sends request it creates a new HTTP
  request with headers, cookies and other stuff
* for mobile clients, it spends their cellular Internet and eats money
* when homeserver uses SSL over HTTP (what is recommended),
  clients are doing again and again the most expensive operation, the TLS handshake

So, instead of long polling I propose to implement
sync logic over [Server Sent Events][mdn-sse](SSE)

## Proposal

[Server Sent Events][mdn-sse](SSE) is a way for servers to push events to clients.
It was a part of HTML5 standard and now available in all major web and mobile browsers.
It was specifically designed to overcome challenges related to short/long polling.
By introducing this technology, we can get the next benefits:
* only 1 persisted connection per client that is kept open "forever".
* SSE is built on top of HTTP protocol, so can be used in communication between servers
* SSE is more compliant with existing IT infrastructure like (Load Balancer, Firewall, etc) than websockets
* web and mobile browsers support automatic reconnection and `Last-Event-Id` header out of the box
* Matrix protocol is built over HTTP, so SSE should fit good in protocol specification

Check this for details:
* https://medium.com/axiomzenteam/websockets-http-2-and-sse-5c24ae4d9d96
* https://www.html5rocks.com/en/tutorials/eventsource/basics/
* https://stackoverflow.com/questions/9397528/server-sent-events-vs-polling
* https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
* supported browsers: https://caniuse.com/#feat=eventsource

SSE is easy to implement by your own on server side as it just a text based streaming on top of HTTP
but there are libraries which can do this for us (e.g., https://pypi.org/project/Flask-SSE/).
Support for SSE exists in Android and iOS libraries as well (few quickly googled):
* Android - http://kaazing.org/
* iOS - https://github.com/inaka/EventSource

This proposal doesn't change the shape of Matrix events or required parameters to do state synchronization
but instead propose to use a different underlying technology to do this. So:
* lets expose `/sync/sse` URL for SSE in order to be backward compatible with other clients and servers
* this URL returns the same data as continually calling `/sync`
* it accepts the same parameters as `/sync`, except `since` and `timeout`
* it accepts additional `heartbeat_interval` parameter in seconds.
  If not passed, server will send heartbeat payload every 5 seconds (I guess we need configuration on server side for this).
  The server must send heartbeat payload every `heartbeat_interval` seconds.
  The heartbeat payload has the form of the empty SSE comment `: \n\n`
* instead of using the `since` query parameter, the next batch token will be passed through the `Last-Event-ID` header
* each [SSE event payload][sse-payload] will have the same format as what [`/sync` returns][matrix-sync]. The `id` of each SSE event equals to the `next_batch` token
* the server sends SSE events in exactly the same way that it would send responses to `/sync` calls with the `since`
  parameter set to the previous `next_batch`


## Tradeoffs

Another alternative is to implement websocket communication for state synchronization. So, why not websockets?
* websockets are built over TCP protocol and requires implementation in server language
* some proxy servers or firewalls may block websockets
* [HTTP/2 was standardized in 2015 without any mention of WebSockets][http2-websockets]
  and only in 2019 support for websockets over HTTP/2 was added.
* lack of built-in support for `Last-Event-Id` and automatic reconnection

The main difference between Websockets and SSE is that the first one is 2 way communication.
But with adoption of HTTP/2, which can be easily enabled in reverse proxy like nginx over HTTPS,
HTTP requests are cheaper than in HTTP/1.1 due to headers compression and request multiplexing.
So, it's not an issue anymore to send requests from client via regular HTTP and get events via SSE.

## Potential issues

Don't see issues. There are old web browsers which does not support SSE
but polyfills with SSE implementation can be used.

## Security considerations

No security issues from SSE perspective

## Conclusion

By adopting SSE, homeservers will be able to keep higher load and bigger amount of clients
s SSE was designed to handle these cases with low consumption of resources.
SSE is just a HTTP streaming (basically `Content-Type`),
so it should fit good in existing HTTP infrastructure and Matrix protocol.

[mdn-sse]: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
[http2-websockets]: https://medium.com/@pgjones/http-2-websockets-81ae3aab36dd
[sse-payload]: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format
[matrix-sync]: https://matrix.org/docs/spec/client_server/r0.5.0#get-matrix-client-r0-sync
