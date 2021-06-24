### MSC2836: Threading

*This MSC probably supersedes https://github.com/matrix-org/matrix-doc/issues/1198*

Matrix does not have arbitrarily nested threading for events. This is a desirable feature for implementing clones of social
media websites like Twitter and Reddit. The aim of this MSC is to define the simplest possible API shape to implement threading
in a useful way. This MSC does NOT attempt to consider use cases like editing or reactions, which have different requirements
to simple threading (replacing event content and aggregating reactions respectively).

The API can be broken down into 2 sections:
 - Making relationships: specifying a relationship between two events.
 - Querying relationships: asking the server for relationships between events.

The rest of this proposal will outline the proposed API shape along with the considerations and justifications for it.

#### Making relationships

Relationships are made when sending or updating events. The proposed API shape is identical to
[MSC1849](https://github.com/matrix-org/matrix-doc/blob/matthew/msc1849/proposals/1849-aggregations.md):
```
{
    "type": "m.room.message",
    "content": {
        "body": "i <3 shelties",
        "m.relationship": {
            "rel_type": "m.reference",
            "event_id": "$another_event_id"
        }
    }
}
```

Justifications for this were as follows:
 - Quicker iterations by having it in event content rather than at the top-level (at the `event_id` level).
 - Ability for relationships to be modified post-event creation (e.g by editing the event).
 - Doesn't require any additional server-side work (as opposed to adding the event ID as a query param e.g `?in-reply-to=$foo:bar`).

Drawbacks include:
 - Additional work required for threading to work with E2EE. See MSC1849 for proposals, but they all boil down to having the `m.relationship`
   field unencrypted in the event `content`.

Edge cases:
 - Any event `type` can have an `m.relationship` field in its `content`.
 - Redacting an event with an `m.relationship` field DOES NOT remove the relationship. Instead, it is preserved similar to how `membership`
   is preserved for `m.room.member` events, with the following rules:
     * Remove all fields except `rel_type` and `event_id`.
     * If `rel_type` is not any of the three types `m.reference`, `m.annotation` or `m.replace` then remove it.
     * If `event_id` is not a valid event ID (`$` sigil, correct max length), then remove it.

   The decision to preserve this field is made so that users can delete offensive material without breaking the structure of a thread. This is
   different to MSC1849 which proposes to delete the relationship entirely.
 - It is an error to reference an event ID that the server is unaware of. Servers MUST check that they have the event in question: it need not
   be part of the connected DAG; it can be an outlier. If the server does not have this event but can fetch this event from another server
   in the room using the `room_id` key as a hint then this is acceptable. This prevents erroneous relationships being made by abusing the CS API.
   Note that it is expected that events over federation will reference event IDs that the receiving server is unaware of: this is allowed.
   This check is only performed when *clients* attempt to make new references.
 - It is an error to reference an event ID in another room.
 - It is an error to reference yourself. Cyclical loops are still possible by using multiple events and servers should guard against this by
   only visiting events once.

#### Querying relationships

Relationships are queryed via a new CS API endpoint:
```
POST /_matrix/client/r0/event_relationships
{
    "event_id": "$abc123",         // the anchor point for the search, must be in a room you are allowed to see (normal history visibility checks apply)
    "room_id": "!foo:localhost"    // Optional. A hint to the server which is used if the event ID is not found. The room ID can be used to work out which servers may have the event.
    "max_depth": 4,                // if negative unbounded, default: 3.
    "max_breadth": 10,             // if negative unbounded, default: 10.
    "limit": 100,                  // the maximum number of events to return, server can override this, default: 100.
    "depth_first": true|false,     // how to walk the DAG, if false, breadth first, default: false.
    "recent_first": true|false,    // how to select nodes at the same level, if false oldest_first - servers compare against origin_server_ts, default: true.
    "include_parent": true|false,  // if event_id has a parent relation, include it in the response, default: false.
    "include_children": true|false // if there are events which reply to $event_id, include them all (depth:1) in the response: default: false.
    "direction": up|down           // if up, parent events (the events $event_id is replying to) are returned. If down, children events (events which reference $event_id) are returned, default: "down".
    "batch": "opaque_string"       // A token to use if this is a subsequent HTTP hit, default: "".
}
```
which returns:
```
{
    "events": [                    // the returned events, ordered by the 'closest' (by number of hops) to the anchor point.
        { ... }, { ... }, { ... },
    ],
    "next_batch": "opaque_string", // A token which can be used to retrieve the next batch of events, if the response is limited.
                                   // Optional: can be omitted if the server doesn't implement threaded pagination.
    "limited": true|false          // True if there are more events to return because the `limit` was reached. Servers are not obligated
                                   // to return more events, see if the next_batch token is provided or not.
}
```

Justifications for the request API shape are as follows:
 - The HTTP path: cross-room threading is not currently allowed but is possible hence the path not being underneath `/rooms`.
   An alternative could be `/events/$event_id/relationships` but there's already an `/events/$event_id` deprecated endpoint and
   nesting this new MSC underneath a deprecated endpoint conveys the wrong meaning.
 - The HTTP method: there's a lot of data to provide to the server, and GET requests shouldn't have an HTTP body, hence opting
   for POST. The same request can produce different results over time so PUT isn't acceptable as an alternative.
 - The anchor point: pinning queries on an event is desirable as often websites have permalinks to events with replies underneath.
 - The `room_id`: The intention is to support the idea of permalinks to events. Even if event IDs were
   [global](https://github.com/matrix-org/matrix-doc/blob/travis/msc/global-event-ids/proposals/2848-global-event-ids.md),
   not all servers will have all events in a room. This means that a server may be allowed to see an event, they just need to request
   it from the right server. The room ID is a convenient way to map to a list of servers who may have this event. This is optional,
   and the lack of a room ID just means if the event ID in the request is not known to the server, the request fails. If the room ID
   is specified, then a federated `/event_relationships` request can be made (see next section).
 - The max depth: Very few UIs show depths deeper than a few levels, so allowing this to be constrained in the API is desirable.
 - The max breadth: Very few UIs show breadths wider than a few levels, so allowing this to be constrained in the API is desirable.
 - The limit: For very large threads, a max depth/breadth can quickly result in huge numbers of events, so bounding the overall
   number of events is desirable. Furthermore, querying relationships is computationally expensive on the server, hence allowing
   it to arbitrarily override the client's limit (to avoid malicious clients setting a very high limit).
 - The depth first flag: Some UIs show a 'conversation thread' first which is depth-first (e.g Twitter), whereas others show
   immediate replies first with a little bit of depth (e.g Reddit).
 - The recent first flag: Some UIs show recent events first whereas others show the most up-voted or by some other metric.
   This MSC does not specify how to sort by up-votes, but it leaves it possible in a compatible way (e.g by adding a
   `sort_by_reaction: 👍` which takes precedence which then uses `recent_first` to tie-break).
 - The include parent flag: Some UIs allow permalinks in the middle of a conversation, with a "Replying to [link to parent]"
   message. Allowing this parent to be retrieved in one API hit is desirable.
 - The include_children flag: Some UIs allow permalinks in the middle of a conversation, with immediate children responses
   visible. Allowing the children to be retrieved in one API hit is desirable.
 - The direction enum: The decision for literal `up` and `down` makes for easier reading than `is_direction_up: false` or
   equivalent. The direction is typically `down` - find all children from this event - but there is no reason why this cannot
   be inverted to walk up the DAG instead.
 - The batch token: This allows clients to retrieve additional results. It's contained inside the HTTP body rather than as
   a query param for simplicity - all the required data that the server needs is in the HTTP body. This token is optional as
   paginating is reasonably complex and should be opt-in to allow for ease of server implementation.

Justifications for the response API shape are as follows:
 - The events array: There are many possible ways to structure the thread, and the best way is known only to the client
   implementation. This API shape is unopinionated and simple.
 - The next batch token: Its presence indicates if there are more events and it is opaque to allow server implementations the
   flexibility for their own token format. There is no 'prev batch' token as it is intended for clients to request and persist
   the data on their side rather than page back and forth through results like traditional pagination.
 - The limited flag: Required in order to distinguish between "no more events" and "more events but I don't allow pagination".
   This additional state cannot be accurately represented by an empty `next_batch` token.

Server implementation:
 - Sanity check request and set defaults.
 - Does the server have the event given by `event_id`? If yes, continue. If no, check for a `room_id` key. If one exists then ask
   servers in the room for `event_id` (e.g via `/event_relationships`). If no server has the event, reject the request.
 - Can the user see (according to history visibility) `event_id`? If no, reject the request, else continue.
 - Retrieve the event. Add it to response array.
 - If `include_parent: true` and there is a valid `m.relationship` field in the event, retrieve the referenced event.
   Apply history visibility check to that event and if it passes, add it to the response array.
 - If `include_children: true`, lookup all events which have `event_id` as an `m.relationship` - this will almost certainly require
   servers to store this lookup in a dedicated table when events are created. Apply history visibility checks to all these
   events and add the ones which pass into the response array, honouring the `recent_first` flag and the `limit`.
 - Begin to walk the thread DAG in the `direction` specified, either depth or breadth first according to the `depth_first` flag,
   honouring the `limit`, `max_depth` and `max_breadth` values according to the following rules:
     * If the response array is `>= limit`, stop.
     * If already processed event, skip.
     * Check how deep the event is compared to `event_id`, does it *exceed* (greater than) `max_depth`? If yes, skip.
     * Check what number child this event is (ordered by `recent_first`) compared to its parent, does it *exceed* (greater than) `max_breadth`? If yes, skip.
     * Process the event. If the event has been added to the response array already, do not include it a second time. If an event fails history visibility
       checks, do not add it to the response array and do not follow any references it may have.

   This algorithm bounds an infinite DAG
   into a "window" (governed by `max_depth` and `max_breadth`) and serves up to `limit` events at a time, until the entire window
   has been served. Critically, the `limit` _has not been reached_ when the algorithm hits a `max_depth` or `max_breadth`, it is only
   reached when the response array is `>= limit`.
 - When the thread DAG has been fully visited or the limit is reached, return the response array as `events` (and a `next_batch` if the request
   was limited). If a request comes in with the `next_batch` set to a valid value, continue walking the thread DAG from where it
   was previously left, ensuring that no duplicate events are sent, and that any `max_depth` or `max_breadth` are honoured
   _based on the original request_ - the max values always relate to the original `event_id`, NOT the event ID previously stopped at.

##### Querying relationships over federation

Relationships can be queried over federation using a new endpoint which is the same as the CS API format. See the CS API section for more info. The path
used for this new federation endpoint is `/_matrix/federation/v1/event_relationships`. There is one additional response field: `auth_chain` which contains
all the necessary auth events for the events in `events`, e.g:
```
{
    "events": [                    // the returned events, ordered by the 'closest' (by number of hops) to the anchor point.
        { ... }, { ... }, { ... },
    ],
    "next_batch": "opaque_string", // A token which can be used to retrieve the next batch of events, if the response is limited.
                                   // Optional: can be omitted if the server doesn't implement threaded pagination.
    "limited": true|false,         // True if there are more events to return because the `limit` was reached. Servers are not obligated
                                   // to return more events, see if the next_batch token is provided or not.
    "auth_chain": [                // The auth events required to authenticate events in `events`, in any order without duplicates.
        { ... }, { ... }, { ... },
    ]
}
```

Justification:
 - In an ideal world, every server would have the complete room DAG and would therefore be able to explore the full scope of a thread in a room. However,
   over federation, servers have an incomplete view of the room and will be missing many events. In absence of a specific API to explore threads over
   federation, joining a room with threads will result in an incomplete view.
 - The requirements here have a lot in common with the [Event Context API](https://matrix.org/docs/spec/client_server/r0.6.0#id131). However, the context
   API has no federated equivalent. This means any event context requests for events the server is unaware of will incorrectly return `404 Not Found`.
 - The same API shape is proposed to allow code reuse and because the same concerns and requirements are present for both federation and client-server.

Server behaviour:
 - When receiving a request to `/event_relationships`: ensure the server is in the room then walk the thread in the same manner as the CS API form. Do not
   make outbound `/event_relationships` requests on behalf of this request to avoid routing loops where 2 servers infinitely call `/event_relationships` to
   each other.
 - For each event returned: include all `auth_events` for that event recursively to create an auth chain and add them to `auth_chain`.
 - Servers should make outbound `/event_relationships` requests *for client requests* when they encounter an event ID they do not have, or they suspect
   that the event has children the server does not have (see the next section). The event may have happened much earlier in the room which another server
   in the room has.

#### Exploring dense threads

The proposed API so far has no mechanism to:
 - List the absolute number of children for a given event.
 - Check that the server has all the children for a given parent event.

To aid this, all events returned from `/event_relationships` SHOULD have 2 additional fields in the `unsigned` section of the event:
 - `children`: A map of `rel_type` to the number of children with that relation.
 - `children_hash`: The base64 string of the SHA256 of all the event IDs of the known children, deduplicated and sorted lexicographically. 

For example, an event `$AAA` with three children: `$BBB`, `$CCC`, `$DDD` where the first two are of `rel_type` "m.reference" and the last is "custom", should
produce an `unsigned` section of:
```
unsigned: {
  children: {
    "m.reference": 2,
    "custom": 1
  },
  children_hash: "GE6QH8oImiq8IoMwQmIDxF9keqtY2Q7KKtJ4caXdYb0=" // base64(SHA256("$BBB$CCC$DDD"))
}
```

Justification:
 - Without this information, it's impossible to know if an event has children _at all_. Servers need to know if children exist so they can fetch them
   over federation.
 - This allows clients to display more detailed "see more" links e.g. "... and 56 more replies".
 - This allows servers to identify when a federated `/event_relationships` request has been window culled by `max_depth` or `max_breadth`, or has just not
   been explored yet.
 - Separating out the counts by `rel_type` allows clients to accurately determine whether children are threaded replies or some other relation.

Server behaviour:
 - When processing an `/event_relationships` response from another server:
    * For each event, check the children count and hash. If there is no `unsigned` section assume the count to be 0.
    * If this event is new, persist it. If this event is not new, compare the children counts. The event with a higher children count should be persisted:
      specifically the `unsigned` section should be persisted as the event itself is immutable.
    * When returning events to another server or to a client, always return the `unsigned` section which produces the *most* children, and NOT the number
      of children the server currently has fetched.
 - When processing an `/event_relationships` request from a client:
    * If the event ID is unknown, perform a federated `/event_relationships` request. Alternatively, if the event is known **and there are unexplored children**,
      perform a federated `/event_relationships` request.
    * An event has unexplored children if the `unsigned` child count on the parent does not match how many children the server believes the parent to have.
      In addition, if the counts match but the hashes do not match, then the event is unexplored.
    * Regardless of whether the federated `/event_relationships` request returns the missing children, mark the event as explored afterwards. This prevents
      constantly hitting federation when walking over this event. The easiest way to mark the event as explored is to remember what the highest children count was
      when the most recent federated request was made, along with the hash of those children. If that number differs from the current `unsigned` count
      or the numbers match but the hashes differ then it is unexplored.
    * Due to marking events as explored regardless of what is returned from the request, it is possible for it to be known that there are missing children on
      an event but being unable to retrieve them. This can happen if the only server with those events goes down before they can be replicated via `/send` to
      other servers, but after another server pulls in the parent event with the right `unsigned` counts. The alternative would be to constantly ask servers
      if they have the children which would increase federation traffic needlessly.
 - Explored events will always remain up-to-date assuming federation between the two servers remains intact. If there is a long outage, any new child will be
   marked as "unexplored" (because the parent event will be missing) and trigger an `/event_relationships` request, akin to how the `/send` federation API will
   trigger `/get_missing_events` in the event of an unknown `prev_event`. This will then pull in events heading up to the root event, along with `unsigned` children
   counts of any potential branches in the thread.
