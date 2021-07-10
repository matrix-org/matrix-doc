# MSC2771: Message Bookmarks

Matrix is currently lacking a feature to bookmark events as a user to provide a way of easy finding
important messages without needing to know a search term. This proposal aims to provide browser or TODO list alike
bookmarks.

## What sets this apart from other Proposals that are similar (like Pinning and MSC2437)?

For "Pinning" this might be obvious but pinning is something that all users in a room see. So if you pin a message 
all users will see that pinned message at the top in riot. While this can be used as bookmarks it doesn't work in 
rooms like #matrix:matrix.org where you might want to remember an event (for example a link to a guide) and others 
might not need to remember this event. Therefore the usage of pinned events does not work very well.

On the other side of similar MSCs is the MSC2437 which allows hashtag alike tagging of events. This allows to search 
events by topics or displays them based on their topic. You might think that bookmarks would work with this (and they 
might) but this Proposal wants to also cover the specifics of bookmarks and is more aimed to be alike browser bookmarks 
and allows not only marking as bookmarks but also aims to give it some bookmark specific metadata.

## Proposal

Bookmarks are selected by a User on an Event. This means a user can select an event and add it to the bookmarks.
The bookmark event inside of the account data is used for clients to keep track of bookmarked events.

The bookmarks are saved with the type `m.bookmarks`.

It is being saved inside of the rooms account data

```json
{
  "events": [
    {
      "event_id": "$12345:example.com",
      "title": "Food Choice",
      "comment": "I need to buy stuff for this"
    }
  ]
}
```

## Alternatives

Instead of using the room account data, it would be possible to save this in the global account data.
This would be similar to `m.direct`.

```json
{
  "!12345:example.com": [
    {
      "event_id": "$67890:example.com",
      "title": "Wood Choice",
      "comment": "I need to buy stuff for this"
    }
  ],
  "!67890:example.com": [
    {
      "event_id": "$12345:example.com",
      "title": "Food Choice",
      "comment": "I need to buy stuff for this"
    }
  ]
}
```

## Potential issues

None