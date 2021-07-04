# MSC3125: Limits API — Part 5: per-Instance limits

Not all servers are as lucky as matrix.org to have variable scaling,
hence some of them will need to place growth limits on themselves,
and users and admins should be able to check and modify them in a
standardised way, and the servers should be able to communicate those
kinds of limits in a standardised way.

Coincidentially enough, the number of this MSC, 3125, is 5 to its 5th
power, in other words, 5 tetrated twice.

Note that there is no Part 4 yet — this proposal reserves that for
permanent room limits that are set at room creation time.

This MSC deals with kinds of limits that are intended to stop a home
server instance's growth beyond certain point.

## The basics

To modify a particular limit:
```
PUT /_matrix/client/r0/admin/limits/ HTTP/1.1
{
   "type": "m.limits.instance.event_cap",
   "value": 123456789
}
```
If `value` is not defined, then said limit is not defined.

The query will be made to the same paths, using the GET method instead.
And to delete the limit for the particular user, use the DELETE method
for the same path.

For now, three such per-instance limits are proposed:
*  Per-instance room limit: `m.limits.instance.room_cap` 
*  Per-instance user limit: `m.limits.instance.user_cap`
*  Per-instance event limit: `m.limits.instance.event_cap`
 *  Per-instance event-as-type limit: **TODO**

How those limits are going to be enforced is left implementation defined,
however, there are few sensible paths to take, such as kicking users from
larger rooms, or kicking larger rooms from the server, or simply stopping
processing events that violate the limit. The latter path may cause a room
to become split brained, however, if a need arises to intentionallly fork
a room, a server is free to choose that path.

## Per-instance room and user limiting semantics

Per-instance room limit defines how many rooms that a given instance can
join before it stops joining further rooms. The join requests will be
rejected, invites overturned and knocks ignored by the server. As soon
as the number of rooms server has joined drops below the limit, joins
will be processed as usual. Rooms with zero users do not count towards
this limit.

Per-instance user limits defines how many users can be served by a given
instance. Once the limit is exceeded, the server will accept no more
user additions in any manner. If there are more users than allowed when
the limit is put in place, then the latest joining users will be stopped
service first. Server administrators are also included in this count,
however, they shall be affected last during such enforcement.

## Per-instance event limiting semantics

Per-instance event limit defines how many events a given instance will
process before serving no further events. As soon as the event count
reaches the limit, no more events shall be processed. Event count limiting
events that only cover event count limiting events are ill-formed. Event
count limiting events themselves also count towards event count limits
if the relevant limiting event covers that limit, however, event count
limits shall not be checked for event count limiting events themselves.

## Potential issues

### Migration concerns

The servers may have to be restarted after implementing this the first
time, in order to track those limits correctly.

### Misconfiguration mishap

Misconfiguring those limits might make the server instance unable to
serve the user base that instance targets.

## Alternatives

No alternatives considered yet.

## Security considerations

Unintentional denial of service by service by server administrators.

## Unstable prefix and endpoints

`m.limits.instance` should be replaced by `org.matrix.msc3125.instance`
and the `r0` in the API endpoint paths should be replaced by `unstable`.
