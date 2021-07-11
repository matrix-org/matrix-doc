# Proposal for improving notifications for E2E encrypted rooms

## Problem

Currently we have no way of receiving accurate notification counts for E2E
encrypted rooms.  This is because the server can't calculate the notification
counts serverside because it can't read the contents of the messages to spot
the notification keywords.

We mitigate this problem to some extent for push notifications by having clients
sync and decrypt all messages for their rooms when running in the background
(which on iOS and Android is intended to be always running in the background),
and then emitting local notifications for keywords.

However, this is also not perfect: it consumes significant bandwidth & CPU
whilst running in the background, as it has to download and decrypt every
message whether or not that message is actually a notification.  Also, if the
app crashes, is terminated by the OS due to memory pressure, or if the client is
offline, notifications will get lost unless the client backpaginates *all*
traffic since it last synced (which we currently don't do, given the potential
bandwidth, CPU, storage & time impact).

This issue has been historically tracked at
https://github.com/vector-im/riot-web/issues/2256

This should not be confused with the trivial Riot/Web bug which fails to make
it highlight or play sounds for notifs in E2E rooms even when it can calculate
them locally: https://github.com/vector-im/riot-web/issues/7489

## Solution

We provide two classes of solution: the common case (which supports notifying
for 'mentions'), and a rare case (which supports for notifying for custom
configured keywords).

### Reliable handling of mention notifications

For notifying for mentions, we propose adding an `m.mentions` field
which resides in the `contents` of `m.room.encrypted` events.  This contains an
array of the mxids who are mentioned in the body of a given event (if any).
This leaks the metadata of who is mentioning who, but we consider this an
acceptable risk given the read receipts, read markers, presence and sync traffic
patterns already leak considerable visible metadata about who is talking to
who.

In practice, this would look like:

```json
{
    "type": "m.room.encrypted",
    "content": {
        "algorithm": "m.megolm.v1.aes-sha2",
        "ciphertext": "AwgOEpABcEOmm0RXiNetf3+MwULKGsUxvpBeA+LpULBHIJe4O/N....",
        "device_id": "QEOYHMYOKQ",
        "sender_key": "1cBKte3VktfCJfKcK7L6REHR1Ng8jgA56Zhma9o0/js",
        "session_id": "kcZWPc2zqgJzaOYCNOLYMlfpe4APN6IGtPmJm/QJa9s",
        "m.mentions": [
            "@matthew:matrix.org",
            "@Amandine:matrix.org"
        ]
    }
}
```

This gives the server the necessary data to correctly calculate missed notifications
due to mentions, even in E2E rooms.  It also lets the server explicitly send badge
update push notifications for missed mentions via APNS/FCM, even if the client
is not running in the background.

As a special case, `@room` is also allowed as a possible value of `m.mentions`,
indicating when the message is attempting to notify the whole room.

One possible extension here is to also define a `m.visible` field on the contents,
which would be a boolean to let servers track whether a given message should
contribute to unread message counts or not and so calculate unread room state
and counts serverside rather than clientside.
(See https://github.com/matrix-org/synapse/issues/2632)

### Better handling of custom keyword notifications

The only way to safely notify for per-user specified custom keywords is for
the recipient to decrypt messages and scan them for keywords clientside.  This
means downloading **all** the history for rooms where we care about custom
keywords to scan for missed ones.  Specifically, the client would have to
backpaginate any gappy syncs it saw (e.g. after returning from being offline)
and potentially consume significant bandwidth/CPU/time as it caught up in the
background on what it had missed.

The good news is that custom keywords are fairly rare, and we can make this a
user choice - i.e. warn them in room settings that their custom keyword notifs
(if they have any) will not currently work unless they consciously burn
bandwidth to maintain an ongoing full clientside copy of the room.

The better news is that clients will also need to be doing this if they want to
provide clientside search of E2E rooms, so this isn't that unreasonable thing to
prompt the user to do, per room.  For instance, then they first try to search in
the room, it could prompt to turn on full sync.  Similarly, if they have keyword
notifs set, it can nag them to turn full sync.  There are large parallels with
configuring an IMAP client like Thunderbird to either download and index all
mail clientside or not.

## Tradeoffs

The main two possible approaches here are either to decorate messages with
plaintext metadata to aid counts/pushes, or to sync everything to the client
and decrypt it here.

Compromising by using both styles for different classes of traffic is hopefully
a satisfactory tradeoff.

It's possible there's some homomorphic encryption approach here where the server
could calculate the sum of notifs without knowing what the actual number was and
sending the encrypted result to the client to figure out, but this feels
overengineered, difficult, likely bandwidth intensive, and doesn't solve the
problem of the server needing to detect pushes.

## Security considerations

Malicious clients might lie about the notification metadata in order to spam
users (or hide mentions).  However, the risk of spam is not much worse than
the user sending spam of any other kind (e.g. non-e2e spam which mentions the
user in the body).  Arguably the ability to hide mentions is actually a feature,
and could save having to use l33tsp34k versions of displaynames when referencing
someone and not wanting to bing them.

