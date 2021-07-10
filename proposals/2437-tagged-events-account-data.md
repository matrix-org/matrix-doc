# MSC2437: Store tagged events in Room Account Data

We want here to let the users tag some room events. 

The first use case would be to let him mark some events as favorites to keep a
reference on important messages or attachments. Clients would then be able to
handle a global bookmark of these favourite events, or display a list of them
at the room level.

A second use case would be to hide/ignore some events in order to prevent their
display in the room history.

The proposal provides a model to store the tagged events in the room account
data. The room account data has been preferred to the global account data in
order to remove/forget the potential tagged events when the user leaves a room.

## Proposal

Define `m.tagged_events` event type to store the tagged events of a room in
the room config. Clients will then set or get this account data content thanks
to the following APIs:

```
PUT /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/m.tagged_events
GET /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/m.tagged_events
```

The content of this event is a `tags` key whose value is an object mapping the
name of each tag to another object.
The JSON object associated with each tag is an object where the keys are the
event IDs and values give information about the events.
The event information are given under the following fields:

* `keywords` (`[string]`) - A list of words which should describe the event,
 useful for searching or viewing favourite events without decrypting them.
* `origin_server_ts` (`integer`) - The timestamp in milliseconds on originating
 homeserver when this event was sent, useful to sort chronologically the events
 (without retrieving the full description of the event).
* `tagged_at` (`integer`) - The timestamp, in milliseconds, when the event was
 tagged, useful to view the most recent tagged events

These fields are optional. The value may be an empty object if no fields are
defined.

The name of a tag MUST NOT exceed 255 bytes.

The tag namespace is defined as follows:

  * The namespace `m.*` is reserved for tags defined in the Matrix specification.
   Clients must ignore any tags in this namespace they don't understand.
  * The namespace `u.*` is reserved for user-defined tags. The portion of the
   string after the `u.` is defined to be the display name of this tag. No other
   semantics should be inferred from tags in this namespace.
  * A client or app willing to use special tags for advanced functionality
   should namespace them similarly to state keys: `tld.name.*`
  * Any tag in the tld.name.* form but not matching the namespace of the current
   client should be ignored.
  * Any tag not matching the above rules should be ignored.
  
Two special names are listed in the specification: The following tags are
defined in the `m.*` namespace:

  * `m.favourite`: The user's favourite events in the room.
  * `m.hidden`: The events that the user wants to hide from the room history.

Example of content:

```
{
    "tags": {
        "m.favourite": {
            "$143273582443PhrSn:example.org": {
                "keywords": [
                  "pets",
                  "cat"
                ],
                "origin_server_ts": 1432735824653,
                "tagged_at": 1432736124573
            },
            "$768903582234ttROC:example.org": {
                "keywords": [
                  "pets",
                  "dog"
                ],
                "origin_server_ts": 1432735825701,
                "tagged_at": 1432735923671
            },
            "$7623459801236vBDSF:example.org": {
                "origin_server_ts": 1432736234980,
                "tagged_at": 1432736512898
            }
        },
        "m.hidden": {
            "$123765582441goFrt:example.org": {
                "keywords": [
                  "out of topic"
                ],
                "origin_server_ts": 1432735824700,
                "tagged_at": 1432735825123
            },
            "$619203608012ttAZw:example.org": {},
            "$423567908022kJert:example.org": {},
            "$456765582441QsXCv:example.org": {
                "keywords": [
                  "spamming"
                ]
            }
        },
        "u.personal": {
            "$903456781253Hhjkl:example.org": {
                "keywords": [
                  "vacation",
                  "London"
                ],
                "origin_server_ts": 1432735824667,
                "tagged_at": 1432735857890
            }
        }
    }
}
```

The benefits to provide the `origin_server_ts` for the favourite events is to
let clients filter/sort them without having to retrieve the full content of
the events. Thanks to this timestamps, clients may ignore the favourite events
which are outside the potential room retention period, or display them as
expired events.
Clients must be ready to handle the case where a favourite event has been
redacted.

About the hidden events, clients must hide these events from the room history.
The event information don't seem very useful. We have provided some of them as
example.

## Limitation
Given that clients have to encode the complete set of tagged events to add,
remove or modify one entry, it might happen that different clients overwrite
each other modifications to the tagged events.

This is a known limitation for any new event type added to the `account_data`
section of a room, or to the top-level `account_data`. For example, we already
suffer from it to handle the `m.direct` event type.

This limitation has been addressed for only one case: the room tagging. Indeed
a set of endpoints have been defined for the corresponding event type `m.tag`.
Here is the existing APIs for this feature: 

```
GET /_matrix/client/r0/user/{userId}/rooms/{roomId}/tags
PUT /_matrix/client/r0/user/{userId}/rooms/{roomId}/tags/{tag}
DELETE /_matrix/client/r0/user/{userId}/rooms/{roomId}/tags/{tag}
```

Should we consider this approach for any new event type?
Another suggestion has been provided during the review: We could provide
account data endpoints to append and remove values to an array in a specific
account data value, something like:

```
PUT /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/<type>/append
DELETE /_matrix/client/r0/user/{userId}/rooms/{roomId}/account_data/<type>/index/4
```

For the `DELETE` method, you'd need some kind of `ETag` value to pass as an
`If-Match` header so avoid deleting an indexed that is out of date because of
other clients deleting an index as well. Perhaps the server could add some kind
of unique tag to the account data value when it is updated.

We mentioned here the discussion about this limitation to keep it in our mind.
This should be the subject of another proposal.
