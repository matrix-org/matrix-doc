# MSC2314: Backfilling Current State

If a server experiences data loss, it is difficult for it to recover membership
in federation without having a user be reinvited, as backfill alone can not
easily retrieve the data that is required to operate in a room (namely the
current state and auth chain).

This MSC introduces S2S APIs to provide a given room's auth chain and current
state events, provided the requesting server is in the room specified.

## Existing APIs

If one knows the room ID and an event ID,
`/_matrix/federation/v1/state/{roomId}?event_id={eventId}` can be used to
retrieve the auth chain and current state events for that given event. However,
this requires knowing an event ID (which cannot be assumed), as well as the
version of the room (which can be assumed to be contained within the current
state delivered). If an event arrives for a room that a Matrix server does not
know about, the event ID could be used to backfill the state, but this is
impractical for rooms which may be low-traffic yet valuable to the end-user
(such as direct messages).

## Proposal

Make the `eventId` parameter to `/v1/state/{roomId}` optional, and return the
room version to ease the parsing of the given events. If the `eventId` parameter
is not given, the receiving server is to instead use what it considers the
room's current state. If `eventId` is not provided, `room_version` in the
response becomes mandatory.

```
GET /_matrix/federation/v1/state/{roomId}

{
  "room_version": "3",
  "auth_chain": [
    {
      "type": "m.room.minimal_pdu",
      "room_id": "!somewhere:example.org",
      "content": {
        "see_room_version_spec": "The event format changes depending on the room version."
      }
    }
  ],
  "pdus": [
    {
      "type": "m.room.minimal_pdu",
      "room_id": "!somewhere:example.org",
      "content": {
        "see_room_version_spec": "The event format changes depending on the room version."
      }
    }
  ]
}
```

## Potential issues

Although the creating server is part of the room ID, a server using this API as
a client may find that the target server does not presently know about the room
(for example, it has been shut down or deleted). Finding servers that will
successfully return results from this API is outside of the scope of this MSC.

Users may not know the room ID for a given room, only a room alias. Translating
this alias into a room ID is outside of the scope of this MSC. Users of this API
may want to use it in conjunction with `/_matrix/federation/v1/query/directory`
to resolve aliases to room IDs as part of an end-user focused API.

Excessively large rooms may cause performance problems for servers implementing
this API (including in its v1 incarnation). Discretionary rate limiting of this
API may be required.

## Security considerations

In the case of a domain-name hijack, this may make recovering rooms that the
domain name was in easier. However, since a domain name hijack will lead to
other servers potentially sending PDUs with the required event IDs to allow
backfill and state querying, this does not constitute a meaningful increase in
attack surface. Proposals such as MSC1228 are expected to mitigate.
