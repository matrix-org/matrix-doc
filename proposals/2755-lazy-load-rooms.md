# MSC2755: Lazy load rooms

[MSC1227](https://github.com/matrix-org/matrix-doc/issues/1227) added lazy
loading of member events to the spec. This was done because member events can
severly outnumber other events in matrix. Alternatively to that MSC, lazy
loading rooms was also explored, but not followed up on, as lazy loading members
promised most of the benefits. It was however mentioned, that lazy
loading/paginating rooms would be othogonal to lazy loading members and the
former could be explored at a later point. This has not been done so far, but
this MSC wants to change that.

One of the issues with lazy loading members is, that this only scales in one
direction. If you have a thousand DMs, lazy loading members will not show many
benefits. Similiarly this does not address other state events, that may bloat a
room state. One example of that is #TWIM:matrix.org, which has a state event
approaching 64kb. In theory there is no limit to the number of those state
events, which can infinitely increase a rooms size. Lazy loading members also
requires the server to iterate all rooms and the initial /sync response will
have to be at least include every room, which may be the entire memory budget an
embedded client has (like a 3DS for example).

Paginating or lazy loading rooms can provide an additional toggle to reduce CPU
overhead and decrease memory usage for clients and servers when receiving
initial state or incremental updates over /sync.

## Proposal

An additional key, `room_limit_by_complexity`, is added to the RoomFilter, which
can be specified directly on `/sync` or used as a stored filter for `/sync`.
This is an approximate limit for the number of rooms returned by `/sync`. You
should specify a positive integer as the value for that key. This integer limits
how many DM size rooms are returned in each `/sync` response. If a room is
bigger than a normal DM, fewer rooms should be returned proportional to their
size. I.e. if the limit is 5, you should only return 5 DMs or one giant room. If
you have rooms that are somewhat in between, a server may return any number of
rooms up to the specified maximum in an implementation defined manner, where the
response is approximately the size of 5 DM rooms.

If the response was limited by the room count filter, the server should set the
`rooms.limited` field to true. Otherwise that field should not be sent. If a
client receives a limited response, it can call `/sync` with the next batch
token to receive the (updates in) other rooms.

A server should also apply this filter on incremental syncs. If there is a big
gap between syncs, which can happen, when a client was offline for a long time,
there may be a lot of state changes in a room. For example the IRC bridge could
have kicked a few hundred users across a few rooms. Lazy loading would still
require these events to be sent in the incremental sync. This proposal would
expect the server to only return a few rooms and set the `rooms.limited` flag to
`true`.

This has also the nice benefit, that initial sync should return a lot faster and
the room list should fill incrementally, giving some feedback to the user, that
the sync is still in progress and actually doing something.

This should not need changes to any endpoint but `/sync` and the filter
endpoints.

## Potential issues

- The metric for the room number limit is intentionally mushy defined. This may
    lead to server implementations choosing bad tradeoffs and returning a lot of big
    rooms at once. In my opinion servers implementers may have different ways to
    collect what rooms to return on `/sync`. This intentionally leaves them some
    leeway to do "what they think is best". A server being too agressive or not
    aggressive enough in limiting rooms should be considered a quality of
    implementation issue, not a strict spec violation. If this turns out to be an
    issue, the spec could be fixed up to be stricter.

- This proposal gives client no explicit control over the size of the `/sync`
    response. This may still cause issues on embedded clients, where RAM is limited.
    I think this MSC is not enough to allow such a toggle. You also need a way to
    paginate arbitrary state in a room. If such a toggle is provided, one could
    imagine a toggle with an absolute response size (in kB or similiar), that
    enables lazy loading rooms, members and state at once. Until then, we have to
    hope, that a single room will always fit into memory, when lazy loading of
    members is also enabled.

- With this proposal and the feature being enabled, you will not have all rooms
    returned in a single call to `/sync`. If a client doesn't want that, they
    simply shouldn't enable this feature.

- This feature adds additional complexity to `sync`, which will also need to be
    encoded into the sync token or otherwise kept track of. This may not be
    very maintainable.

## Alternatives

- The limit for the sync response could be specified in an absolute byte size,
    which would limit the count of rooms returned by their size. (Return as many
    rooms as fit inside the limit or a single room.) I think it is too hard for
    client developers to eastimate, how big a room would be in bytes, so they may
    only get one room in each sync request. On the other hand it would make response
    size a lot more predictable. I think to allow such a toggle, you should also be
    able to paginate state. So this is out of scope for now, providing a simpler way
    to limit the response size.

- You may want to limit the state returned in each room more. In my opinion the
    use of that is somewhat limted, when you already lazy load members.  Limiting
    the state by returning less rooms sounds more useful for now. This proposal
    does not prevent paginating state in the future.

- One could also implement paginating rooms differently, where a client actually
    never gets to see all rooms unless requested, which would be a lot more
    similar to how lazy loading members works. I would argue that this would
    degrade the experience a lot, since the room list in most clients is a very
    central piece, while the full member list of a room is usually not that
    front and center and only visible, when viewing that specific room.

## Security considerations

I don't think this has any obvious security implications.

## Unstable prefix

Keys introduced in this MSC should use `im.nheko.msc2755` as a prefix:
`im.nheko.msc2755.room_limit_by_complexity` in the filter and
`im.nheko.msc2755.limited` inside the rooms key.
