# MSC3202: Encrypted Appservices

Presently, appservices in Matrix are capable of attaching themselves to a homeserver for high-traffic
bot-like usecases, such as bridging and operationally expensive bots. Traditionally, these appservices
only work in unencrypted rooms due to not having enough context on the encryption state to actually
function properly.

This MSC targets the missing bits to support encryption at the appservice level: other MSCs, such as
[MSC2409](https://github.com/matrix-org/matrix-doc/pull/2409) and [MSC2778](https://github.com/matrix-org/matrix-doc/pull/2778)
give appservices foundational pieces to get device IDs and to-device messages, as required by encryption.

## Proposal

This proposal takes inspiration from [MSC2409](https://github.com/matrix-org/matrix-doc/pull/2409) by
defining a new set of keys on the appservice `/transactions` endpoint, similar to sync:

```json5
{
  "events": [
    // as defined today
  ],
  "ephemeral": [
    // MSC2409
  ],
  "device_lists": {
    "changed": ["@alice:example.org"],
    "left": ["@bob:example.com"]
  },
  "device_one_time_keys_count": {
    "@_irc_bob:example.org": {
      "curve25519": 10,
      "signed_curve25519": 20
    }
  }
}
```

These fields are heavily inspired by [the extensions to /sync](https://matrix.org/docs/spec/client_server/r0.6.1#id84)
in the client-server API.

Both new fields can be omitted if there are no changes for the appservice to handle. For
`device_one_time_keys_count`, the format is slightly different from the client-server API to better
map the appservice's user namespace users to the counts. Users in the namespace without keys or
which have unchanged keys since the last transaction can be omitted.

Like MSC2409, any user the appservice would be considered "interested" in (user in the appservice's
namespace, or sharing a room with an appservice user/namespaced room) would qualify for the device
list changes section.

## Potential issues

Servers would have to track and send this information to appservices, however this is still perceived
to be more performant than appservices using potentionally thousands of `/sync` streams.

Appservices additionally cannot opt-in (or out) of this functionality unlike with MSC2409. It is
expected that servers will optimize for not including/calculating the fields if the appservice has
no interest in the information. Specifically, appservices which don't have any keys under their user
namespace can be assumed to not need device list changes and thus can be optimized out.

## Alternatives

An endpoint for appservices to poll could work, though this is extra work for the appservice and would
likely need pagination and such, which is all heavyweight for the server. Instead, having the server
batch up updates and send them to the appservice is likely faster.

## Security considerations

None relevant - this is the same information the appservice would get if it spawned `/sync` streams for
all the users in its namespace.

## Unstable prefix

While this MSC is not considered stable for implementation, implementations should use `org.matrix.msc3202.`
as a prefix to the fields on the `/transactions` endpoint. For example:
* `device_lists` becomes `org.matrix.msc3202.device_lists`
* `device_one_time_keys_count` becomes `org.matrix.msc3202.device_one_time_keys_count`

Appservices which support encryption but never see these fields (ie: server is not implementing this in an
unstable capacity) should be fine, though encryption might not function properly for them. It is the
responsibility of the appservice to try and recover safely and sanely, if desired, when the server is not
implementing this in an unstable capacity. This is not a concern once the MSC becomes stable in a released
version of the specification, as servers will be required to implement it.
