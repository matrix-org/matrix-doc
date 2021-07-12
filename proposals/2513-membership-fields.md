# Abstract channel for fields in Membership Events

This proposal reconciles the several surfaces available to clients for
updating room membership by providing a forward-compatible mechanism
to channel current and future features.

Currently there are two primary vectors for clients to mutate room memberships:
1. Manual `content` generation via
[PUT /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-rooms-roomid-invite)
2. Assisted `content` generation via the specific rich-endpoint interface in
[CS-r0.6.0-10.4.2](https://matrix.org/docs/spec/client_server/r0.6.0#joining-rooms),
[CS-r0.6.0-10.4.3](https://matrix.org/docs/spec/client_server/r0.6.0#leaving-rooms), and
[CS-r0.6.0-10.4.4](https://matrix.org/docs/spec/client_server/r0.6.0#banning-users-in-a-room),

## Problem

The rich interface cited by the above option 2 is not extensible. For example
in  [POST /_matrix/client/r0/rooms/{roomId}/invite](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-rooms-roomid-invite) the
only specified *Body Parameters* is `user_id`. The property `user_id` does
not itself appear in membership event `content` thus servers must refrain from
simply passing unrecognized top-level *Body Parameters* into the generated
content. Future *Body Parameters* may be specified to be private material
or require server-side mutation; this prevents forward-compatibility due to
lack of any current specification.

[MSC2367](https://github.com/matrix-org/matrix-doc/pull/2367) is exemplary,
it specifies a `reason` property in `m.room.member`
of all `content.membership` flavors to be recognized by software. In order
to implement [MSC2367](https://github.com/matrix-org/matrix-doc/pull/2367),
and future proposals of that nature, client and server
software must both support each such new enumerated property, or the feature
will be ineffective. Prudent client developers are thus forced to make use
of the above option 1 in all cases, for example with Riot's `/myroomnick`
and `/myroomavatar` features, which make use of
[PUT /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-rooms-roomid-state-eventtype-statekey).
This exemplifies a relegation of the rich interface into perpetual obsolescence.

## Solution

Allow `content` property to be specified in *Body Parameters* for all of the
following APIs:

```
POST /_matrix/client/r0/rooms/{roomId}/invite
POST /_matrix/client/r0/rooms/{roomId}/leave
POST /_matrix/client/r0/rooms/{roomId}/kick
POST /_matrix/client/r0/rooms/{roomId}/ban
POST /_matrix/client/r0/rooms/{roomId}/unban
POST /_matrix/client/r0/rooms/{roomId}/join
POST /_matrix/client/r0/join/{roomIdOrAlias}
```

If specified the `content` property will be synthesized into the generated
membership event's `content`. Server software will place a lower precedence
on client-proffered properties to those otherwise specified, but will
abstractly convey all other properties into the generated membership event's
`content`.

## Discussion

This proposal does not deprecate MSC2367 as the sanction of `content.reason`
in `m.room.member` events of all flavors is ideally specified. However, this
proposal does option that if MSC2367 is not yet integrated, its property is
moved from the top-level `reason` into `content.reason` for cleanliness of
the API surface. This proposal also requests that all future features which
involve a direct-entry in generated `m.room.member` event `content` are
channeled through the specified `content` *Body Parameters*.
