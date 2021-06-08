# MSC2880: extend event and state API to allow sending to all rooms
`amsg` is a command, available in some IRC clients, to send a message to all available IRC rooms that the user has access to.
`astate` is a similar idea for state events.
## Potential uses
* Custom fields in member events in all rooms, without setting them individually
* Banning a user from all rooms you can easily (for moderation)
* Emergency announcements, to all your friends and family members
* Sending empty events to all rooms to prevent being kicked for inactivity
## Proposal
The client-server API is extended by allowing the `roomId` in API calls to send events to a room to be the special value of `*`.

For example, state would be sent to all rooms by using the API
`PUT rooms/*/state/{eventType}/{stateKey}`
and normal messages would be sent by doing
`PUT rooms/*/send/{eventType}/{txnId}`

The API response would be extended to be a dictionary of responses for each room the event is sent to, such as follows.
```json
{
  "!jPONbbbkNqNujFyVcz:matrix.org": "$N9wG08xHjNXaUnQMfAyDxAxKC_eL7r_MU4jPElxph5s",
  "!UjcEvNndgssKYbZSeJ:blob.cat": "$OTTx39SwYdVYN6A-NL703dK7QuwIyiB-OOHunpxt8X0"
}
```
## Implementation details
### Servers
Servers should only send events to rooms where the client is authorized to send an event to, and should not return `M_FORBIDDEN` due to the user not being allowed to send events to certain rooms.

Servers may want to strictly rate-limit the API to prevent spamming and high resource use.
### Clients
Clients may want to warn users when sending an `amsg` or `astate` to avoid accidental spamming.
## Notes
A similar functionality in servers already exists for `PUT profile/{userId}/displayname` and `PUT profile/{userId}/avatar_url`.
