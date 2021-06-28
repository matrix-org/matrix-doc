# MSC2845: Thirdparty Lookup API for Telephone Numbers

Matrix clients may support VoIP and bridges can exist that accept a Matrix VoIP
call and terminate it on the PSTN, but currently no provision is made for a
user to enter a telephone number in order to call that number.

## Proposal
The Matrix API defines the thirdparty lookup API for this purpose: the
`GET /_matrix/client/r0/thirdparty/user/{protocol}` endpoint would be
used to look up a Matrix ID for a bridged user for a given phone number.

We define the protocol `m.protocol.pstn` to be a standard protocol identifier
for the PSTN, where users are identified by their telephone number. This
protocol has exactly one field, `m.id.phone` which is the phone number as
entered by the user (as defined for phone number identifiers elsewhere in the
Matrix spec).

Clients can assume that this protocol identifier can be used to reach phone
numbers on the PSTN and therefore a phone number entered by the user may be
reached using this protocol.

For the `m.protocol.pstn`, the API is generally expected to return only one result,
and clients may take the first and ignore any others.

The bridge is not expected to perform any canonicalisation of phone numbers at
this point: if a user dials a local number, a Matrix User ID representing that
local number should be returned. For this reason, there is no 'country' field
(or any other fields to indicate the user's location).

The `m.protocol.pstn` should appear in other thirdparty APIs as any other
bridged protocol would, eg. `GET /_matrix/client/r0/thirdparty/protocols`.

Protocols are currently not namespaced and it is up to the Homeserver admin to
avoid collisions within the configuration. Any further protocols defined by the
specification should be namespaced, but collision avoidance remains the
responsibility of the Homeserver admin.

The spec for `GET /_matrix/client/r0/thirdparty/user/{protocol}` shall also be
ammended to clarify that each field (ie. query parameter) may appear only once,
therefore only one phone number can be queried per request (other protocols may
return multiple results, however, if multiple User IDs match the specified
fields).

### Example
A user enters the number, "01818118181" into the dial pad. The client makes the
following query:

```
GET /_matrix/client/r0/thirdparty/user/m.protocol.pstn?m.id.phone=01818118181

```

The Homeserver is running SIP bridge with prefix `_sip_`. The bridge is
configured with a SIP gateway at `sip.example.org`. It therefore responds with:

```
[
  {
    "userid": "@_sip_01818118181%40sip.example.org:example.org",
    "protocol": "m.protocol.pstn",
    "fields": {
      "m.id.phone": "01818118181"
    }
  }
]
```

In this instance, the bridge has URL-encoded the SIP URI for the phone number
and added it to its `_sip_` prefix in order to obtain the Matrix User ID: this
behaviour is dependent on the specific bridge implementation.

## Potential issues
The `GET /_matrix/client/r0/thirdparty/user/{protocol}` is implemented in
Synapse but has no current known client support. The endpoint has existed for
some time as was designed for purposes exactly like this, but this would be the
first known usage of it.

This API also assumes that the bridge is hosted on the same Homeserver as the
user, and as such does not allow usage of a bridge on a different Homeserver.
This is a general problem with the `thirdparty` API that could be rectified.
Alternatively, the Matrix IDs returned by the bridge could reside on a
different Homeserver.

## Alternatives
Information could be given in `.well-known` on how to map a telephone number into
a Matrix ID. This would be generally significantly less flexible and would ignore
the existing way of performing this lookup that exists in the spec. It would also
allow much less flexibility on how a Matrix ID was formed given a phone number.

## Security considerations
None known.

## Unstable prefix
`m.protocol.pstn` is defined to be `im.vector.protocol.pstn` during development.
`m.id.phone` already exists in the specification and therefore shall be used
as-is during development.
