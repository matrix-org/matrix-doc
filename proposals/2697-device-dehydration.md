# MSC2697: Device Dehydration

End-to-end encryption in Matrix relies on the sending device being able to send
megolm sessions to the recipients' devices.  When a
user logs into a new device, they can obtain the megolm sessions using key
backup or key sharing if another of their devices had previously received the
session.  However, when a user has no logged-in devices when a message is sent,
they are unable to receive incoming megolm sessions.

One solution to this is have a dehydrated device stored (encrypted)
server-side, which may be rehydrated and used when the user creates a new
login rather than creating a new device from scratch.  The new login will
receive any to-device messages that were sent to the dehydrated device.

## Proposal

### Dehydrating a device

To upload a new dehydrated device, a client will use `PUT /dehydrated_device`.
Each user has at most one dehydrated device; uploading a new dehydrated device
will remove any previously-set dehydrated device.

`PUT /dehydrated_device`

```json
{
  "device_data": {
    "algorithm": "m.dehydration.v1.olm"
    "other_fields": "other_values"
  },
  "initial_device_display_name": "foo bar",
}
```

Result:

```json
{
  "device_id": "dehydrated device's ID"
}
```

After the dehydrated device is uploaded, the client will upload the encryption
keys using `POST /keys/upload/{device_id}`, where the `device_id` parameter is
the device ID given in the response to `PUT /dehydrated_device`.  The request
and response formats for `POST /keys/upload/{device_id}` are the same as those
for `POST /keys/upload` with the exception of the addition of the `device_id`
path parameter.

Note: Synapse already supports `POST /keys/upload/{device_id}` as this was used
in some old clients.  However, synapse requires that the given device ID
matches the device ID of the client that made the call.  So this will be
changed to allow uploading keys for the dehydrated device.

### Rehydrating a device

To rehydrate a device, a client first logs in as normal and then calls `GET
/dehydrated_device` to see if a dehydrated device is available.  If a device is
available, the server will respond with the dehydrated device's device ID and
the dehydrated device data.

`GET /dehydrated_device`

Response:

```json
{
  "device_id": "dehydrated device's ID",
  "device_data": {
    "algorithm": "m.dehydration.v1.olm",
    "other_fields": "other_values"
  }
}
```

If no dehydrated device is available, the server responds with a 404.

If the client is able to decrypt the data and wants to use the dehydrated
device, the client calls `POST /dehydrated_device/claim` to tell the server
that it wishes to do so.  The request includes the device ID of the dehydrated
device to ensure that it is still available.

If the requested device is still the current dehydrated device and has not
already been claimed by another client, the server responds with a successful
response.  The server also changes the device ID associated with the client's
access token to the device ID of the dehydrated device, and will change the
device display name for the dehydrated device to the display name given when
the client logged in.

`POST /dehydrated_device/claim`

```json
{
  "device_id": "dehydrated device's ID"
}
```

Response:

```json
{
  "success": true
}
```

If the requested device ID does not belong to the user's current dehydrated
device or the dehydrated device has already been claimed, the server responds
with a 404.

Clients should not call any other endpoints before rehydrating a device.  In
particular, if a client calls `/sync` while rehydrating, the client should not
expect the `/sync` to return sensible information.  For example, it could
contain a mix of to-device messages sent to the old device ID and the new
device ID.

### Device dehydration format

The `device_data` property is an object that has an `algorithm` field
indicating what other fields are present.

#### `m.dehydration.v1.olm.libolm_pickle`

- `passphrase`: Optional.  Indicates how to generate the decryption key from a
  passphrase.  It is in the same format with Secure Secret Storage.
- `account`: Required. FIXME: libolm's pickle format

## Potential issues

### One-time key exhaustion

The dehydrated device may run out of one-time keys, since it is not backed by
an active client that can replenish them.  Once a device has run out of
one-time keys, no new olm sessions can be established with it, which means that
devices that have not already shared megolm keys with the dehydrated device
will not be able to share megolm keys.  This issue is not unique to dehydrated
devices; this also occurs when devices are offline for an extended period of
time.

This may be addressed by using fallback keys as described in
[MSC2732](https://github.com/matrix-org/matrix-doc/pull/2732).

To reduce the chances of one-time key exhaustion, if the user has an active
client, it can periodically replace the dehydrated device with a new dehydrated
device with new one-time keys.  If a client does this, then it runs the risk of
losing any megolm keys that were sent to the dehydrated device, but the client
would likely have received those megolm keys itself.

Alternatively, the client could perform a `/sync` for the dehydrated device,
dehydrate the olm sessions, and upload new one-time keys.  By doing this
instead of overwriting the dehydrated device, the device can receive megolm
keys from more devices.  However, this would require additional server-side
changes above what this proposal provides, so this approach is not possible for
the moment.

### Accumulated to-device messages

If a dehydrated device is not rehydrated for a long time, then it may
accumulate many to-device messages from other clients sending it megolm
sessions.  This may result in a slower initial sync when the device eventually
does get rehydrated, due to the number of messages that it will retrieve.
Again, this can be addressed by periodically replacing the dehydrated device,
or by performing a `/sync` for the dehydrated device and updating it.

## Alternatives

Rather than uploading a dehydrated device to the server, we could instead have
the sender resend the megolm session in the case where a user had no active
devices at the time that a message was sent.  However this does not solve the
issue for users who happen to never be logged in at the same time.  But this could
be done in addition to the solution proposed here.

The sender could also send the megolm session to a the user using a public key
using some per-user mechanism.  This would require changes to both the sender
and receiver (whereas this proposal only requires changes to the receiver), and
would require developing a system by which the sender could determine whether
the public key may be trusted (whereas this proposal the existing cross-signing
mechanism).

## Security considerations

If the dehydrated device is encrypted using a weak password or key, an attacker
could access it and read the user's encrypted messages.

## Unstable prefix

While this MSC is in development, the `/dehydrated_device` endpoints will be
reached at `/unstable/org.matrix.msc2697.v2/dehydrated_device`, and the
`/dehydrated_device/claim` endpoint will be reached at
`/unstable/org.matrix.msc2697.v2/dehydrated_device`.  The dehydration algorithm
`m.dehydration.v1.olm.libolm_pickle` will be called
`org.matrix.msc2697.v1.olm.libolm_pickle`.
