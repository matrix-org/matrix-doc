# Proposal to allow overriding `m.room.power_levels` using `initial_state`
Bots and bridges that create rooms often want to override the initial power
levels. The spec defines a `power_level_content_override` field that is applied
on top of the default power levels for this purpose. However, that field can't
easily replace the entire default content, as it gets merged with the default
levels.

Synapse already allows replacing the entire power level event content by
placing a power level event in `initial_state`. However, interpreting the spec
literally means inserting the default power level event first, then inserting
the one from `initial_state`, which might not be possible due to auth rules
anymore.

## Proposal
The proposed solution is updating the room creation event order to specify that
a power level event in `initial_state` must be used to replace the default
content.

Specifically, the third point in the [/createRoom](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-createroom)
endpoint spec is updated to specify that `m.room.power_levels` events in the
`initial_state` list should be used to replace the default power event:

> 3. A default `m.room.power_levels` event, giving the room creator (and not
     other members) permission to send state events. If the `initial_state`
     list includes a `m.room.power_levels` event with an empty state key, that
     event replaces the default one entirely. Otherwise, the
     `power_level_content_override` parameter is applied on top of the default
     power levels to create the final content.

## Potential issues
Server implementations will have to separately check for `m.room.power_levels`
events in the `initial_state` list, which is slightly more effort than the
current flow.

## Alternatives
`power_level_content_override` can technically be used to undo everything in
the default power levels, but it's more convenient and intuitive if
`initial_state` can be used to simply replace the first power level event.

## Security considerations
None, as this doesn't change any event authorization or state resolution rules,
it just makes it more convenient to replace the default power level event.

## Unstable prefix
Probably not useful here, as there are no new fields and the behavior is
already implemented in Synapse.
