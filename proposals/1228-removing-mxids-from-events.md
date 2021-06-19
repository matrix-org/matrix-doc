# MSC1228: Removing MXIDs from events

## Background

We would like to be able to break the association between a user's ID (such as
`@richvdh:sw1v.org`) and their activity in a room.

The stretch goal is to also remove the association with server names, since for
many users, they are the only user on a server and it is reasonable to be able
to ask for the removal of any history of `sw1v.org`'s involvement with a room.

The general idea presented here is to use a pseudomym in many places where we
currently use user IDs. The current `@user:server` then becomes a user alias;
the mapping between alias and the psuedonumous ID is public but can be removed
in the future.

User IDs currently appear in the following places in a room:

 * `sender` of each event
 * `state_key` of `m.room.member` events
 * `users` list in `m.room.power_levels` events
 * `creatorUserId` in the content of `m.widget`

Server names appear in the following places:

 * `origin` of each event
 * keys in the `signatures` dict of each event
 * Room IDs
 * Room Aliases
 * `state_keys` in `m.room.aliases` events
 * `matrix.to` permalinks

## Proposal

[This is v3 of this proposal, which in summary is: do proposal v1, but also
introduce a requirement for a global `user_key` at the same time, which in
future will replace mxids as the user's One True Identity. v1 and v2 are
available for reference at
https://docs.google.com/document/d/1ni4LnC_vafX4h4K4sYNpmccS7QeHEFpAcYcbLS-J21Q#heading=h.y1krynr6itl4.]

 * Each user (currently identified by an mxid) will also have a `user_key`. In
   time, this will replace the mxid as your One True Identity; however for now
   they will live in parallel.

   * A `user_key` is represented like `~1:dV3hr3yE9SxhsWEGBJdTho777S8ompkJTh`,
     where `1:` is a version (to allow other systems to be used in future) and
     the rest is an (unpadded urlsafe-base64ed) ed25519 public key.

   * Homeservers are responsible for making up keys for their users.

   * For now, each homeserver maintains a one-to-one mapping between
     `user_key` and mxid for each of their users. In future, we will look to
     break this link to allow portability of accounts.

 * Room IDs also become ed25519 public keys.

   * They look like: `!Sr_Vj3FIqyQ2WjJ9fWpUXRdz6fX4oFAjKrDmu198PnI`.

   * The server which creates the room is responsible for creating the keypair.

   * The `m.room.create` event is signed with the room id to stop people making
     new rooms which look like old ones. After this point, the private key is
     never needed again. <sup id="a1">[1](#f1)</sup>

 * Define a `user_room_key`, which is yet another ed25519 public key.

   * It looks like `^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw`.

   * Homeservers are responsible for making up user keys for their users. They
     can (and should) use a different key in each room for each user.

   * This `user_room_key` is used where we currently use an mxid in the DAG:
     `sender`, `m.room.member`, `m.room.power_levels`,
     `creatorUserId`. `creator` is removed as per
     [MSC2175](./2175-remove-creator-field.md).

   * Events are **signed by the `user_room_key` of the sender instead of the
     server's key**.

   * If a user leaves and rejoins a room, they should use the same
     `user_room_key` (unless a server admin has manually removed the old
     mapping). This makes ban evasion harder. (It's up to server owners to
     ensure this rule is followed - servers which don't respect it and allow a
     serial abuser to evade bans by issuing different `user_room_keys` are likely
     to suffer whole-server bans.)

 * Invite and join events include:

   * `mxid_mapping`: field which gives the user's `@user:server` mxid and which
     must be signed by the server in question, and the signature must be
     verified before the mapping is considered valid.

   * `user_mapping`: contains the `user_key` giving your True Identity, and
     signed by that key. The signature must be verified by receiving
     homeservers for it to be considered a valid invite/join event for a vNext
     room.

### Examples

`m.room.create`: signed by both the room key and the `user_room_key` of the
sender:

```json
{
  "type": "m.room.create",
  "state_key": "",
  "room_id": "!Sr_Vj3FIqyQ2WjJ9fWpUXRdz6fX4oFAjKrDmu198PnI",
  "event_id": "$Riw5upWofaD4MNGM7bbZIj3bf+Th3fW/tklH4+6+VOg",
  "sender": "^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw",
  "content": {},
  "origin_server_ts": 1459891964497,
  "prev_events": [],
  "prev_state": [],
  "auth_events": [],
  "signatures": {
    "!Sr_Vj3FIqyQ2WjJ9fWpUXRdz6fX4oFAjKrDmu198PnI": "<...>",
    "^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw": "<...>"
  },
  "hashes":{"sha256":"3ASU57dV3hr3yE9SxhsWEGBJdTho777S8ompkJTh/Uo"}
}
```

`m.room.member`, showing `mxid_mapping` and `user_mapping`:

```json
{
  "type": "m.room.member",
  "state_key": "^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw",
  "room_id": "!Sr_Vj3FIqyQ2WjJ9fWpUXRdz6fX4oFAjKrDmu198PnI",
  "event_id": "$k21EhS3j8lhwqTi5NMTUH04oFyvR/1ujBGSWbW27aDs",
  "sender": "^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw",
  "content": {
    "membership": "join",
    "avatar_url": "...",
    "displayname": "...",
    "mxid_mapping": {
      "user_room_key": "^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw",
      "user_id": "@richvdh:matrix.org",
      "signatures": {
        "matrix.org": { "ed25519:a_zrXW": "<...>" }
      }
    },
    "user_mapping": {
      "user_key": "~1:dV3hr3yE9SxhsWEGBJdTho777S8ompkJTh",
      "user_room_key": "^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw",
      "signatures": {
        "~1:dV3hr3yE9SxhsWEGBJdTho777S8ompkJTh": "<...>"
      }
    }
  },
  "origin_server_ts": 1489597048772,
  "prev_events": [
    "$Riw5upWofaD4MNGM7bbZIj3bf+Th3fW/tklH4+6+VOg"
  ],
  "prev_state": [],
  "auth_events": [
    "$Riw5upWofaD4MNGM7bbZIj3bf+Th3fW/tklH4+6+VOg"
  ],
  "signatures": {
    "^Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw": "<...>"
  },
  "hashes":{"sha256":"KLx4Alfa0QzOihSmUMZ1WQj5QdWnbMHwmqKxmYO8hJE"}
}
```

### Handling the mxid mapping

When a server joins a room, it will be presented with a bunch of
`m.room.member` events which may claim mappings onto mxids. There are three
reasons we need to know whether the mapping is valid:

 * For clients, to help track users between rooms and to correlate to presence
 * To authorise other servers to do backfill requests, etc.
 * For outgoing messages, knowing which servers to send to.

None of these are _particularly_ urgent (they all degrade fairly gracefully in
the case that a mapping is missed). A lot of the slowness in joining rooms
currently comes from having to pull server keys so that event signatures can be
verified during the join process, so it would be nice to be able to consider
the join complete as soon as the signature on the event is verified, and verify
the `mxid_mappings` in the background.

#### Implementation

As a homeserver, we make an attempt to verify the sender before sending events
to our clients.

 * When a new invite/join event turns up for a _room you are already in_ (either
   via federation push, or because we pulled it via `/event/xxx` due to missing
   `auth_events`/`prev_events`):

   We make an attempt to verify its `mxid_mapping` before persisting it into
   our db. If the sig is wrong, we reject the event at that point.

   If we can't get the key (with a shortish timeout), we handle it as normal
   (and schedule a retry for later).

   Typically we only care about the most recent<sup id="a2">[2](#f2)</sup>
   `mxid_mapping` for each `user_room_key`; when we see another we can cancel any
   pending verification of any previous mapping<sup id="a3">[3](#f3)</sup>. Any
   previously-verified mapping should remain in place until another mapping
   becomes available.

 * When we _backfill_:

   We do the same thing, although in many cases we'll already have active
   mappings for the users in question, so we can ignore any received that
   way. By only honouring the most recent mapping, we gain the correct
   semantics for account portability: authorisation for backfill depends on the
   current location of the user, rather than wherever they were in the past.

 * When we join a _new room_:

   For now we do the same thing (ie, make an attempt to verify the mxid
   mappings in the join events we receive, and time them out quickly). In
   future we might optimise this so the the mappings are verified lazily.

This should mean that in the majority of cases, we'll have a verified mxid by
the time we send the event to a client.

For each `user_room_key`, we therefore have:

 * zero or one verified mxid mappings.
 * zero or one incomplete mxid mappings.

We extend the CS API to include a `verified_sender_mxid` field on any events
sent to a client where we know the user's current **verified** mxid.

 * This is included in the interests of helping simple clients do the right
   thing most of the time - but it is annoying and dangerous because it will
   **sometimes** be missing. Still, we don't want to either (a) hold up all
   traffic in the room while we wait for a verification which may never
   succeed; (b) hold back some events while we do a verification for a sender;
   (c) require that all clients always have to wait for an asynchronous
   verification and match them up.

We also add a **new** field to the `/sync` response which tells clients about
mxid mappings as they are resolved.

Question: should we remove unverified mxid mappings from join events before
serving them to the clients, to stop client developers relying on it and
breaking everything?

### Sending invites

We have a bootstrapping problem for invites in that, until a user joins a room,
we don't know their `user_room_key`.

Also: invite events are supposed to be signed by the invitee, so that other
members of the room can be sure that they have actually received a copy of the
event.

The current invite dance is:

 * inviting server builds a complete invite event, and signs it
 * inviting server sends a copy to invited server, along with some (unsigned)
   state about the room: name, avatar, inviting user's join event
 * invited server checks that request came from server of inviting user
 * invited server also signs the event, and tells the user about it
 * inviting server adds the (double-signed) event to the DAG and sends it to
   the rest of the federation (including the invited server, if it was already
   in the room)

We could change this to:

 * inviting server builds a partial invite event
 * inviting server PUTs to `/_matrix/federation/v3/invite/<event_id>/<target_mxid>` on invited server
 * invited server checks that request came from server of inviting user
 * invited server adds:
   * `user_room_key` in state_key
   * mxid attestation
   * signature
 * invited server tells the user about it, and returns the completed event to inviting server
 * inviting server adds its signature to the complete event
 * inviting server adds the (double-signed) event to the DAG and sends it to
   the rest of the federation (including the invited server, if it was already
   in the room)

## Problems

How to handle the state keys in `room_aliases` events?

How to handle server names in `matrix.to` permalinks?

What if somebody does a join with an inappropriate avatar/displayname? If we
redact their join, we'll redact their identity assertion too :/

## Other things that might fall out nicely

 * Fixes broken backfill due to changed signing keys (matrix-org/synapse#3121)
 * Case sensitive mxid comparison problems?
 * Opens a path to killing off perspectives in favour of just asking servers
   what their keys are (via TLS, with trust coming from X.509 certificates).
 * Helping with the domain reuse problem
 * Nicer way of validating redactions by comparing the `user_room_key` of the
   message and the redaction which addresses the suboptimal solution introduced
   by [MSC1659](./1659-event-id-as-hashes.md)
 * …

## Stuff we might want to avoid designing out

* Ability to migrate users between servers by changing their mapping assertions

* Ability to support alternative identity mapping assertions rather than being
  strictly mxid->user_key (e.g. 3pid->user-key too).  This could help
  decentralised identity mappings in general in future, and possibly unify 3pid
  invites with normal invites?  It could also support discovering servers by
  key rather than DNS (e.g. via DHT), which would be useful for p2p in future.

## Key management

If a private user key gets lost, they can just start using a new one and
announce a new mapping; however this may require an update to the
`power_levels` to give rights to the new user.

If a private user key is compromised, then again we start using a new one and
announce a new mapping, so that new events from the old key wouldn't look like
they came from that user. Again it may need `power_level`s updates to remove
power from the old `user_key`, but I think that is fair: you give away the keys
to your privileged account, you have to expect some cleanup. Ideally we would
have a way of revoking the old key properly, but this can be deferred for now.

<a id="f1"/>[1] although we might think about letting its use confer some sort of founder semantics.[↩](#a1)

<a id="f2"/>[2] or more accurately, the one in the current room state.[↩](#a2)

<a id="f3"/>[3] if a user/server spams out mappings so quickly that none of them ever complete, that is their own loss.[↩](#a3)
