# MSC2695: Get event by ID over federation

Currently, there is no clear client-server API to retrieve a single event by the
event ID alone. There is the deprecated [`GET
/_matrix/client/r0/events/{eventId}`](https://matrix.org/docs/spec/client_server/latest#deprecated-get-matrix-client-r0-events-eventid),
but this could be removed some day and also does not support accessing events on
remote servers over federation.

As part of revising matrix.to URI syntax in
[MSC2644](https://github.com/matrix-org/matrix-doc/pull/2644), there is
interest in supporting permalinks to events that contain the event ID without
the room ID. In order for such links to be useful, we need a clear path to get
that event using the event ID without having the room ID.

While the matrix.to interstitial UI is the primary initial use case, other tools
that wish to preview or display a single event should benefit from having such
an API as well.

## Proposal

This proposal un-deprecates and extends the existing `GET
/_matrix/client/r0/events/{eventId}` API to address this need.

### API details

`GET /_matrix/client/r0/events/{eventId}`

Get a single event based on `eventId`.

You must have permission to retrieve this event e.g. by being a member in the
room for this event in order to access the full event content. If the room is
`world_readable`, the full event content can be retrieved without
authentication.

For all events, even those for which you do not have access, this API will
always return at least the `event_id` and `room_id` keys (assuming the event can
be found locally or via one of the provided servers). In this way, this API can
always be used to determine the room ID of an event, as long as a server in the
room is known.

If the event is not known to the local server, it will attempt to retrieve the
event via federation (e.g. `GET /_matrix/federation/v1/event/{eventId}`) from
the provided servers in the `server_name` query parameter.

* Authentication
  * Optional
  * If called without authentication, then only events in `world_readable` rooms
    are accessible.
* Rate-limited
  * Since this revised version supports unauthenticated requests, rate limiting
    is important to limit abuse and DoS attacks
* Path parameters
  * `eventId` (`string`): **Required.** The event ID to get.
* Query parameters
  * `server_name` (`[string]`): The servers to attempt to get the event from if
    unknown to the local server. One of the servers must be participating in the
    room.

#### Example request

`GET
/_matrix/client/r0/events/%24Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU?server_name=matrix.org&server_name=example.org
HTTP/1.1`

#### Example responses

If the event is found and is either `world_readable` or the authenticated user
has permission to retrieve it, then the full event content is returned with
status code 200:

```
{
  "content": {
    "body": "This is an example text message",
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "formatted_body": "<b>This is an example text message</b>"
  },
  "type": "m.room.message",
  "event_id": "$Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU",
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "origin_server_ts": 1432735824653,
  "unsigned": {
    "age": 1234
  }
}
```

If the event is found but is not allowed to be retrieved, then a short form with
only `event_id` and `room_id` is returned with status code 200:

```
{
  "event_id": "$Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU",
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org"
}
```

If the event cannot be found on the local server and is not present on the
optionally provided servers, then return status code 404.

If the requester has been rate-limited, return status code 429 with the usual
content:

```
{
  "errcode": "M_LIMIT_EXCEEDED",
  "error": "Too many requests",
  "retry_after_ms": 2000
}
```

## Potential issues

This proposal revives and extends a previously deprecated API. While that should
be safe given that it does not introduce breaking changes, there could be other
currently unknown complexities that result.

## Alternatives

Rather than reusing and extending an existing API, a new one could be defined
instead. If there is some reason to not revive the existing API, this may indeed
end up as the preferred approach. For the moment, reviving the existing API
seems preferable, as it already makes use of the simplest, most obvious API path
suited for this purpose.

## Security considerations

The proposed version of the API adds support for unauthenticated access. This is
a key feature of the proposal, as it is desirable to support a static matrix.to
interstitial page that may wish to query event details (assuming the user agrees
to such requests) without requiring such a page to create an authenticated
session on some server for every viewer. Supporting unauthenticated access opens
the door to possible DoS attacks by e.g. requesting every event one by one via
this API. It is therefore critical to have good rate-limiting measures in place
for both authenticated and unauthenticated requesters.

## Unstable prefix

Although this proposal revives and extends an existing API, it seems prudent to
test the revised version under the `/unstable` prefix at first, just as if it
were a fully new API.

No `unstable_features` flag is currently envisioned at this time, as it does not
seem critical to ask in advance whether a server supports the proposal.
