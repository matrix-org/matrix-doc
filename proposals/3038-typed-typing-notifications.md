# MSC3038: Typed Typing Notifications

Typing notifications in Matrix currently support a single boolean value of typing or not typing. While
this works for most use cases (text chat specifically), it is not always applicable when sending more
complicated data types like voice messages.

This MSC extends the existing typing notification structure to support metadata about the event the
user is sending. All of the metadata is optional.

For reference, a typing notification currently looks something like this:

```json5
{
  "content": {
    "user_ids": [
      "@alice:matrix.org",
      "@bob:example.com"
    ]
  },
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "type": "m.typing"
}
```

## Proposal

A new, optional, `event` field is added to the `PUT` body of 
[`/rooms/:roomId/typing/:userId`](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-typing-userid)
which represents the event the user is working on sending. A new `PUT` body may look like:

```json5
{
  "typing": true,
  "timeout": 33038,
  "event": {
    "type": "m.room.message",
    "content": {
      "msgtype": "m.text"
    }
  }
}
```

The `event` is a stripped-down version of a real event, indicating the `type` and relevant parts of 
the `content` to be included. This does technically allow a client to also send partial events such
as the event body, however this MSC strongly advises that clients do not send or render that information
due to the privacy implications. See the "Security Considerations" section for more information.

For a `type` of `m.room.message`, The default `content.msgtype` is `m.text`. Similarly, when no
`event` information is supplied, the user can be assumed to be sending a `m.text` `m.room.message`
event. The server should reject any invalid fields (wrong data types, unexpected locations, etc),
though clients are ultimately responsible for parsing the data safely. 

The ephemeral event a client would receive could look something like this:

```json5
{
  "content": {
    "user_ids": [
      "@alice:matrix.org",
      "@bob:example.com"
    ],
    "events": {
      "@alice:matrix.org": {
        "type": "m.room.message",
        "content": {
          "msgtype": "m.voice"
        }
      }
    }
  },
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "type": "m.typing"
}
```

In this example, `@alice:matrix.org` is recording a theoretical voice message while `@bob:example.com`
is typing a regular text event (the default). If the receiving client doesn't recognize the event
Alice is trying to send, for example, then the client would assume that they are sending a regular
text event or use generic language like "Alice is sending something...".

The `events` object is not required. Clients should interpret invalid data (wrong data types, missing
fields, etc) as though users are typing text messages. Users who are *not* listed in `user_ids`
should not show up in the `events` object, and clients should ignore any updates for users who are
not in the `user_ids` array.

Like with typing notifications currently, a user can send `typing: false` at any time to stop typing.
Changing the `event` information being sent replaces any previous state, including removal of `event`
from the `PUT` body.

For example:

1. User hits `PUT /typing` with `{"typing": true, "event": {"type": "m.room.message"}}`
2. Other users see them as typing a text message.
3. The same user hits `PUT /typing` with `{"typing": true, "event": {"type": "org.example.msg"}}` this time.
4. Other users see them as typing an `org.example.msg` event.
5. The same user once again hits `PUT /typing` with `{"typing": true}`
6. Other users now see them as typing a text message again
7. Finally, the user sends `{"typing": false}` to clear their typing status for other users.

## Potential issues

This MSC is potentially far too generic for what it aims to achieve, which is a "User is recording a 
voice message..." line in clients. This approach feels suitable for other applications in the future,
such as potentially streaming uploads or other lengthy message sending stats (as this approach could
send progress information too).

## Alternatives

Not really considered at the moment, but there is an option of a whole other `m.recording` EDU and partner
API to cover the use case of "show user as recording a voice message". This feels like overkill for such
a feature, however.

## Security considerations

As already mentioned, because the `content` the client sends to `/typing` is sent verbatim over federation
it could be a way to expose far more information than the user intended to send, such as their draft of
the message they are typing. Clients are strongly discouraged from using this practice, and servers should
enforce strong rate limits to help discourage the behaviour. Servers could even optionally reject `body`
being included in `content`, for example. 

If a client does decide to render `body` (or `formatted_body`) information from the typing notification,
it should consider the security risks associated with using unsafe user input, like HTML injection.

Clients could also abuse this feature for custom status, presence, or other similar functionality where it
might otherwise be disabled/non-functional on their homeserver. Again, servers should use rate limits to
avoid this sort of behaviour and room administrators/moderators should consider banning/kicking the users
from the room for doing this. Servers could also use pattern-detecting behaviour if appropriate for their
deployment to determine if a user is abusing typing notifications (for example, a user is unlikely to be
typing a message for 4 solid hours).

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3038.events` in place
of `events` - both in the `PUT` body and in the resulting `m.typing` ephemeral event. Note that servers
which do not support this functionality will end up ignoring any mention of `events`, thus leaving the
user as typing a text message in existing client implementations.
