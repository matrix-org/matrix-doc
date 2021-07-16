# Third party user power levels

This MSC is a requirement for [MSC2199](https://github.com/matrix-org/matrix-doc/pull/2199)
to work in Matrix. It serves little value outside of MSC2199 due to the ability of users
within rooms to promote third party users once they claim their invite.

Currently when a third party (email) invite is sent the user which claims that does not
inherit any power level. As mentioned, this is not normally a huge issue for rooms where
the other users in the room can just promote them when they claim the invite. It is an
issue when the users in the room are not able to alter the power levels in the room, such
as in the case of immutable DMs (MSC2199).

Third party invites are a critical part of Matrix and being able to start DMs with third
party users is a hard requirement for MSC2199, however this portion of the proposal is
complicated enough to warrant a dedicated proposal.


## Proposal

*Note*: Other options to this problem are available, however this solution feels like the
cleanest and most straightforward. See "Alternative Solutions" below for more information.

In a future room version...

A new object is introduced to the power levels, with very similar semantics to how `users`
currently works:

```json
{
    "users": {
        "@alice:example.org": 50
    },
    "third_party_users": {
        "sWNAqPiVhScFoaAureCDj": 50
    },
    // other fields
}
```

`third_party_users` maps a `m.room.third_party_invite` token (`state_key`) to power level.
When a user successfully claims the invite, they inherit the power level represented by
the `third_party_users` without needing an entry in `users`.

The new field has auth rules which are adapted from the existing
[v1 auth rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules).

The new field has auth rules very similar to `users`:
1. Taking place immediately after 10a (requiring `users` to be a specific shape): If the
   `third_party_users` in `content` is not a dictionary with keys that are known tokens
   for `m.room.third_party_invite` events in current room state with values that are
   integers (or a string that is an integer), reject.
2. Rewriting 10d: For each entry being added, changed, or removed in `events`, `users`,
   and `third_party_users`:
   * Unchanged: if the current value is higher than the `sender`'s current power level,
     reject.
   * Unchanged: if the new value is higher than the `sender`'s current power level, reject.
3. Rewriting 10e: For each entry being changed under the `users` and `third_party_users`
   key, other than the `sender`'s own entry:
   * Unchanged: if the current value is equal to the `sender`'s current power level, reject.
4. Introducing a new rule about how to determine the power level of a `sender` (not currently
   specified, but implied through schema): The user's ID in `users` takes precedence over
   an associated entry in `third_party_users`, which takes precedence over `users_default`.
   There is no `third_party_users_default` field proposed here. This auth rule is intended
   to take place as one of the first to establish the user's power level for authorizing
   which events can take place.
5. Introducing a new rule taking place after 5a (rejection for missing `m.room.member` keys):
   `third_party_invite` under `content` must be preserved by membership events when they
   replace prior membership events which contained the field. Else the event is rejected.
   This is to make the server's implementation of matching up `m.room.member` events to
   third party invites a little faster given the relationship will always be held in current
   state, avoiding the requirement to look back through unknown amounts of state changes.

As specified today, the `token` under `third_party_invite` on a membership event can be
associated to a `m.room.third_party_invite`'s `state_key`, therefore linking the two events
together.

Now that third party invites are critical to the authorization of events, the redaction
rules are to be updated to incorporate the important parts:
1. Redacting a `m.room.third_party_invite` event must preserve `key_validity_url`, `public_key`,
   and `public_keys` under `content`. For each object in `public_keys`, all fields must be
   stripped except for `key_validity_url` and `public_key`.
2. Redacting a `m.room.member` event must additionally preserve `third_party_invite` under
   `content`. All fields are stripped from the `third_party_invite` object with the exception
   of `signed`, which additionally has all fields stripped with the exception of `mxid`,
   `signatures` (in its entirety), and `token`.


## Alternative solutions

Keeping in mind this proposal is fully intended for MSC2199...

1. The auth rules could instead be altered to allow a user which claims a third party
   invite to empower themselves one time only. They'd only be able to set themselves and
   no others to the `state_default` power level. The disadvantage here is that one could
   not have third party invites for users which are not intended to receive power without
   some additional restrictions.

2. The important users get tracked in an immutable state event (generated during room creation
   when using the preset). This sacrifices reusability of the power levels for additional
   tracking, and is not enforceable in pre-existing DMs (although neither are power level
   enforcements so does it matter?). The state event would list the user IDs and third party
   IDs (which can then be traced to membership events) which are "important".

3. Declare bankruptcy and don't support DMs with non-Matrix users. This is an unacceptable
   solution due to it preventing a major feature of Matrix.

There are potentially other solutions as well, however these 3 (and the one proposed here)
feel like the most sensible solutions. The solution proposed appears to be the cleanest
option which also avoids DM-specific behaviour in the auth rules, making it potentially
useful outside of DM use cases.


## Security considerations

There's a lot of tiny changes to auth rules and the redaction algorithm here. This could
lead to missing a field that is required to make all the parts work together, or it could
introduce a new abuse vector. Reviewers are encouraged to check the author's work.

At least one potential abuse vector is specifically mitigated in this proposal that is not
mentioned above: display names for third party invites could be unacceptable for the room
and need to be redacted. The specification currently requires that the `display_name` field
exist on third party invites (and the related `third_party_invite` content on membership
events), however the redaction algorithm currently also allows for it to be removed. This
proposal maintains the ability for the `display_name` to be redacted despite the requirement
for the field to exist. This proposal does not propose making the `display_name` optional.
