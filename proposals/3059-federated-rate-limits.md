# MSC3059: Limits API — Part 3: Federated per-user ratelimiting on Matrix

Not all servers are as lucky as matrix.org to have variable scaling,
hence some of them will need to place rate limits on users and rooms,
and users and admins should be able to check and modify them in a
standardised way, and the servers should be able to communicate those
kinds of rate limits in a standardised way. This has been mentioned
in **[#803](https://github.com/issues/803)**.

## The basics

As **[@ara4n](https://github.com/ara4n)** said in **[#803](https://github.com/issues/803)**:

> Suggestions are:
> 
>  * **Rate limit per-user**.  This has the disadvantage that a server admin will have to
>  reach down from the heavens and explicitly configure config or something for
>  particular sets of users. This feels fragile and kludgy, and overlaps with
>  the current AS-configuration stuff where we can configure rate limiting for particular
>  namespaces of users (but only if they're an AS).
>  * **Rate limit per-room(-per-user)**.  This is nicer as we can just store it in room state,
>  and people can set it based on power levels.  It has the disadvantage though that after
>  rate-limiting has been disabled in a huge room, someone can accidentally/deliberately
>  still DoS the server out of existence.  This could be extended to per-room-per-user rules
>  too  (i.e. let this particular user talk fast in this particular room) but that
>  feels a bit overkill.
>  * **Rate limit per-room(-per-user), but with units being egress-msg/s
>  rather than ingress-msgs/s** 
>  This might be quite an elegant solution to prevent server overload.  By specifying the limit
>  in egress-msg/s, you can be confident that a room won't sprout lots of users and then overload
>  the server — and it lets server admins specify a meaningful global cap per-server too. 
>   (i.e. configure that no user is allowed to trigger more than 100 egress messages
>   per second, or whatever).

All rate limits are in this proposal are applied by the homeserver.
In more detail: The limits shall be enforced by the initiating user's homeserver,
based on the server's own time of receiving the event and checked by other servers
and receiving clients, again based of the same `origin_server_ts` value. An event
is to be rejected immediately if it exceeds the rate limit set for that kind of event.
Rate limiting events with negative values are ill-formed. Unit of the rate limits
are events per second, ie `ev Hz`.

A rate limit of zero for particular event type means that the event is completely
disallowed for the applicable users of the rate limit. Rate limit events with
universal scope and value zero are ill-formed, so are rate limiting events with
value zero that only cover rate limiting events. If a rate limiting event with
a particular scope includes rate limiting events within its scope and its value
is zero, that limit is ignored for rate limiting events and previous rate limit
continues to apply for rate limiting events only, still considering the limiting
scope of the previous rate limiting events that affect the rate limiting events
in the process of rate limiting. Rate limit increases are retroactive
and decreases apply going forward from the point the request is made.
Rate limiting events themselves follow a different rate limit excess policy
from other events:

Rate limit events will not be rejected for exceeding the rate limits
unless all the limit has entirely been spent by rate limiting events. 
If a rate limit is reached by a rate limiting event otherwise, those
actions are to be taken in order, until rate limits are obeyed again:
1. The last rate limit of the same scope sent from same homeserver
will be replaced as-if by editing, if the new limit has a greater
limit value than the old one.
2. The previous non-rate limiting, non-membership events are
invalidated according to state resolution order starting from the tip.

Rate limit events in an end-to-end encrpyted room that only cover end-to-end
encrypted events shall also be sent end-to-end encrypted, and otherwise be
rejected by the homeserver as unauthorised.

## Per-user per-server event rate limiting semantics

To modify per-user event rate limit of all users:
```
PUT /_matrix/client/r0/admin/limits/ HTTP/1.1
{
   "type": "m.limits.rate.user",
   "value": 123.4567
}
```

To modify per-user event rate limit of all users for some event types:
```
PUT /_matrix/client/r0/admin/limits/scoped HTTP/1.1
{
   "type": "m.limits.rate.user",
   "limits": {"m.room.message": 123.4567, "m.ban": 1.234567}
}
```

To modify per-user event rate limit of a particular user:
```
PUT /_matrix/client/r0/admin/limits/{user_id} HTTP/1.1
{
   "type": "m.limits.rate.user",
   "value": 123.4567
}
```

To modify per-user event rate limit of a particular user for some event types:
```
PUT /_matrix/client/r0/admin/limits/{user_id}/scoped HTTP/1.1
{
   "type": "m.limits.rate.user",
   "limits": {"m.room.message": 123.4567, "m.ban": 1.234567}
}
```
Queries are made to the same paths, using GET method instead.
Users can query rate limits of users from the same homeserver.
To clear the limit, either DELETE the rate limit or send a 
not defined value. A server is free to apply lower limits
than set by these endpoints at some or all times.

## Per-user per-room event rate limiting semantics

The event bodies are very similar to above per-user per-server limits.
An example state event below (in the example below, both the power
level and roles are specified but normally those two will not appear
in the same time):

```
{
   "type": "m.limits.rate.user",
   "power_level": 0,
   "power_level.operator": "maximum",
   "users": [],
   "users.operator": "include",
   "roles": [],
   "roles.operator": "include_min(1)",
   "limits": {"m.room.message": 123.4567, "m.ban": 1.234567}
}
```

Limits are cleared and edited following the usual message editing conventions.
`users` is an unordered list of user MXIDs and/or aliases.
`power_level` is the power level that the rate limit is going to be applied.
`power_level.operator` is the relevant comparison operator that the power level
is going to be applied. Valid operators are greater than or equal (`minimum`,
`min`, `gte`, `greater_or_equal`), equal (`equals`, `equal`, `exact`), less than
or equal (`maximum`, `max`, `lte`, `less_or_equal`), greater (`greater`,
`minimum_exclusive`, `minex`), less (`less`, `maximum_exclusive`, `maxex`).
`roles` is reserved and meant to include an unordered list of roles for a future
role-based access control. `roles.operator` and `users.operator` are
combinatoric operators that are going to be applied to the user's MXID (`users`), or
user's roles and role limiting scope (`roles`) to evaluate whether the rate
limit applies to a given user. The valid combinatoric operators for roles are
`include_min({n})`, include at least `n` roles from the list,
`include_max({n})`, include at most `n` roles from the list, `include({m},{n})`,
include at least `m` and at most `n` roles from the list, `include({n})`,
include exactly `n` roles from the list, `exclude_min({n})`, exclude at least
`n` roles from the list, `include_only_min({n})`, include at least `n` roles
from the list and no others, `include_only_max({n})`, include at most `n` roles
from the list and no others, `include_only({m},{n})`, include at least `m`
and at most `n` roles from the list and no others, `include_only({n})`,
include exactly `n` roles from the list and no others, `exclude_min({n})`,
exclude at least `n` roles from the list, `exclude_max({n})`, exclude at
most `n` roles from the list, `exclude({m},{n})`, exclude at least `m`
and at most `n` roles from the list, `exclude({n})`, exclude exactly `n` roles
from the list. `all` is a placeholder representing all the roles in the list
and can be used as a parameter in those inclusion or exclusion operators.
The valid combinatoric operators for users are `include` and `exclude`.
Users having at least one of `limits.rate` or `limits` power can change
per-room rate limit.  However, all users can impose rate limits on oneselves,
and those self-imposed limits cannot be increased by other users above
the self-imposed values. Both `users` and `roles` parameters can be used,
in which case the applicable users is based on the union of the user set
based on user filtering and the user set based on the role filtering.

Applicable user set of the rate limit is then calculated as follows:
* A rate limiting event with both power level based filtering and role
based filtering (`power_level` and `roles` defined) at the same time
is rejected.
* If both `power_level` and `roles` are omitted and `users` are defined,
and `users.operator` is `exclude`, then the limit applies to all users,
except ones stated in the list.
* If `power_level` is defined, users are filtered according to `power_level`
and `power_level.operator`, then the `users` are added or subtracted from
that set according to `users.operator`.
* If `roles` is defined, the following rules apply:
* ** If `roles.operator` is an exclusion operator, then take the set of all
users and subtract users according to `roles.operator` according to `roles`
and the roles user possesses.
* ** If `roles.operator` is an inclusion operator, then start with empty set,
and add users according to `roles` listed and `roles.operator`.
* ** If `users` is also defined, then the `users` are added or subtracted
from the set calculated according to the abovementioned method, depending
on `users.operator`.
* For burst definitions, the same rules apply, except maximum applicable
user set is the set of users that are limited by the parent rate limit.

## Rate limit burst capability

Bursting can be defined using the `burst` property, which includes an array
of JSON objects, each defining a burst group over a base limit. Repeating
the above with bursting capabilities. Bursting coefficient `burst.coef` is
multiplied by base limit to calculate effective rate limit during the
burst period, for up to `burst.duration` seconds.

An example state event below (in the example below, both the power
level and roles are specified but normally those two will not appear
in the same time):

```json
{
   "type": "m.limits.rate.user",
   "power_level": 0,
   "power_level.scope": "maximum",
   "roles": [],
   "roles.operator": "exclude(all)",
   "limits": {"m.room.message": 123.4567, "m.ban": 1.234567},
   "burst": [
   {
   "burst.coef": 1.00,
   "burst.duration": 0,
   "users": [],
   "users.operator": "exclude",
   "roles": [],
   "roles.operator": "include_min(1)"
   }
   ]
}
```

## Potential issues

As **[@ara4n](https://github.com/ara4n)** said:

> However, implementation-wise, i'm a bit worried that different APIs will have
> different limiting thresholds depending on the room that they interact with 
> — and that the HS will have to query the room state every time someone says
> something to decide how limited they should be.

Rate limiting events themselves obeying the rate limits may make the limiting
logic pretty complex and cause a lower practical limit than allowed by the request.

## Alternatives considered

None considered yet.

## Security considerations

Possible rate limit request spams may cause both server-side and client-side
performance degradation.

## Unstable prefix

`m.limits.rate` should be replaced by `org.matrix.msc3059.rate`. And unstable API
endpoints should have `r0` replaced by `unstable` in the endpoint paths.
