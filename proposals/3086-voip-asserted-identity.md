# MSC3086: Asserted Identity for VoIP Calls

Sometimes, the identity of the party on the other end of a VoIP call can
change, This can often be due to a call transfer: if this happens via
[MSC2747](https://github.com/matrix-org/matrix-doc/pull/2747) then the new
party will be advertised in the `m.call.replaces` event, but sometimes the
transfer mechanics can be handled entirely by an intermediatary such as a
switch or PBX. In this case, it can be useful to inform the transferee who
they're now speaking to.

## Proposal

This MSC proposes a new call event, `m.call.asserted_identity` which has the
common VoIP fields as specified in
[MSC2746](https://github.com/matrix-org/matrix-doc/pull/2746) (`version`,
`call_id`, `party_id`) and an `asserted_identity` object containing `id`,
`display_name` and `avatar_url` fields, similar to the `target_user` field in
[MSC2747](https://github.com/matrix-org/matrix-doc/pull/2747).

Unlike `target_user`, all 3 fields are optional. A user ID may be included if
relevant, but unlike `target_user`, it is purely informational. The asserted
identity may not represent a matrix user at all, in which case just a
`display_name` may be given, or a perhaps a `display_name` and `avatar_url`.

The `asserted_identity` may also be null, in which case the asserted identity
for the connected party reverts back to whatever the client would display had
no `m.call.asserted_identity` been sent (ie. probably the display name and
avatar of the remote party in the room in which the call is taking place). The
same applies if an `asserted_identity` object is given with no fields, but this
form is not recommended.

The asserted identity is supplied entirely by the opponent party in the call
and not verified by any other party and the client should treat it a such. The
client should not simply present the user as now being connected to the
asserted identity, preferring a 'call transferred to' style UI. The given
display name and/or avatar may not match the given Matrix user ID. The given
Matrix user ID may not exist at all. The entity on the other side of the call
may not have changed at all.

The event fulfils a similar purpose to [RFC 4916](https://tools.ietf.org/html/rfc4916)
or the [P-Asserted-Identity header in SIP](https://tools.ietf.org/html/rfc3325#section-9.1).

Examples:

The call has been transferred to a user called Alice:
```
{
    "version": "1",
    "call_id": "thE1dofth1scallisthis5trIng",
    "party_id": "abcdef",
    "asserted_identity": {
        "id": "@alice:rabbithole.example",
        "display_name": "Alice",
        "avatar_url": "mxc://rabbithole.example/ameD1aidLooksab1tliktHi5"
    }
}
```

The reason your widgets haven't arrived is a problem with your payment details
and you're being transferred to the accounts department:
```
{
    "version": "1",
    "call_id": "thE1dofth1scallisthis5trIng",
    "party_id": "abcdef",
    "asserted_identity": {
        "display_name": "Widgets Inc. Accounts",
    }
}
```

## Potential issues

 * Is of limited use to anyone without a VoIP switch / PBX
 * Trust considerations detailed elsewhere

## Alternatives

We could also perform an
[MSC2747](https://github.com/matrix-org/matrix-doc/pull/2747) call transfer for
the purpose of just updating the identity, however it would be undesireable to
tear down the media connection itself just to change the advertised identity.

In cases where the call is bridged from another protocol without media-level
bridging, the other party may update the connected identity without triggering
a media renegotiation (eg. in SIP, an RFC4916 message in an UPDATE with no
content), so requiring a new media connection to be established would prevent
such interoperability.

Additional spec could be added to perform a 'fake' call transfer, re-using the
same media connection, but if the transferee client did not understand this
event, it would drop the media connection and fail the call.  If a client does
not understand or ignores this event, it will simply not get the updated
identity.

## Security considerations

As detailed above, the information given in this event is not to be trusted any
more than the client / user trusts the user ID who sent it. It is important for
clients to present it as such.

## Unstable prefix

In unstable, the event name is `org.matrix.call.asserted_identity`
