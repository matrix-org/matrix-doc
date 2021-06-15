# MSC2249: Require users to have visibility on an event when submitting reports

The [report API](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-rooms-roomid-report-eventid)
currently does not require users to be joined to the room in order to report that an
event is inappropriate. This allows anyone to report any event in any room  without being joined to the room.
There is limited use (and scope for abuse) for users to call report on rooms they are not joined to,
so this proposal requires that reporting users must be joined to a room before they can report an event.

Furthermore this proposal addresses the case where the user may not have visibility
on an event (e.g. not being able to read history in a room).

In that case, similar logic applies as described below.

## Proposal

The `/rooms/{roomId}/report/{eventId}` endpoint should check to see if the authenticated user
is joined to the room in the current state of the room. If the user is not joined to the room OR
the room does not exist, the server should respond with:

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "The room does not exist, or you are not joined to the room."
}
```

where the contents of `error` can be left to the implementation. It is important to note that this response
MUST be sent regardless if the room exists or not as this endpoint could be used as a way to brute
force room IDs in order to find a room.

If the user is joined to the room, but the event doesn't exist on the homeserver OR the user doesn't have permission to see
the event then the response should be:

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "The event does not exist, or you do not have permission to see it."
}
```

It is not expected for homeservers to attempt to backfill an event they cannot find locally, as the user is unlikely to
have seen an event that the homeserver has not yet stored.

If the event is redacted, reports MAY still be allowed depending on the implementation. There is an argument that
a redeacted event should still be reportable as even deleted abusive content was harmful at a point.


## Tradeoffs

None

## Potential issues

This will incur a performance penalty on the endpoint as the homeserver now needs to query state in the room, however
this is considered acceptable given the potential to reduce abuse of the endpoint.

## Security considerations

Care should be taken not to give away information inadvertently by responding with different error codes depending
on the existence of the room, as it may give away private rooms on the homeserver. This may be somewhat unavoidable
due to the time delay for checking the existence of a room vs checking the state for a user, so implementations
MAY decide to "fuzz" the response times of the endpoint to avoid time-based attacks.
## Conclusion

This proposal should hopefully reduce the abuse potential of the /report endpoint without significantly increasing
the complexity or performance requirements on a homeserver.
