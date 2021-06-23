# MSC2723: Forwardes message metadata

Currently a forwarded message is not easily recognized as a forwarded message. While for messages
of `msgtype` `m.text`, `m.emote` and `m.notice` clients could do something in the `formatted_body`
of `content`, for all other message types the forward highlighting would be very poor.
To get around this and provide a guideline to clients which information should go with a forward,
we suggest adding the "forward info" explicitly.
See also https://github.com/vector-im/riot-web/issues/4747.

## Proposal

### Providing m.forwarded

Leaning onto edits (adding `m.new_content` inside `content`), we want to suggest to add
`m.forwarded` to `content` to forwarded messages. The required information would cover at least
the original `sender`, `room_id` and `origin_server_ts`:

```
{
    "content": {
        "body": "Big Ben, London, UK",
        "geo_uri": "geo:51.5008,0.1247",
        "m.forwarded": {
            "event_id": "$123275682943PhrSn:example.org",
            "room_id": "!jEsTZKDJdhfrheTzSU:example.org",
            "sender": "@someone:example.org",
            "origin_server_ts": 1432735824141
        },
        "msgtype": "m.location"
    },
    "event_id": "$143273582443PhrSn:example.org",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.room.message",
    "unsigned": {
        "age": 1234
    }
}
```

## Potential issues

### Resolving display name and avatar
Since the receiver (of a forward) may not be in the room, the message has originally been posted
to, he may not be able to get the original sender's `displayname` and `avatar_url` from
`/_matrix/client/r0/rooms/{roomId}/members`.

We see two possible solutions at the moment:

1. The forwarder adds `displayname` and `avatar_url` to `m.forwarded`.
2. The receiving client resolves the `displayname` and the `avatar_url` from the user id given by
   `sender` using `/_matrix/client/r0/profile/{userId}`.

Both solutions have a drawback. In case of 1., changing the display name or the avatar would not be
reflected in forwards. And the avatar URL may even become invalid(?). The second solution may cause
confusion is the original sender has set different display names and avatars for different rooms.
I.e. if the original sender is in the room where the message is forwarded to, it may appear there
under a different display name and avatar. 

### Clients can fake forwards
Should we care of/can we avoid "fake forwards"? Does it make sense/is it possible at all to only
add the original `event_id` when sending a forward and assign the server the responsibility of
adding the forward information?

## Alternatives

### Extending info

```
{
    "content": {
        "body": "Big Ben, London, UK",
        "geo_uri": "geo:51.5008,0.1247",
        "info": {
            "forward_info": {
                "event_id": "$123275682943PhrSn:example.org",
                "room_id": "!jEsTZKDJdhfrheTzSU:example.org",
                "sender": "@someone:example.org",
                "origin_server_ts": 1432735824141
            }
        },
        "msgtype": "m.location"
    },
    "event_id": "$143273582443PhrSn:example.org",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.room.message",
    "unsigned": {
        "age": 1234
    }
}
```

### Discarded: Using m.relates_to
We've also discussed and discarded usind `m_relates_to` for highlighting the message as forward,
like the following:

```
"m.relates_to": {
    "rel_type": "m.forwarded",
    "event_id": "!1234:server.abc",
}
```

We discarded this idea for two reasons:

1. The idea of `m.relates_to` seems to be that related messages belong to the same room.
2. Its unclear who should fetch the event from a different room she/he/it is potentially not in
   and how this could be done at all.

## Unstable prefix
Clients can implement this feature with the unstable prefix `com.famedly.app.forwarded` instead of
`m.forwarded` until this MSC gets merged.

