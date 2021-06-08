MSC3032: Thoughts on updating presence
======================================

This is deliberately a loose-form, draft MSC to note down my current thoughts
on how we might improve the presence system and integrate it with
profiles-as-rooms (MSC1769).

## `PUT /_matrix/client/r0/presence/{userId}/status`
`status_msg` becomes deprecated. In it's place there's a new state event in the
user's MSC1769 profile room, `m.status`. It's not a field in the `m.profile`
object because it's intended to be updated fairly frequently and we don't need
to update the whole profile each time (this would be inefficient and risk data
races).

`presence` stays, with the additional value of `busy` as per MSC3026, but this
endpoint is explicitly for the *user* setting their presence manually, eg. selecting
'busy' or 'unavailable' from a checkbox in the UI.

## `set_presence` in `/sync`
This is differentiated from `PUT /_matrix/client/r0/presence/{userId}/status`
by being explicitly for automatic updates from clients, eg.:
 * A client supplies `unavailable` if it doesn't believe the user is paying attention
   (eg. they haven't moved the mouse ina  while).
 * A client supplies `busy` if the user is on a call in that client.

## Effective presence
The homeserver can then combine the multiple sources of presence information from
the clients and the user-set value to determine an effective presence for the user.
This is a black-box as far as the spec is concerned, but semantics will be along
the lines of 'if any status is busy, the user is busy'.

Question: if a user sets themselves 'busy', what status do they set when they're
free again? 'online'?

## Publishing presence
Homeservers take the effective presence and publish it as an `m.presence` state
event in the user's profile room. You subscribe to a user's presence by peeking
into their profile room.

m.presence events go away entirely after some deprecation period.

Question: How would we restrict the set of people allowed to see presence
   info (ie. assuming we allow a wider set of people to see the user's profile)
Question: What happens if a user send an `m.presence`event to their profile room?
          Should they be allowed to?

## `GET /_matrix/client/r0/presence/{userId}/status`
Also goes away.

## Presence for the smartphone generation
The presence status enum was designed in a time when smartphones were relatively
new and it was still assumed that if you weren't at your computer, you were
unavailable. This isn't true now we all carry our computers in our pockets.
This probably requires only a small change in how we interpret the values though:
 * `online`: Actively using a client right this moment
 * `unavailable`: No particular status / default. It's assumed the user may be
   available and respond if you message them, or maybe not.
 * `busy`: Unavailable to talk.
 * `offline`: It should be assumed that messages won't reach the user.
