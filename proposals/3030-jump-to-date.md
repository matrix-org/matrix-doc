# MSC3030: Jump to date API endpoint

Add an API that makes it easy to find the closest messages for a given timestamp.

The goal of this change is to have clients be able to implement a jump to date feature in order to see messages back at a given point in time. Pick a date from a calender, heatmap, or paginate next/previous between days and view all of the messages that were sent on that date.

For our [roadmap of feature parity with Gitter](https://github.com/vector-im/roadmap/issues/26), we're also interested in using this for a new better static Matrix archive. Our idea is to server-side render [Hydrogen](https://github.com/vector-im/hydrogen-web) and this new endpoint would allow us to jump back on the fly without having to paginate and keep track of everything in order to display the selected date.

Also useful for archiving and backup use cases. This new endpoint can be used to slice the messages by day and persist to file.

Related issue: [*URL for an arbitrary day of history and navigation for next and previous days* (vector-im/element-web#7677)](https://github.com/vector-im/element-web/issues/7677)


## Problem

These types of use cases are not supported by the current Matrix API because it has no way to fetch or filter older messages besides a manual brute force pagination from the latest. Paginating is time-consuming and expensive to process every event as you go (not practical for clients). Imagine wanting to get a message from 3 years ago 😫


## Proposal

Add the `?around=<timestamp>` query parameter to the `GET /_matrix/client/r0/rooms/{roomId}/messages` endpoint. This will start the response at the message with `origin_server_ts` closest to the provided `around` timestamp. The direction is determined by the existing `?dir` query parameter.

Use topoligical ordering, just as Element would use if you follow a permalink.


## Potential issues

If you ask for “the message with `origin_server_ts` closest to Jan 1st 2018” you might actually get a rogue random delayed one that was backfilled from a federated server, but the human can figure that out by trying again with a slight variation on the date or something.


## Alternatives

### Filter by date in `RoomEventFilter`

Extend `RoomEventFilter` to be able to specify a timestamp or a date range. The `RoomEventFilter` can be passed via the `?filter` query param on the `/messages` endpoint.


### New `destination_server_ts` field

Add a new field and index on messages called `destination_server_ts` which indicates when the message was received from federation. This gives a more "real" time for how someone would actually consume those messages.

The contract of the API is "show me messages my server received at time T" rather than the messy confusion of showing a delayed message which happened to originally be sent at time T.

We've decided against this approach because the backfill from federated servers could be horribly late.

---

Related issue around `/sync` vs `/messages`, https://github.com/matrix-org/synapse/issues/7164

> Sync returns things in the order they arrive at the server; backfill returns them in the order determined by the event graph.
>
> *-- @richvdh, https://github.com/matrix-org/synapse/issues/7164#issuecomment-605877176*

> The general idea is that, if you're following a room in real-time (ie, `/sync`), you probably want to see the messages as they arrive at your server, rather than skipping any that arrived late; whereas if you're looking at a historical section of timeline (ie, `/messages`), you want to see the best representation of the state of the room as others were seeing it at the time.
>
> *-- @richvdh , https://github.com/matrix-org/synapse/issues/7164#issuecomment-605953296*


## Security considerations

We're only going to expose messages according to the existing message history setting in the room (`m.room.history_visibility`). No extra data is exposed, just a new way to sort through it all.



## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*
