# MSC3060: Room labels

Currently, the only allowed way in Matrix to advertise information about a room
is through its name, avatar and topic, which can feel a bit limiting (a room's
name is usually expected to be very short and isn't always very descriptive, and
a room's topic is usually where one would find related social media accounts or
the room's rules/code of conduct).

On top of that, room names and topics are expected to be human-readable, which
makes it difficult to use them for automation. One example of necessary
automation that client developers might want to implement would be to filter out
rooms allowing or dedicated to NSFW (Not Safe For Work, i.e. erotic or
pornographic) content from the public room directory. Apple actually requires
any application to be able to filter out such content in order to be accepted on
their App Store.

## Proposal

### `m.room.labels` state event

A new state event is defined, with the type `m.room.labels`. Its content
includes an array of freeform strings used to describe the room and its
discussions:

```json
{
  "type": "m.room.labels",
  "content": {
    "labels": [
      "archlinux",
      "linux",
      "support",
    ]
  },
  [...]
}
```

A label is expected to be fairly short, and to designate only one concept,
therefore each label is limited in size to 35 characters and can contain only
one word (a word being defined as a string containing any character except for a
space (` `)).

As a sidenote for context, the length of 35 characters is based on the allowed
length for a topic on a GitHub repository (since the semantics of GitHub topics
are very similar to the ones described here).

Room labels appear in responses to `/publicRooms` requests, alongside other
metadata for the room (member count, name, address, etc.).

### `m.nsfw` room label

A label is also defined, `m.nsfw`. Room admins must use this label to express
that they're open to NSFW content being shared in the room. Clients can use this
label to filter rooms allowing NSFW content out of the room list if needed or
desired.

Clients must display all room labels as defined, except for `m.nsfw`, which can
also be displayed as the string `nsfw` or any case variant.

## Alternatives

An alternative to advertise topics could be through a modified
[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) (to allow multiple
types for a given room), however the semantics for room types (how the room
should be used by clients) are fairly different to those of labels (how the room
should be used by humans).

## Unstable prefix

Until the feature described in this proposal is merged into the Matrix
specification, implementations must use the unstable prefix
`org.matrix.msc3060.labels` instead of `m.room.labels`.
