# MSC3013: Encrypted Push

Push notifications have the problem that they typically go through third-party gateways in order to
be delivered, e.g. FCM (Google) or APNs (Apple) and an app-specific gateway (sygnal). In order to
prevent these push gateways from being able to read any sensitive information the `event_id_only` format
was introduced, which only pushes the `event_id` and `room_id` of an event down the push. After
receiving the push message the client can hit the `GET /_matrix/client/r0/rooms/{roomId}/event/{eventId}`
to fetch the full event, and then create the notification based on that.

This, however, introduces the issue of having to perform an additional HTTP request to be able to
display the full event notification. On some systems (e.g. some weird vendor-specific android phones,
or while driving through ~~rural germany~~ places with patchy cellular network availability) this isn't
always the case.

This proposal adds a method to encrypt the push message in a way only the recipient client can decrypt
it, allowing the server to send the full event over push again, with this MSC and [MSC2782](https://github.com/matrix-org/matrix-doc/pull/2782).

## Proposal

A new pusher kind `http.encrypted.curve25519-aes-sha2` is introduced. It behaves the same as the pusher
kind `http`, except that the content it pushes is encrypted. That means it inherits all the pusher
data requirements, all the formats etc. It adds a new pusher data field, `public_key`, which is a
(optionally unpadded) base64-encoded curve25519 public key. This new field is not to be added to the
actual push payload being sent to push gateways. As such, setting such a pusher could look as
following (assuming [MSC2782](https://github.com/matrix-org/matrix-doc/pull/2782) has been merged):

```
POST /_matrix/client/r0/pushers/set HTTP/1.1
Content-Type: application/json

{
  "lang": "en",
  "kind": "http.encrypted.curve25519-aes-sha2",
  "app_display_name": "Mat Rix",
  "device_display_name": "iPhone 9",
  "profile_tag": "xxyyzz",
  "app_id": "com.example.app.ios",
  "pushkey": "APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvPVGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7hH5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMCg2ZXKqpc8FXKmhX94kIxQ",
  "data": {
    "url": "https://push-gateway.location.here/_matrix/push/v1/notify",
    "format": "full_event",
    "public_key": "GkZgmbbxnYZfFtywxF4K7NUPqA50Kb7TEsyHeVWyHBI"
  },
  "append": false
}
```

Now, when the homeserver pushes out the message, it is to perform the `notification` dict as with the
http pusher, and then encrypt all of its contents, apart from the `devices` key, using the following
algorithm:

1. Generate an ephemeral curve25519 key, and perform an ECDH with the ephemeral key and the public key
   specified when setting the pusher to generate a shared secret. The public half of the ephemeral key,
   encoded using unpadded base64, becomes the `ephemeral` property of the new payload.
2. Using the shared secret, generate 80 bytes by performing an HKDF using SHA-256 as the hash, with
   a salt of 32 bytes of 0, and with the empty string as the info. The first 32 bytes are used as the
   AES key, the next 32 bytes are used as the MAC key, and the last 16 bytes are used as the AES
   initialization vector.
3. Stringify the JSON object, and encrypt it using AES-CBC-256 with PKCS#7 padding. This encrypted
   data, encoded using unpadded base64, becomes the `ciphertext` property of the new payload.
4. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256 using the MAC key
   generated above. The first 8 bytes of the resulting MAC are base64-encoded, and become the `mac`
   property of the new payload.

This is the same algorithm used currently in the unstable spec for megolm backup, as such it is
comptible with libolms PkEncryption / PkDecryption methods.

### Example:
Suppose a normal http pusher would push out the following content:
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
      "unread": 2,
      "missed_calls": 1
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

The following object would have to be json-encoded to encrypt:

```json
{
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
    "unread": 2,
    "missed_calls": 1
  }
}
```

Resulting in the following final message being pushed out to the push gateway:

```json
{
  "notification": {
    "ephemeral": "base64_of_ephemeral_public_key",
    "ciphertext": "base64_of_ciphertext",
    "mac": "base64_of_mac",
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

## Potential issues

It is currently implied that a homeserver could push the same notification out to multiple devices
at once, by populating the `devices` array with more than one element. Due to the nature of cryptography,
this won't be possible anymore.

It is still unclear how well this will work with iOS and its limitations, especially concerning badge-only
updates if a message was read on another device.

If the gateway does additional processing, like marking call attempts differently, the relevant data
musn't be encrypted.

## Alternatives

Instead of this MSC, the push gateway for a specific app could encrypt the contents so that FCM/APNs
are still unable to see them. As the push gateway is set by app, that would mean that another server
than your homeserver gets full event contents for your push notifications. So this is also questionable
from a privacy point of view.

## Security considerations

In a first draft symmetric encryption was used. However, using asymmetric encryption seems like the
proper way to go here, as, in the case of the server being compromised, there is no need to re-negotiate
a new key to encrypt the push message.

## Unstable prefix

Is this needed here? If so, how? Soru is kinda confused as the pusher kinds are just `http` and `email`,
not having any `m.` prefix.
