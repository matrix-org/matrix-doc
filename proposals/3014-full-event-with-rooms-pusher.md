# MSC3014: HTTP Pushers for the full event with extra rooms information

With [MSC2782](https://github.com/matrix-org/matrix-doc/pull/2782) adding a pusher for the full event
content and [MSC3013](https://github.com/matrix-org/matrix-doc/pull/3013) allowing to encrypt push
content huge steps are taken towards not needing to do any http requests at all to be able to process
incoming push frames properly. The notable exception here are badge-only frames, as they only tell
that the badge count updated, and its new count, but there is currently no way to tell which rooms
specifically have been read to be able to dispose of the notification, apart from calling `/sync` or
`/notifications`.

## Proposal

For pushers of type `http` (and thus all pushers inheriting from that type) a new `format`,
`full_event_with_rooms`, is introduced. This pusher has the same fields as the `full_event` pusher
described in [MSC2782](https://github.com/matrix-org/matrix-doc/pull/2782), with the addition of a
new `rooms` field inside of the `counts` object. This new field is a map of room IDs to notification
count. The rooms with a notification count of zero are not to be included in this map.

As such, an example of an event being pushed out could look as following:

```json
{
  "notification": {
    "event_id": "$3957tyerfgewrf384",
    "room_id": "!slw48wfj34rtnrf:example.com",
    "type": "m.room.message",
    "sender": "@exampleuser:matrix.org",
    "sender_display_name": "Major Tom",
    "room_name": "Mission Control",
    "room_alias": "#exampleroom:matrix.org",
    "prio": "high",
    "content": {
      "msgtype": "m.text",
      "body": "I'm floating in a most peculiar way."
    },
    "counts": {
      "unread": 4,
      "missed_calls": 1,
      "rooms": {
        "!someroom:example.org": 3,
        "!slw48wfj34rtnrf:example.com": 1,
      }
    },
    "devices": [
      {
        "app_id": "org.matrix.matrixConsole.ios",
        "pushkey": "V2h5IG9uIGVhcnRoIGRpZCB5b3UgZGVjb2RlIHRoaXM/",
        "pushkey_ts": 12345678,
        "data": {},
        "tweaks": {
          "sound": "bing"
        }
      }
    ]
  }
}
```

And a badge count only update could look as following:

```json
{
  "notification": {
    "counts": {
      "unread": 4,
      "missed_calls": 1,
      "rooms": {
        "!someroom:example.org": 3,
        "!slw48wfj34rtnrf:example.com": 1,
      }
    },
    "devices": [
      {
        "app_id": "org.matrix.matrixConsole.ios",
        "pushkey": "V2h5IG9uIGVhcnRoIGRpZCB5b3UgZGVjb2RlIHRoaXM/",
        "pushkey_ts": 12345678,
        "data": {},
        "tweaks": {
          "sound": "bing"
        }
      }
    ]
  }
}
```

## Alternatives

Instead of introducing a new pusher format a new flag to toggle the `rooms` field in the data of setting
an http pusher could be added. That way, the new `rooms` field could also be used in the `event_id_only`
format. As `event_id_only` needs to query `/sync`, `/event` or `/notifications` anyways it would not
benifit from this MSC at all.

## Security considerations

If not used in combination of [MSC3013](https://github.com/matrix-org/matrix-doc/pull/3013) this will
leak even more data to an untrusted gateway.

As one might create their own custom trusted gateway with e.g. gotify that could benefit from this,
this pusher format is also available for the plaintext http pusher.

## Unstable prefix

Is this needed for pusher formats?
