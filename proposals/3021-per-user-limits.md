# MSC3021: Limits API — Part 1: per-User Fanout Limits

Not all servers are as lucky as matrix.org to have variable scaling,
hence some of them will need to place fanout limits on users and rooms,
such as how many rooms a user is allow ürüned to be member of, how many members can
a room simultaneously have, how many child rooms a space room is allowed
to have, or how many sessions a user is allowed to have simultaneously open.
This MSC deals with the easiest part, per-user fanout limits.

## The basics

To modify the limit of a particular user:
```
PUT /_matrix/client/r0/admin/limits/{user_id} HTTP/1.1
{
   "type": "m.limits.fanout.user_rooms",
   "value": 123456789
}
```

To modify the limits of all users:
```
PUT /_matrix/client/r0/admin/limits/ HTTP/1.1
{
   "type": "m.limits.fanout.user_rooms",
   "value": 123456789
}
```
If `value` is not defined, then said limit is not defined.

The query will be made to the same paths, using the GET method instead.
And to delete the limit for the particular user, use the DELETE method
for the same path. A user is allowed to query users from own homeserver only.
If, a server-wide limit is defined but a user specific limit is not,
the user specific limit shall be returned as if it were the same. In case
both limits exist, the smaller limit for a given user shall apply.

Every user MUST be allowed to query own limits, and users MAY be allowed to 
query others' limits and change them.

For now, two such limits are proposed:

* Per-user room limit: `m.limits.fanout.user_rooms`
* * Per-user room-as-type limit: `m.limits.fanout.user_rooms.{room_type}`
* Per-user device limit: `m.limits.fanout.open_sessions`

## The per-user room limit semantics

A user shall not be allowed to join more rooms once it joins as many rooms as 
specified by the per-user room limit. The join requests will be rejected,
invites overturned and knocks ignored by the server. As soon as the number of
rooms user has joined drops below the limit, joins will be processed as usual.

If a user has more room than it is allowed to be joined when the limit is put
in place, it is to be auto-kicked from the excess rooms by the server
starting from the last joined one. If a limit for a particular type of room
exists, that limit shall only be considered for that type of room. For example,
`m.limits.fanout.user_rooms.space` will only affect space rooms and not bare
rooms. If the limit for a subtype of room is greater than the general room limit
per user, the subtype limit will be ignored.

## The per-user session limit semantics

A user shall not be allowed to create new sessions once the number of open
sessions reaches the limit. As soon as the number of open sessions drops below
the limit, logins will be processed as usual. If a user has more open sessions
than it is allowed to be open when the limit is put in place, it is to be
logged out from the excess sessions by the server starting from the least
recently active session according to the last log-out time of said sessions.

## Alternatives considered

None considered yet.

## Security considerations

An administrator may abuse the limiting capabilities to randomly prevent the user
from joining various rooms without leaving a recorded trail.
