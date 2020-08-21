# MSC2403: Add "knock" feature
Many people are in invite-only rooms. Sometimes, someone wants to join such a
room and can't, as they aren't invited. This proposal adds a feature for a
user to indicate that they want to join a room.

# Proposal
This proposal implements the reserved "knock" membership type for the
`m.room.member` state event. This state event indicates that when a user
knocks on a room, they are asking for permission to join. It contains an
optional "reason" parameter to specify the reason you want to join. Like
other membership types, the parameters "displayname" and "avatar_url" are
optional. This membership can be set from users who aren't currently in said
room. An example for the membership would look like the following:
```json
{
  "membership": "knock",
  "displayname": "Alice",
  "avatar_url": "mxc://example.org/avatar",
  "reason": "I want to join this room as I really love foxes!"
}
```

After a knock is received in a room, it is expected to be displayed in the
timeline, similar to other membership changes. It is recommended to not
display the reason until the user interacts with the client in some way (e.g.
clicking on a "show reason" button), as else this would essentially allow
outsiders to send messages into the room. Clients can optionally add a way
for users of a room to review all current knocks. After a knock in a room, a
member of the room can invite the knocker.

To be able to implement this properly, two new endpoints need to be added:
one in the Client-Server API and one in the Server-Server API.

## Restrictions
There are restrictions to being able to set this membership.

### Current membership
Only users without a current membership or with their current membership
being "leave" can knock on a room. This means that a user that is banned or
currently in the room cannot knock on it.

### Join Rules
The `join_rule` of `m.room.join_rules` must be set to "invite" for a knock to
succeed. This means that people can't knock in public rooms. Additionally the
new join rule "private" is introduced. This is so that people can, when
creating a new room, prevent anyone from knocking.

### Power levels
The default power level for "knock" is the default power level for the room.
If a user has a too low power level to knock, then they aren't allowed to do
so. As power levels can be set for users not currently in the room, this can
be used as a way to limit who can and can't knock.

#### Example:
`@alice:example.org` CAN knock, but `@bob:example.org` CANNOT: The
(incomplete) content of `m.room.power_levels` is as follows:
```json
{
  "users": {
    "@alice:example.org": 1
  },
  "users_default": 0,
  "knock": 1
}
```

## Membership changes
Once someone has sent a `knock` membership into the room, the membership for
that user can be transitioned to the following possible states:
 - `invite`: In this case, the knock was accepted by someone inside the room
   and they are inviting the knocker into the room.
 - `leave`: In this case, similar to how kicks are handled, the knock has
   been rejected.
 - `ban`: In this case, the knock was rejected and the user has been prevented
   from sending further knocks.

## Client-Server API
Two new endpoints are introduced in the Client-Server API (similarly to
join): `POST /_matrix/client/r0/rooms/{roomId}/knock` and
`POST /_matrix/client/r0/knock/{roomIdOrAlias}`.

### `POST /_matrix/client/r0/rooms/{roomId}/knock`
The path parameter (`roomId`) is the room on which you want to knock. It is
required. The post body accepts an optional string parameter, `reason`, which
is the reason you want to join the room. A request could look as follows:

```
POST /_matrix/client/r0/rooms/%21d41d8cd%3Amatrix.org/knock  HTTP/1.1
Content-Type: application/json

{
  "reason": "I want to join this room as I really love foxes!"
}
```

#### Responses:
##### Status code 200:
The user knocked successfully. Empty reply:
```json
{}
```

##### Status code 400:
This request was invalid, e.g. bad JSON. Example reply:
```json
{
  "errcode": "M_UNKNOWN",
  "error": "An unknown error occurred"
}
```

##### Status code 403:
The user wasn't allowed to knock (e.g. they are banned). Error reply:
```json
{
  "errcode": "M_FORBIDDEN",
  "error": "The user isn't allowed to knock in this room."
}
```

##### Status code 429:
This request was rate-limited. Example reply:
```json
{
  "errcode": "M_LIMIT_EXCEEDED",
  "error": "Too many requests",
  "retry_after_ms": 2000
}
```

### `POST /_matrix/client/r0/knock/{roomIdOrAlias}`
The path parameter (`roomIdOrAlias`) is either the room ID or the alias of
the room you want to knock on. Additionally several `server_name` parameters
can be specified via the query parameters. The post body accepts an optional
string parameter, `reason`, which is the reason you want to join the room. A
request could look as follows:

```
POST /_matrix/client/r0/knock/%23monkeys%3Amatrix.org?server_name=matrix.org&server_name=elsewhere.ca  HTTP/1.1
Content-Type: application/json

{
  "reason": "I want to join this room as I really love foxes!"
}
```

#### Responses:
The possible responses are the same as for the `POST
/_matrix/client/r0/rooms/{roomId}/knock` endpoint.

## Server-Server API
Similarly to join and leave over federation, a ping-pong game with two new
endpoints is introduced: `make_knock` and `send_knock`. Both endpoints must
be protected via server ACLs.

### `GET /_matrix/federation/v1/make_knock/{roomId}/{userId}`

Asks the receiving server to return information that the sending server will
need to prepare a knock
event.

Request format:

| Parameter | Type | Description |
|-----------|------|-------------|
| Path parameters:
| roomId | string | Required. The room ID that should receive the knock.
| userId | string | Required. The user ID the knock event will be for.
| Query Parameters:
| ver | [string] | The room versions the sending server has support for. Defaults to `[1]`.

Response Format:

| Parameter | Type | Description |
|-----------|------|-------------|
| room_version | string | The version of the room where the server is trying to knock.
| event | Event Template | An unsigned template event. May differ between room versions.

#### Responses
##### Status code 200:
Returns a template to be used to knock on rooms. May depend on room version.
```json
{
  "room_version": "2",
  "event": {
    "type": "m.room.member",
    "room_id": "!somewhere:example.org",
    "content": {
      "membership": "knock"
    },
    "state_key": "@someone:example.org",
    "origin": "example.org",
    "origin_server_ts": 1549041175876,
    "sender": "@someone:example.org"
  }
}
```

##### Status code 400:
This request was invalid, e.g. bad JSON. Example reply:
```json
{
  "errcode": "M_INCOMPATIBLE_ROOM_VERSION",
  "error": "Your homeserver does not support the features required to join this room",
  "room_version": "3"
}
```

### `PUT /_matrix/federation/v1/send_knock/{roomId}/{eventId}`
Submits a signed knock event to the resident server for it to accept into the
room's graph. Note that event format may differ between room versions.

Request format:

| Parameter | Type | Description |
|-----------|------|-------------|
| Path parameters:
| roomId | string | Required. The room ID that should receive the knock.
| eventId | string | Required. The event ID for the knock event.

The JSON body is expected to be the full event.

Response Format:

| Parameter | Type | Description |
|-----------|------|-------------|
| `<body>` | [integer, Empty Object] |

A request could look as follows:
```
PUT /_matrix/federation/v1/send_knock/%21abc123%3Amatrix.org/%24abc123%3Aexample.org HTTP/1.1
Content-Type: application/json

{
  "sender": "@someone:example.org",
  "origin": "matrix.org",
  "origin_server_ts": 1234567890,
  "type": "m.room.member",
  "state_key": "@someone:example.org",
  "content": {
    "membership": "knock",
    "displayname": "Alice",
    "avatar_url": "mxc://example.org/avatar",
    "reason": "I want to join this room as I really love foxes!"
  }
}
```

#### Response:
##### Status code 200:
The event was successfully accepted into the graph by the receiving
homeserver.
```json
{}
```

# Potential issues
This new feature would allow users to spam rooms that they don't partake in.
That is why this proposal adds both the new join rule and the new power
level, in order to allow room admins to mitigate such potential spam.

# Alternatives
As for the join rule "invite", instead the join rule "knock" could be
introduced, meaning the room is like "invite" only that people can also
knock. The difference is for existing rooms: With this proposal people can
knock in existing "invite" rooms, with the alternative suggestion being that
they can't.

The two endpoints for the Client-Server API seem redundant, this MSC followed
how JOIN is working currently: One "proper" endpoint (`/rooms/{roomId}/join`)
and one to work properly over federation (`/join/{roomIdOrAlias}`). They
could both be merged into one, however, as that would also affect the join
endpoint it seems out-of-scope for this MSC.

# Security considerations
This doesn't allow users access to a room in any way. However, care should be
taken to ensure that no spam vectors are enabled by this change.