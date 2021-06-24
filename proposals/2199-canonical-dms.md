# Canonical DMs (server-side middle ground edition)

In the messaging space it is common for apps to expose exactly 1 chat for a conversation
between two users, and in some cases a specific set of users. Matrix currently does not
adequately support this as it allows for multiple rooms to represent a DM between two users.
Although supporting multiple chats with individuals is potentially useful for some use cases,
clients are increasingly wanting to be able to support exactly one DM for a user.

Any messaging app is likely to want to differentiate DMs from all the noise, and Riot in
particular is looking at using the DM between users for a more personal experience within
the app (such as key verification between users). This proposal focuses on immutable DMs
between users to assist in identifying the "One True DM" between users and prevent the
room's scope from increasing.

For comparison to Matrix, the following chat apps/platforms all support and encourage a
single DM between users. They all redirect the user to an existing chat with the target
user, creating a new DM if needed.

* Slack
* Discord
* IRC
* Telegram
* Gitter
* Facebook Messenger
* Twitter
* Hangouts
* Instagram
* Rocket.Chat
* Steam
* WhatsApp
* SMS
* and probably many others...

Platforms which allow/encourage users to have multiple DMs with a specific person are:

* Matrix (currently)
* Email
* XMPP (technically speaking)

This proposal covers how servers enforce exactly one DM (ideally immutable) between a set
of users. Clients have some responsibilities to render this appropriately, however the server
is expected to do most of the heavy lifting here. Immutable DMs are direct chats between
users where the participants can't change the room's aesthetics. For example, users can't
change the name or topic of the room, and they'll always be DMs.

This proposal supports "direct chats" or "DMs" in the sense of private conversations with
a set of users. This means that a DM between 3 users is possible, however the common case
is likely to be 1:1 (2 person) chats.

Immutability of DMs is also proposed in this MSC, however as an optional feature of DMs and
not a requirement.


## Proposal

In short, the entire direct chat module in Matrix is deprecated by this proposal. The direct
chat module relies on clients behaving themselves and tracking all the information for themselves
while somehow coming to the same conclusions as any other client the user happens to run. In
practice this becomes very difficult to do and maintain, particularly given the direct chats
are stored in an account data blob. If two clients were to update the account data at the same
time (which happens *a lot*), the clients would end up overwriting each other.

Direct chats consist of "important" and "unimportant" users to allow for bots and personal
assistants in a chat. Unimportant users don't affect the DM-ness of the room and are essentially
observers on the room (with speaking rights). How classification is done is defined later in
this proposal.

Direct chats are now expected to be identified and labelled by the server through the `summary`
response field on `/sync`. The `m.heroes` MUST contain the important users in a DM, regardless
of the presence of a name, canonical alias, etc on the room. The heroes must never be truncated
for a DM, and must not contain the syncing user's ID. A new field, `m.kind`, is mandatory for
direct chats which can only be `m.dm`. Future values may be added in a future proposal. Like
the other fields in the summary, `m.kind` may be omitted if there was no change in the field.

For the purposes of demoting a DM from its DM status, `m.kind` can also be the literal `null`
to identify it as "unknown or irrelevant kind".

Implementation note: clients can identify whether a room is a 1:1 or multi-way chat by looking
at the `m.kind` and `m.heroes`: if the kind is `m.dm` and there's only 1 user in `m.heroes`
then the room is a 1:1 chat. If the kind is `m.dm` and there's 2+ users in the `m.heroes` then
it is a multi-way/private group chat.

Implementations should also be wary of semantics regarding what causes a room to jump between
a multi-way DM and a 1:1 DM. Users can be invited (and joined) to either kind of room without
causing the room to jump to a different kind: for example, a 1:1 chat can have several unimportant
users in it (bots, etc) which do not make it a multi-way DM. Similarly, if an important user
were to leave a multi-way DM the room does not become a 1:1 DM. This is all described in further
detail later in this proposal.

With irrelevant fields not included, an example sync response would be:
```json
{
    "rooms": {
        "join": {
            "!a:example.org": {
                "summary": {
                    "m.heroes": ["@alice:example.org"],
                    "m.joined_member_count": 1,
                    "m.invited_member_count": 1,
                    "m.kind": "m.dm"
                }
            },
            "!b:example.org": {
                "summary": {
                    "m.heroes": ["@bob:example.org"],
                    "m.joined_member_count": 2,
                    "m.invited_member_count": 0,
                    "m.kind": "m.dm"
                }
            },
            "!c:example.org": {
                "summary": {
                    "m.heroes": ["@alice:example.org", "@bob:example.org"],
                    "m.joined_member_count": 3,
                    "m.invited_member_count": 0,
                    "m.kind": "m.dm"
                }
            },
            "!d:example.org": {
                "summary": {
                    "m.joined_member_count": 5,
                    "m.invited_member_count": 2,
                }
            }
        }
    }
}
```

Clients rendering the above should end up with something like the following:

![alice-bob-over-banquet](./images/2199-dms-client.png)


Servers are expected to be able to identify direct chats for users and flag them appropriately
in the room summary. How existing DMs are migrated is covered later in this proposal. The
server must use these rules to determine if a room is a direct chat:
* The join rules are `invite`.
* The rejoin rules are `invite` or `join` (as per [MSC2213](https://github.com/matrix-org/matrix-doc/pull/2213)).
* The user's most recent membership event has `"m.dm": true` in the `content`.
* The room has an explicit power level event (running a DM without a PL event is not supported).
* The room has at least 2 possible important users (who may or may not be joined yet).
* The user themselves is important in the room.
* The room is not tombstoned.
* The room is not soft-tombstoned by the server (described later in this proposal).
* No important users have been banned. Kicking or leaving the room does not affect the DM-ness
  of the room.

Assuming no other conflicts arise (duplicate chats, etc) the room is considered a DM between
the important users in the room. Important users are identified simply by having a power level
greater than or equal to the `state_default` power level requirement.

The server MUST maintain the `m.dm` flag when updating or transitioning any user's membership
event. The server SHOULD refuse to let the user manipulate the flag directly through `PUT /state`
and similar APIs (such as inviting users to a room). Servers MUST consider a value of `false`
the same as the field not being present.

Servers are not expected to identify a room as a direct chat until the server resides in the
room. Servers MUST populate the room summary for invites if the server is a resident of the
room. Clients SHOULD use the room summary on invites and joined rooms to identify if a room
is a direct chat or not. Where the summary is not available and an `m.dm` field is on the
invite event, clients should be skeptical but otherwise trusting of the room's DM status.
For example, a skeptical client might list the room with a warning stating that the room
is flagged as a DM without being appropriately decorated, but not prevent the user from
accepting the invite.

Servers MUST attempt to identify (or re-affirm) rooms as a DM whenever the relevant state
events in the rules above change or are updated.

Soft tombstoned rooms are rooms which are considered tombstoned without an actual tombstone
state event being present. This is typically used to flag rooms where tombstone events cannot
be sent as tombstoned. This proposal goes into more detail on this a bit later.

#### A note about leaving DMs

Unless an important user is banned, the DM is still considered alive and should be able to
be rejoined even if some important people were to leave. However, there's a good chance that
when all important users leave that the room becomes unjoinable and therefore dead. To help
combat this, servers should approach rooms where important users have left with caution by
assuming the room cannot be brought back to life.

If [MSC1777](https://github.com/matrix-org/matrix-doc/pull/1777) or similar were to land,
the server should abuse the capability to determine how alive the room is. By refreshing
its perspective, it can avoid scenarios where it has to make assumptions about the state
of the room it is no longer in. The server should never autojoin the user to the room,
regardless of MSC1777 support or not.

The following cases are reinforcement reading for the conditions mentioned so far. They
describe how the server is expected to behave given a common scenario - not all scenarios
are covered here.

**Case 1: The DM resides on a single homeserver**: when all important users leave the DM,
the DM is to be considered soft-tombstoned for those users. This will cause a new DM to be
created. The presence of unimportant users can be enough for a homeserver to consider the
room not dead and therefore rejoinable.

**Case 2: The DM resides on 2+ homeservers**: this gets a bit tricky. When the last important
user leaves, that homeserver would not have visibility on the room anymore but does not have
enough information for it to be tombstoned (soft or otherwise). Another server can still rejoin
the room due to unimportant users being left behind, or keep the room alive without the other
homeserver continuing participation. The homeservers involved will still converge on the room
when other conversations start.

**Case 3: A duplicate DM comes in for a room the server has left**: when the server does not
have visibility on the members of a room anymore it cannot tombstone newly created rooms and
point to the room it can't see. If the server happens to be a resident of the room, it can
absolutely tombstone the new room in favour of the old room, even if the server's membership
is just unimportant users and the important users having left. When the server does encounter
an invite for a DM which duplicates a room it has left, it must assume that its perspective
of the older room is antiquated and that something happened to cause a new invite to come
in. After joining, if a server happened to tombstone the room to point to the older room
then the user could then try and join the room and refresh the server's perspective.

*Note*: Originally case 3 had a step for the server to autojoin the user into the existing
room to refresh its state, however this left a glaring hole for abuse to filter its way down
to a given user.


#### Creating DMs

The room creation preset `trusted_private_chat` is deprecated and to be removed in a future
specification version. Clients should stop using that preset and instead use the new endpoint
for creating DMs, as defined here.

**`POST /_matrix/client/r0/create_dm`**:

This is mostly a clone of `/createRoom` with the unnecessary parts left behind. This does not
replace `/createRoom`. This requires authentication and can be rate-limited.

Request parameters (JSON body):
* `room_version` (`string`) - The version to create the room with. Same as `room_version` from
  `/createRoom`.
* `invite` (`[string]`) - The list of user IDs to invite to the room. Same as `invite` from
  `/createRoom` with the added behaviour described below.
* `invite_3pid` (`[3pid invite]`) - The list of 3rd party users to invite to the room. Same as
  `invite_3pid` from `/createRoom` with the added behaviour described below.
* `creation_content` (`object`) - Additional content for the creation event. This is also the
  same as `creation_content` from `/createRoom`.

Note: `name`, `topic`, `visibility`, `room_alias_name`, `initial_state`, `preset`, `is_direct`,
and `power_level_content_override` are all intentionally excluded from the clone. There is no
preset support, aesthetic characteristics of the room (name, topic, etc) are not supported for
immutable DMs under this MSC, and the remaining fields do not have strong use cases for DMs -
clients can always send state event updates after creating the room, for instance.

Response (JSON):
The server creates the room similar to how `/createRoom` operates:

1. An `m.room.create` event is created, as is `m.room.power_levels` using the defaults.
2. Join rules of `invite` are set with a rejoin rule of `join`, as per
   [MSC2213](https://github.com/matrix-org/matrix-doc/pull/2213)). This is to allow DMs to be
   re-used (described later) without sacrificing security of the DM by letting random people
   who were invited at some point into the room.
3. History visibility of `invited` is set.
4. Guest access of `can_join` is set so that guests can be included in DMs where needed.
5. Encryption is enabled by default using the most preferred megolm algorithm in the spec.
   Currently this would be `m.megolm.v1.aes-sha2`.
6. Power levels with the following non-default structure are set:

   ```json
   {
       "events_default": 0,
       "state_default": 50,
       "users_default": 0,
       "ban": 50,
       "invite": 50,
       "kick": 50,
       "redact": 50,
       "notifications": {
           "room": 50
       },
       "events": {
           "m.room.name": 100,
           "m.room.avatar": 100,
           "m.room.topic": 100,
           "m.room.history_visibility": 100,
           "m.room.power_levels": 100,
           "m.room.join_rules": 100,
           "m.room.encryption": 100,
           "m.room.canonical_alias": 100
       },
       "users": {
           <see below>
       },
       "third_party_users": {
           <see below>
       }
   }
   ```

   This power level event is not applied until after the invites have been sent as otherwise
   it would be impossible to give third party users power. Servers should apply a default
   power level event to the room and then apply the power level event described here after
   the invites have been sent. Servers can optimize this process and use this power level
   event at step 0 of the room creation process if there are no third party invites to send.
   Users invited to the room get power level 50, including the creator.
    * Third party users invited to the room get power level 50, as described by MSC2212 (see
      later on in this proposal for how this works). Like the invited users, all third party
      users invited as a result of the `/create_dm` call are considered important.
7. Users (3rd party and otherwise) are invited. Important users (those invited and the creator)
   MUST have `"m.dm": true` in their membership event content. Third party important users get
   the same `m.dm` flag on their `m.room.third_party_invite` event contents.

Servers MUST return an existing room ID if the server already knows about a DM between the
important users. The important users which have left the DM MUST be explicitly re-invited.
If the user trying to create the room is not in the DM themselves, the server MUST try and
re-join the user to the room. If the re-join fails, the server should create a new room
for the DM and consider the existing one as soft-tombstoned.

The rationale for preventing either party from manipulating the room is to ensure that there is
equal representation of the room from both parties (automatically named, automatic avatar, etc).
Users generally expect that a DM will be predictably dressed for searching and scanning, meaning
that the other parties cannot change the aesthetics of the room. For predictable history and
privacy, the room's history & join rules are locked out from the users. The users can upgrade the
room at any time to escape power level struggles, although this may not maintain the DM status.

*Note*: The `private_chat` preset is untouched as it does not affect DMs. `trusted_private_chat`
was intended for DMs despite its name and is deprecated as a result.

*Note*: Servers are still expected to be able to identify DMs from `/createRoom`, and clients
are able to craft DMs using `/createRoom`. When this happens, servers MUST return an existing
room ID for a DM if one exists and it looks like the user is trying to create a DM through the
`/createRoom` endpoint.

#### Glare and duplicated rooms

There is a potential for two users to start a DM with each other at the same time, preventing
either server from short-circuiting the `/createRoom` call. Servers MUST NOT prevent users
from accepting or rejecting invites to known conflicting DM rooms. Servers SHOULD NOT retract
the invite and SHOULD NOT automatically join the user to the room. The rationale is that the
user is likely to have already received a notification about a room invite and would be
confused if the room went missing or was automatically accepted. Clients are welcome to adjust
their UX as desired to do something else instead (like automatically reject/accept the invite
or hide it when it is an apparent duplicate).

When the server joins a room it has identified as conflicting/duplicating an existing DM it
MUST apply the conflict resolution algorithm:
1. Order all the conflicting room's creation events by their `origin_server_ts`.
2. Pick the room with the **oldest** creation event as the canonical DM.
3. Send a tombstone state event to the non-canonical DM rooms pointing at the canonical room.
   * If the tombstone cannot be sent by the server due to auth rules, it must consider the
     room as "soft-tombstoned". A soft-tombstoned room is just a flag for preventing a room
     from being counted as a DM and has no further behaviour or implication in this proposal.

The rationale for picking the oldest creation event is it is likely the room with the most
context for the user. It is possible that a malicious user intentionally creates a new room
with an ancient creation event however there's very little gain in doing so. The algorithm
is chosen such that any two servers come to the same conclusion on which room to use.


#### Upgrading DM rooms

There may come a time where DM rooms need to be upgraded. When DM rooms are upgraded through the
`/upgrade` endpoint, servers MUST preserve the `content` of the previous room's creation event and
otherwise apply the `immutable_dm` preset over the new room. If conflicts arise between
the previous room's state and the state applied by the preset, the preset takes preference over
the previous room's state.

Servers MUST create the new room by using the the room creation rules listed earlier in this
proposal. This means inviting the other parties of the previous room to the new room automatically
and ensuring the room state is as described above. Auth errors with transferring state (such as
the room name) must be considered non-fatal to the upgrade process: just skip that state event.

Note: normally room upgrades modify the power levels in the old room in an attempt to mute all
participants. However, no one will have power to modify the power levels in the old room.
Therefore, servers MUST NOT fail to upgrade a room due to being unable to update the power levels
in the old room. This is considered acceptable by this proposal because upgraded DM rooms will
lose their DM status, making them at worst just another room for the user.

Servers should do their best to follow tombstones to new DM rooms, however they should not assume
that those new rooms are valid DM rooms nor should they automatically join/invite the important
users to the room.


#### Detecting server support

Servers which implement this MSC prior to it appearing in a spec release MUST advertise as such
through the unstable feature flag `m.immutable_dms` on `/versions`. Clients which detect server
support should not only check for the feature flag but also the presence of a supported spec
version on the server (as the flag may disappear once the feature lands in a release). Currently
this proposal is expected to land in r0.6.0 of the Client-Server API.

Some servers have thousands and even millions of users which will need their DMs migrated. In
order to allow those servers to advertise the feature (both as an unstable flag and as a released
spec version) the client SHOULD assume that the server has not migrated its user's DMs until the
server sends the `m.direct_merged` account data event. More information about migration can be
found in the next section.


#### Migration

Users already have DMs which need to be correctly mapped by the server. Servers MUST use the
following process for migration for each user:
1. Grab a list of room IDs from their `m.direct` account data (if present). Ignore the user IDs
   that are associated with the room IDs.
2. Identify each room as either a DM or some other room, flagging them as appropriate, using the
   following steps:

   * If the room does not have a `rejoin_rule`, consider the rejoin rule as `join` for the
     purposes of identification.
   * Identify the room using the rules specified earlier in this proposal.
   * If the room did not have a `rejoin_rule`, attempt to set the rejoin rule to `join`. If that
     fails, do not consider the room a DM. Note that this will not cause the rule to magically
     work on prior room versions: it is just set to ensure that the DM flagging conditions
     are met as they don't care for the behaviour, just the value being present.

   Identification of DMs may involve conflict resolution, which should only happen after the steps
   above have been executed.
3. Set `m.direct_merged` account data with `content` consisting of a single array, `rooms`, listing
   all the room IDs the server iterated over, regardless of result.

The server SHOULD support automatically migrating any additions to `m.direct` even after migrating
the user. This is to allow for the user having an older client which does not yet support proper
DMs. Removals from `m.direct` are recommended to be left unhandled to ensure consistency with the
updated DMs.

Clients SHOULD NOT assume that the server will migrate direct chats if the user's `m.direct`
account data does not list any rooms. This is more important for new accounts created after the
DMs feature has been introduced in Matrix: if the server had to set `m.direct_merged` for every
user in the future, the server would be collecting largely useless data. Instead, the server is
given the option to skip migrations for users that have no data to migrate (such as new users).


#### Sugar APIs (for appservices/thin bots)

Appservice users and some bots are unlikely to see the room summary information. In an attempt to
combat this, some APIs are provided for users and thin clients to call and poke into the server's
view of their DM list.

The expected use cases for not using `/sync` are:
* When appservices want to contact a user in a DM fashion (IRC bridge sending NickServ info).
* When thin bots aren't syncing and want to alert users (monitoring bots triggered by external event).
* Clients which don't trust their local cache of DMs.

Appservices in particular are expected to heavily use the DM-finding API below and should cache
the result. When the appservice sees an event which the server might have reidentified the room
for it should invalidate its cache. Servers should make both of these endpoints highly cached.

**`GET /_matrix/client/r0/user/:userId/dms`**

The only parameter, `:userId`, is the user ID requesting their DMs. The auth provided must be valid
for this user. Example response:
```json
{
    "dms": {
        "!a:example.org": {
            "important": ["@alice:example.org"]
        },
        "!b:example.org": {
            "important": ["@bob:example.org"]
        },
        "!c:example.org": {
            "important": ["@alice:example.org", "@bob:example.org"]
        }
    }
}
```

The `important` array does not include the user themselves.

**`GET /_matrix/client/r0/user/:userId/dm?involves=@alice:example.org&involves=@bob:example.org`**

The `:userId` is the user ID requesting their DMs - the auth provided must be valid for this user.
This additionally takes `?involves` (specified multiple times) to search for a DM involving the given
users. It should be considered a bad request if the user asks for a DM involving themselves.

Example response:
```json
{
    "room_id": "!c:example.org"
}
```

If no DM exists involving those users, an empty object should be returned with 200 OK.


#### Third party invites

Third party invites (email invites) are hard to handle as the participants in the room are
unlikely to be able to modify the power levels in the room because the immutable DM preset
forbids this by design. To remedy this, this proposal requires that third party users get
their own power level, as described in [MSC2212](https://github.com/matrix-org/matrix-doc/pull/2212).

In addition to MSC2212, this proposal requires that a `m.dm` field be added to the
`m.room.third_party_invite` event. When the invite is claimed, the `m.dm` field must
be copied to the generated membership event.

#### Complete list of deprecations

Earlier in this proposal it was mentioned that the existing direct chats module is replaced
by this proposal, however it didn't exactly explain the scope. The existing module is
optionally supported by servers (which requires very little effort on their part), however
this proposal recommends that servers drop support completely per the deprecations below.

Deprecated things:
* `is_direct` on `/createRoom` now does nothing (ignored field, like any other unrecognized
   field).
* `is_direct` on membership events now means nothing (replaced by `m.dm`).
* `m.direct` account data is deprecated (replaced with the behaviour described in this
   proposal).

After sufficient time has passed, the deprecated components should be removed from the
specification.


#### Test cases for the server/proposal to consider

**Disclaimer**: This section might add clarity but might also be confusing. Sorry.

**Simple case**

The happy path of DMs.

1. Alice starts a DM with Bob. Alice and Bob end up with a single room.
2. Bob then starts a DM with Alice and gets redirected to the existing room by their client
   or server.
3. Alice tries to start a new DM with Bob. Like Bob in the last step, Alice is redirected
   to the existing room.
4. Bob then starts a DM with Alice and Charlie. A new room is created. Similar redirection
   semantics take place when the three parties attempt to duplicate the room.

**Simple glare**

The slightly less happy path of DMs: when servers collide.

1. Alice and Bob reside on different homeservers.
2. Alice starts a DM with Bob, who does not accept nor reject it.
3. Bob starts a DM with Alice, who does not accept not reject it.
4. Alice accepts Bob's invite. Alice's server realizes this is a duplicate room and sends
   a tombstone to the room, pointing at the DM Alice created earlier.
   * During this, Bob's server would have originally flagged the room as a DM for Bob and
     Alice, but the tombstone signals to Bob's homeserver that something is up and assumes
     that Bob has no DM with Alice (yet).
5. Bob gets a tombstone in Alice's DM and realizes there's a pending invite. Bob accepts.
6. Bob's homeserver sees that the room is a DM and flags it as the DM for Bob and Alice.

Alice and Bob's homeserver have come to the same conclusion. In the worst case, both servers
could accept the invites at the same time and conflict with each other on the tombstone. The
worst case for this is a split DAG on the tombstone with two tombstone state events, resolved
through state resolution. Both servers would have still come to the same conclusion on which
room to use so either of the tombstone events sent could be considered a no-op.

**De-duplication during migration / tombstone tree**

1. Alice has 3 existing DMs with Bob, who resides in both rooms.
2. The server updates (Alice and Bob happen to be on the same server in this example, however
   the scenario works cross-server too).
3. The server realizes that Alice and Bob share multiple DMs and pick the oldest DM. The
   server tombstones the other 2 rooms.
4. Alice and Bob now have exactly one DM with each other.

The room map looks a bit complicated now, but there's a tree of rooms where two point to
a single room. Clients aren't exactly expected to represent this nicely but can try if they
want to. There will be no `predecessor` for them to work off of.

If the canonical DM room was then upgraded or otherwise tombstoned itself, the tree starts
to become more linear.

**Tombstone tree with glare**

Following the example of a "tombstone tree" then creating a conflicting room with glare
the servers should resolve to use the canonical room identified by the tombstone tree. The
conflicting room should be tombstoned to point at the canonical room.

**Change in power levels, join rules, or membership**

If the power levels or join rules change then the server needs to re-evaluate the room. If
the room ends up being no longer a DM, the server must flag it as such to the relevant clients
and *not* send a tombstone into the room. The parties are considered to not have a DM.

If the membership changes such that someone ends up leaving the room (on their own or through
a kick/ban) then the DM is no longer considered a DM, similar to the paragraph above.

If the room starts to look like a DM again (members rejoin, join rules become acceptable again,
etc) then the conflict resolution algorithm might take place depending on the user's DMs.

**Malicious takeover of a DM**

1. Alice and Bob are on different homeservers, but don't have to be for this scenario.
2. Alice starts a DM with Bob. Bob accepts.
3. Bob's homeserver sends a tombstone into the DM to point it at Matrix HQ.
4. Both Alice and Bob no longer have a viable DM: both homeservers do not consider Matrix HQ
   as the replacement room, and do not treat the tombstoned room as a DM.

Ultimtely this is a wasted effort: both homeservers would start a new DM after the room was
directed at HQ.

**The cases covered by leaving DMs above**

This proposal covers a few cases that servers are supposed to consider when a user (or many
users) leaves a room. Please reference that section for more detail.


## Tradeoffs / issues

This is really complicated for servers to implement. The alternative is that the client
does all the work (see below in 'Alternative solutions') however this is deemed unreasonable
by the author and early reviewers of the proposal.

This allows for bots and personal assistants to be residents of a room. There is an argument
for restricting DMs to just important users (excluding any chance of unimportant users),
namely to ensure that security is not sacrificed through leaky bots/assistants. The author
believes there is a stronger argument for assistant-style/audit bots in a DM, such as a reminder
bot or Giphy bot. The rationale being that although bots pose a security risk to the conversation,
the rooms are supposed to have a history visibility setting which prevents the history from
being exposed to the new parties. Important parties additionally should have the power to remove
the new user account from the room if they don't agree.

This proposal enables encryption by default for DMs. Encryption in the specification is
moderately incomplete as of writing, making the move to enable encryption by default somewhat
questionable. For instance, a large number of bots and bridges in the ecosystem do not currently
support encryption and generally fall silent in encrypted rooms. Bots in today's ecosystem
can use [Pantalaimon](https://github.com/matrix-org/pantalaimon) or add dedicated support
if they so choose, however bridges are still unable to decrypt messages even with Pantalaimon.
Bridges being able to support encryption (they'll need EDUs and a device ID) is a problem
for a different MSC, and likely a different spec version. In the meantime, this proposal
specifically does not prohibit DMs which are unencrypted and bridges can start DMs as such,
or refuse to participate in DMs which are encrypted. Generally speaking, bridges in the
current ecosystem start the DMs with users instead of the users contacting the bridge,
however there are some prominent examples of this being reversed (IRC, most puppet bridges,
etc). Clients can combat this by identifying bridge namespaces (also a future spec problem)
and offering users the option to not encrypt the room, or by just having that checkbox
always present. Ideally, this proposal and cross-signing, better encryption for bridges,
etc all land concurrently in the next specification version.

This proposal is vague about which encryption algorithm to support. This is an intentional
choice by the author to support the possibility of a given encryption algorithm being
deemed unsuitable by Matrix in the future. For example, if a given algorithm was broken or
found to have security flaws it would be difficult to update the specification if the preset
had baked in a specific algorithm. Instead, the proposal asks the specification to make
a recommendation and for servers to think critically of the available algorithms (of which
only one is actually available at the moment) to make the best decision for their users.


## Alternative solutions

The sugar APIs are a bit awkward for the value they provide. Bridges are more commonly in
need of direct chats and thin bots arguably can still sync their way through life. Bridges,
and possibly clients, could receive changes to their DMs over a purpose-built room managed
by the server. Similar to server notices, the server could maintain state events in a readonly
immutable room for the user/client to sit in and receive updates. The author feels as though
this is more complicated than it should be, requiring servers to maintain hundreds, thousands,
or even millions of dedicated rooms for users which can easily overwhelm an appservice. For
instance, the Freenode IRC bridge has millions of users which would equate to millions of
rooms which all need to be synced down the appservice pipe which is already fairly congested.

Servers could be less involved and all this work could be done by the client. Although
easier for servers, clients are more likely to run into conflicts between themselves. The
most common type of conflicts for clients to have is updating account data at the same time,
which happens a lot more often than it should. When there's conflicts in updating account
data, there's a strong possibility that data is lost due to overwrites. Sure, the client
could be told to use room tagging instead however a similar problem occurs when one client
wants to add a tag and another wants to remove it. An earlier draft of this proposal did
cover what a mostly client-side implementation of immutable DMs could look like: it can
be found [here](https://gist.github.com/turt2live/6a4e21437508bce76be89d6cbaf65723).

Servers could be even more involved and require a whole new room version to change the
event auth rules for DMs. The author strongly believes that this is far too complicated
and way overkill for what Matrix needs/wants to achieve, despite having written an earlier
draft of this proposal calling for exactly that. Many of the problems with this approach
are described in that draft, found [here](https://gist.github.com/turt2live/ed0247531d07c666b19dd95f7471eff4).

There is also an argument that the existing solution is fine and clients should just
make it work for their purposes. The author believes this is an invalid argument given
the introduction of this proposal and the problems highlighted regarding client-driven
DMs.


## Security considerations

Some clients are investigating the usage of immutable DMs for security and privacy related
functionality of their design. For example, client designers are looking into handling key
verification and cross-signing within the immutable DM (if such a concept existed) rather than
in a floating dialog. To accomplish this in a safe and secure way it may be desirable to have
high levels of enforcement regarding immutable DMs. This may increase the user's comfort in
knowing that none of the users in the room can manipulate it. Clients which need this level of
confidence may wish to ignore insecure DMs and attempt to start new ones by upgrading the
existing DM through a predefined `preset` (ideally acquiring permission first).

There is a theoretical scenario where a homeserver or user could maliciously prevent a user
from opening a new DM with them. This is considered a feature given modules like ignoring users
exists, however a homeserver/user could continously set up a scenario where an existing DM
becomes unjoinable while sending tombstones for all new DM rooms which point to the unjoinable
room. This has a largely social impact on the room that technology cannot resolve (if people
are going to be mean, they're going to be mean). Attempts to alter the DM such that the user
cannot join without being notified are possible (changing the rejoin rules) however in those
cases both homeservers should be considering the room as no longer a DM, unless of course
the homeserver was being the malicious actor. Because of how tombstones currently work in
Matrix, users would have to perform an action to try and join the new DM and eventually the
user may get frustrated with the other user and ignore them, breaking the cycle of new DMs
being created.


## Pitfalls with the current system

The existing DM system in Matrix support multiple DMs with a user, however that system is
not necsarily more complex than this proposal (in fact, it's probably simpler than what
is proposed here). The existing system has the disadvantage of being non-deterministic where
two users in the same room can have a different view of that room in their clients: Alice
can see it as a DM whereas Bob sees it as just another room. Having non-deterministic DMs
can lead to conversational confusion ("hey Bob, let's go to our DM" and Bob asking where that
is) or uncertainty about where to send sensitive information.

Using the example of clients wanting to use DMs as a channel for exchanging key information,
knowing that all parties in the conversation perceive it as a DM is important. If the
verification were to land in a random room, the other party may miss it or be concerned it is
not a real verification request.

Further, the existing system is managed completely client-side and every client is expected
to clone the same logic. By pushing the DM calculations to the server, all the client has to
do is render them. Most messenger Matrix clients want or have a concept of DMs, and instead of
duplicating the same code over and over the server could just inform the client of its DMs.


## Conclusion

Immutable DMs are a hard problem to solve and involve a bunch of tiny changes to multiple parts
of the specification. Of all the iterations of this proposal, this proposal is targeted at being
a safe balance of client complexity and user safety, sacrificing the server's complexity in favour
of predictable results. Most clients are interested in implementing DMs in some capacity, and this
proposal helps make it less painful and more reliable for them. Users should feel safer to use
DMs with this proposal given the enabled encryption and permissions models imposed on the room.
