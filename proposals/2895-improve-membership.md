# Improving the way membership lists are queried

Note: this MSC has been converted from a legacy MSC format to Markdown verbatim. The prior
MSC is documented [here](https://docs.google.com/document/d/1WgfAK_O6Ih22badCX4-rComT9sz4cHiPa3pGuTejszU/edit#).

Previous history of this MSC is at https://github.com/matrix-org/matrix-doc/pull/1337

## Problem scope

A common operation for bots, bridges, scripts, and clients is to determine what rooms the user is a
member of and who the members of those rooms are. Although possible with the current specification,
the API can be improved to provide more granular and simplified access to this information.

The affected routes are:

* `GET /_matrix/client/r0/rooms/{roomId}/members`
* `GET /_matrix/client/r0/rooms/{roomId}/joined_members`
* `GET /_matrix/client/r0/joined_rooms`

This proposal aims to resolve [matrix-doc#1123](https://github.com/matrix-org/matrix-doc/issues/1123).

## Background

The `/joined_members` and `/joined_rooms` endpoints were originally added in [synapse#1680](https://github.com/matrix-org/synapse/pull/1680)
during a time when the IRC bridge on matrix.org was under extreme load. The endpoints were fully
intended to alleviate load by having the bridge do less work and have the server doing more.

## Proposal

This proposal calls for both `/joined_members` and `/joined_rooms` to be deprecated. The
deprecation is to be coupled with improving how `/members` works and introducing a new `/rooms`
endpoint, which will work in a very similar way to the updated `/members` endpoint. Both endpoints
are proposed to get some way to filter based upon membership, as outlined in the options below.

### Option 1: Query string

A new query parameter, `membership`, should be added to the `/members` endpoint. The parameter
filters the membership list of the room such that only members with a matching `membership` are
returned. The parameter can be supplied multiple times to filter on multiple membership states. For
example, the request could be `/members?membership=join&membership=invite` to get all invited and
joined members for the room. If no `membership` parameter is specified, the default is to return
all members of the room regardless of membership state.

To compliment the `/members` endpoint, a new endpoint should be added to query the rooms for the
user. This uses the same style of using a membership query parameter to filter the rooms.

Some examples of using this endpoint are below. The `rooms` field is an object where the key is a
room ID and the value is information about that room, currently storing a single `membership`
field. The value is an object to support future expansion of this API.

```json5
// GET /_matrix/client/r0/rooms?membership=join&membership=invite
{
   "rooms": {
       "!somewhere:domain.com": {
           "membership": "join"
       },
       "!elsewhere:matrix.org": {
           "membership": "invite"
       }
   }
}
```

```json5
// GET /_matrix/client/r0/rooms?membership=ban
{
   "rooms": {
       "!plzno:domain.com": {
           "membership": "ban"
       }
   }
}
```

```json5
// GET /_matrix/client/r0/rooms
{
   "rooms": {
       "!somewhere:domain.com": {
           "membership": "join"
       },
       "!elsewhere:matrix.org": {
           "membership": "invite"
       },
       "!plzno:domain.com": {
           "membership": "ban"
       },
       "!curbaf:domain.com": {
           "membership": "leave"
       }
   }
}
```

### Option 2: Filter

As with Option 1, a new endpoint would be added to handle getting the list of rooms. However, instead of both `/members` and `/rooms` taking a query parameter for membership they would instead take a filter (re-using existing matrix concepts). Similar to how `/messages` works, this filter would be a `RoomEventFilter` instead of having all the available options. Additionally, the filter would support a `membership` field to filter based upon membership.

An example filter for getting members/rooms of membership `invite` or `join` would be:

```json5
{
   "limit": 5, // The maximum number of items to return. Defaults to no limit.

   // These only apply when fetching members in a room
   "senders": ["*"],
   "not_senders": [],

   // These only apply when fetching rooms
   "rooms": ["*"],
   "not_rooms": [],

   // NEW! Filter based upon the given membership values.
   "membership": ["join", "invite"],

   // These are copied from the RoomEventFilter schema, but are ignored
   "types": [],
   "not_types": [],
   "contains_url": true,
}
```

### Option 3: Even more filters

Expanding on Option 2, we give `/state` the option of a filter (also from Option 2). This would
require the `types` to be useful, and we could potentially deprecate the `/members` endpoint
entirely with this approach.

Likewise, `/context` should take a similar filter so clients can get members at a given point in
history.

## Alternative solutions

### Using ?membership=join,invite or ?membership=join+invite instead

The arguments in favour of this approach are:

* It doesn’t rely on undefined behaviour in RFC3986
* Using multiple keys in the query string hasn’t been done before in the matrix spec

The arguments against this approach are:

* It’s not as pretty and may require hex encoding
* It adds unnecessary complexity given most query string parsers are capable of handling multiple
  keys in the query string. It is additional complexity because implementations would now need to
  do string splitting instead of relying on their already-in-use parsing libraries

### Encoding ?membership as a JSON value

The arguments in favour of this approach are:

* The filtering API already does this
* It doesn’t rely on undefined behaviour in RFC3986

The arguments against this approach are:

* It’s not as pretty and requires hex encoding
* Implementations would be forced to perform decoding, adding additional complexity (see the con
  for comma-separated values)
