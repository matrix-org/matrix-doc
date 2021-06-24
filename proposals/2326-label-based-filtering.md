# Label based filtering

## Problem

Rooms often contain overlapping conversations, which Matrix should help users
navigate.

## Context

We already have the concept of 'Replies' to define which messages are responses
to which, which [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849)
proposes extending into a generic mechanism for defining threads which could (in
future) be paginated both depth-wise and breadth-wise.  Meanwhile,
[MSC1198](https://github.com/matrix-org/matrix-doc/issues/1198) is an alternate
proposal for threading, which separates conversations into high-level "swim
lanes" with a new `POST /rooms/{roomId}/thread` API.

However, fully generic threading (which could be used to implement forum or
email style semantics) runs a risk of being overly complicated to specify and
implement and could result in feature creep. This is doubly true if you try to
implement retrospective threading (e.g. to allow moderators to split off
messages into their own thread, as you might do in a forum or to help manage
conversation in a busy chatroom).

Therefore, this is a simpler proposal to allow messages in a room to be filtered
based on a given label in order to give basic one-layer-deep threading
functionality.

## Proposal

We let users specify an optional `m.labels` field onto the events. This field
lists freeform text labels:

```json
{
  // ...
  "m.labels": [ "somelabel" ]
}
```

The labels are expected to be insensitive to case, therefore clients are
expected to lowercase them before sending them to servers. A label's length is
limited to a maximum of 100 characters.

Labels which are prefixed with # are expected to be user-visible and exposed to
the user by clients as a hashtag, letting the user filter their current room by
the various hashtags present within it. Labels which are not prefixed with # are
expected to be hidden from the user by clients (so that they can be used as
e.g. thread IDs bridged from another platform).

A label can contain any UTF-8 character, regardless of whether it starts with a
hash or not (i.e. we don't limit the hashtag to e.g. the set of allowed
characters in a Twitter hashtag, and not-hashtag-like labels also don't have
that sort of constraints).

Clients can use these to filter the overlapping conversations in a room into
different topics. The labels could also be used when bridging as a hashtag to
help manage the disconnect which can happen when bridging a threaded room to an
unthreaded one.

Clients are expected to let users add hashtag-like labels to a message before
sending it, and to display hashtag-like labels on messages to help user easily
identify the labels they can make their client filter on.

Clients are expected to explicitly set the label on a message if the user's
intention is to respond as part of a given labelled topic. For instance, if the
user is currently filtered to only view messages with a given label, then new
messages sent should use the same label. Similarly if the user sends a reply to
a given message, that reply should typically use the same labels as the message
being replied to.

When a user wants to filter a room to given label(s), it defines a filter for
use with `/sync`, `/context`, `/search` or `/messages` to limit appropriately.
This is done by new `labels` and `not_labels` fields to the `EventFilter`
object, which specifies a list of labels to include or exclude in the given
filter.

Senders may edit the `m.label` fields in order to change the labels associated
with an event. If an edit removes a label that was previously associated with
the original event or a past edit of it, neither the original event nor an edit
of it should be returned by the server when filtering for events with that
label.

When editing the list of labels associated with an encrypted event, clients must
set the updated list of labels in the `content` field of the encrypted event in
addition with the `m.new_content` field of the decrypted event's `content`
field, so that servers can update the list of labels associated with the
original event accordingly.

When sending an edit of an event that has labels attached to it, clients are
expected to provide a list of labels, even if the edit doesn't add or remove any
label from the list provided in the original event or its latest edit (in this
case, the list is the same as the one provided in the original event or its
latest edit).

### Encrypted rooms

In encrypted rooms, the `m.label` field of `m.room.encrypted` events contains,
for each label of the event that's being encrypted, a SHA256 hash of the
concatenation of the text label and the ID of the room the event is being sent
to, i.e. `hash = SHA256(label_text + room_id)`.

The reason behind using a hash built from the text label and the ID of the room
here instead of e.g. a random opaque string or a peppered hash is to maintain
consistency of the key without having access to the entire history of the room
or exposing the actual text of the label to the server, so that e.g. a new
client joining the room would be able to use the same key for the same label as
any other client. See the ["Alternative solutions"](#alternative-solutions) for
more information on this point.

When filtering events based on their label(s), clients are expected to use the
hash of the label(s) to filter in or out instead of the actual label text.

#### Example

Consider a label `#fun` on a message sent to a room which ID is
`!someroom:example.com`. Before encryption, the message would be:

```json
{
  "type": "m.room.message",
  "content": {
    "body": "who wants to go down the pub?",
    "msgtype": "m.text",
    "m.labels": [ "#fun" ]
  }
}
```

`3204de89c747346393ea5645608d79b8127f96c70943ae55730c3f13aa72f20a` is the SHA256
hash of the string `#fun!someroom:example.com`. Here's an example code
(JavaScript) to compute it:

```javascript
label_key_unhashed = "#fun" + "!someroom:example.com"
hash = crypto.createHash('sha256');
hash.write(label_key_unhashed);
label_key = hash.digest("hex"); // 3204de89c747346393ea5645608d79b8127f96c70943ae55730c3f13aa72f20a
```

Once encrypted, the event would become:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "AwgAEpABm6.......",
    "device_id": "SOLZHNGTZT",
    "sender_key": "FRlkQA1enABuOH4xipzJJ/oD8fxiQHj6jrAyyrvzSTY",
    "session_id": "JPWczbhnAivenK3qRwqLLBQu4W13fz1lqQpXDlpZzCg",
    "m.labels": [
      "3204de89c747346393ea5645608d79b8127f96c70943ae55730c3f13aa72f20a"
    ]
  }
}
```

## Problems

Do we care about internationalising hashtags?

Too many threading APIs?

Using hashes means that servers could be inclined to compute rainbow tables to
read labels on encrypted messages. However, since we're using the room ID as
some kind of hash, it makes it much more expensive to do because it would mean
maintaining one rainbow table for each encrypted room it's in, which would
probably make it not worth the trouble.

## Alternative solutions

Instead of using hashes to identify labels in encrypted messages, using random
opaque strings was also considered. Bearing in mind that we need to be able to
use the label identifiers to filter the history of the room server-side (because
we're not expecting clients to know about the whole history of the room), this
solution had the following downsides, all originating from the fact that nothing
would prevent 1000 clients from using each a different identifier:

* filtering would have serious performances issues in E2EE rooms, as the server
  would need to return all events it knows about which label identifier is any
  of the 1000 identifiers provided by the client, which is quite expensive to
  do.

* it would be impossible for a filtered `/message` (or `/sync`) request to
  include every event matching the desired label because we can't expect a
  client to know about every identifier that has been used in the whole history
  of the room, or about the fact that another client might suddenly decide to
  use another identifier for the same label text, and include those identifiers
  in its filtered request.

Another proposed solution would be to use peppered hashes, and to store the
pepper in the encrypted event. However, this solution would have the same
downsides as described above.

## Security considerations

The proposed solution for encrypted rooms, despite being the only one we could
think of when writing this proposal that would make filtering possible while
obscuring the labels to some level, isn't ideal as it still allows servers to
figure out labels by computing [rainbow
tables](https://en.wikipedia.org/wiki/Rainbow_table).

Because of this, clients might want to limit the use of this feature in
encrypted rooms, for example by enabling it with an opt-in option in the
settings, or showing a warning message to the users.

It is likely that this solution will be replaced as part of a future proposal
once a more fitting solution is found.

## Unstable prefix

Unstable implementations should hook up `org.matrix.labels` rather than
`m.labels`. When defining filters, they should also use `org.matrix.labels` and
`org.matrix.not_labels` in the `EventFilter` object.

Additionally, servers implementing this feature should advertise that they do so
by exposing a `org.matrix.label_based_filtering` flag in the `unstable_features`
part of the `/versions` response.
