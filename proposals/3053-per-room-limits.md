# MSC3053: Limits API — Part 2: per-Room Fanout and Complexity Limits

Not all servers are as lucky as matrix.org to have variable scaling,
hence some of them will need to place fanout limits on users and rooms,
such as how many rooms a user is allowed to be member of, how many members can
a room simultaneously have, how may child rooms a space room is allowed
to have, or how many sessions a user is allowed to have simultaneously open.
This MSC deals with per-room fanout and complexity limits.

## The basics

Per-room fanout limit means a limit imposed on a particular room, across
all participating server instances. Room complexity limit means a limit
imposed across some or all rooms in a particular instance. Room complexity
limit is only an upper bound and a server may choose to implement
a lower limit than one set by this API.

To modify the limit of a particular room:
```
PUT /_matrix/client/r0/admin/limits/{room_id} HTTP/1.1
{
   "type": "m.limits.complexity.user_cap",
   "value": 123456789
}
```

To modify the limits of all rooms:
```
PUT /_matrix/client/r0/admin/limits/ HTTP/1.1
{
   "type": "m.limits.complexity.user_cap",
   "value": 123456789
}
```

The modify the user limit of room across servers, this state event shall be
sent to the room:
```
{
   "type": "m.limits.fanout.room_users",
   "state_key": "user_cap",
   "value": 123456789
}
```

If `value` is not defined, then said limit is not defined either.

The query will be made to the same paths, using the GET method instead.
And to delete the limit for the particular user, use the DELETE method
for the same path. A user is allowed to query users from own homeserver only.
If, a server-wide limit is defined but a room specific limit is not,
the room specific limit shall be returned as if it were the same. In case
both limits exist, the smaller limit for a given room shall apply.

For now, four such limits are proposed (with event types and state keys respectively):

* Per-room user fanout limit: `m.limits.fanout.room_users` / `users`
* Immediate child room nesting limit: `m.limits.fanout.room_children` / `children`
* Inherited child room nesting limit: `m.limits.fanout.room_branching` / `branches`
* Descendant room nesting limit: `m.limits.fanout.room_rooms` / `room_rooms`
* Per-room user complexity limit: `m.limits.complexity.user_cap` / `user_cap`
 * Per-room-as-type user complexity limit: `m.limits.complexity.user_cap.{room_type}`
 / not applicable to room state events

Room limits specified as sub-keys of `m.limits.fanout` are sent as state events,
and room limits specified as subkeys of `m.limits.complexity` are sent as admin
API settings, as shown above by user capping example.

## The per-room user limit semantics

A room shall not be allowed to have more members once it has as many members as 
specified by the per-room user limit. The join requests will be rejected,
invites overturned and knocks ignored by the server. As soon as the number of
rooms user has joined drops below the limit, joins will be processed as usual.

If a room has more users than it is allowed to be joined when the limit is put
in place, then the join of exceeding users shall be undone according to
the state resolution order, but only to the point of the limit request,
and no further. If a limit for a particular type of room exists, that limit
shall only be considered for that type of room. For example,
`m.limits.complexity.room_users.space` will only affect space rooms and
not bare rooms. If the limit for a subtype of room is greater than
the general user limit per room, the subtype limit will be ignored.
To set per-room user fanout limit, user has to have power to `limits`.
The power level required for `limits` shall be greater than or equal to
the greatest of the power level required for `invite`, `redact`, `ban`,
`power_levels`.

## Room nesting limit semantics

A room shall not be allowed to have more child rooms once it has as many children
as specified by the child limit. New child rooms will not be added. As soon as
the number of child rooms drops below the limit, joins will be processed as usual.

* Immediate child room nesting limit only affects direct children of said rooms.
* Inherited child room limit affects direct children of said rooms, and
 is recursively applied to child rooms.
* Descendant room nesting limit affects all descendants of said rooms.

If the limit for a subtype of room is greater than the general nesting limit
per room, the subtype limit will be ignored. To set per-room nesting limit,
user has to have power to `tombstone` and `attach`.

## Alternatives considered

Having those limits as permanent limits specified as fields in the `m.room.create`
event of the respective room (Later changed the plans to bring this forward as
another MSC, as an orthogonal feature with changeable ones).

## Security considerations

Misuse of this feature might cause permanently forking a room.

## Unstable prefix and room version

As this feature requires a new room version, `org.matrix.msc3053.limits` can be
used as the unstable room version. And `r0` should be replaced by `unstable` for
unstable endpoint paths.
