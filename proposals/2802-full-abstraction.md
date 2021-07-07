# MSC2802: Full Room Abstraction

This proposal aims to provide a re-imagining of the Matrix Specification, making it less opinionated
towards Instant-Messaging, abstracting it, while preserving all features currently encoded in the
spec.

### Note: Acronyms/Terms for this document

This document uses a few acronyms and terms for brevity;

- "CS" or `c-s`: Client-Server API Specification
- "SS" or `s-s`: Server-Server API Specification
- "Custom Room Version": Referring to a hypothetical room version specification introduced by third
  parties, or Matrix, in the future.
- "Room Version Logic": Referring to room-version specific concerns, e.g. event validation
  specifics, etc.
- `/sync`: Client-Server `/_matrix/client/r0/sync` specification.

## Background/Preface

Matrix aims to be an inoperable standard, to be a generic data platform, with behavior only emerging
from the specific data interactions that take place on the room level.

However, the majority of the spec today is filled with specific biases towards a Instant-Messaging
type of implementations, some examples;

- [CS 9.3 Room Events](https://matrix.org/docs/spec/client_server/r0.6.1#room-events) defines an
  opinion of specific event types used for room moderation and control, this also breaches
  separation of concern, as this is defined in the Client-Server API, and possibly does not apply to
  any and all Room Versions, likely custom ones.

- [CS 9.7 Redactions](https://matrix.org/docs/spec/client_server/r0.6.1#redactions) defines an
  opinion on how-to redact/remove events, this can be undesirable in some specific situations, and
  requires global logic (thus another separation of concern) across all server implementations.

- [CS 13.2.1 Instant Messaging - Events](https://matrix.org/docs/spec/client_server/r0.6.1#id43)
  defines a series of *heavily* IM-opinionated events, that're proposed for global use, this
  breaches separation of concern yet again, as this is the concern of specific room versions, and
  client implementations of those room versions.

- [CS 13.4 Typing Notifications](https://matrix.org/docs/spec/client_server/r0.6.1#id49) and [CS
  13.5 Receipts](https://matrix.org/docs/spec/client_server/r0.6.1#id53) define a specific API,
  which has to be mirrored on Server-Server API Spec, these APIs are opinionated towards IM-specific
  purposes.

- [CS 9.4.1 `GET /_matrix/client/r0/sync`](https://matrix.org/docs/spec/client_server/r0.6.1#id257)
  has a response format heavily opinionated for IM purposes, with no headroom for many/much other
  custom implementation, with many extra keys tacked on as spec required it.

## The Proposal

The proposal is thus;

### The Vision

The relative vision of the proposal (to the current spec) is to see that `c-s` and `s-s` become
least opinionated over room-version-specific logic, and instead only concern with
receiving/returning data from and to internal logic.

The abstract vision of the proposal is to abstract `c-s` and `s-s` and any inline data/logic
definitions to easily allow custom extensions, and allow opinionated implementation to exist *only*
if it falls within a optional-keyed context (e.g. room versions and PSS (see below) `type` keys).

### Goals

The 1st goal is to decouple official data structures (prefixed with `m.`) from the `c-s` or `s-s`
specification, and instead delegate these to a "Schema" specification, outlining data structures for
"official" events or similar.

The 2nd goal is to lift opinionated event-specific behavior out of `c-s`, and put it inside Room
Version Logic, this allows event logic to be as arbitrary as they could be, with the workings of a
room.

The 3rd goal is to abstract miscellaneous other APIs from `c-s` and `/sync` in tandem, and allow
these to be generic, introducing a new form of non-room-specific data propagation in the process.

### 1st goal

Currently, `c-s` defines a set of
["modules"](https://matrix.org/docs/spec/client_server/r0.6.1#modules), and with it, specific event
specification for Instant Messaging.

While the logic, client, and server behavior should be delegated elsewhere (with that is the scope
of the 2nd goal), this goal concerns with the decoupling of *data schema* out of the `c-s`.

This goal also concerns itself with data structures such as
[`m.ignored_user_list`](https://matrix.org/docs/spec/client_server/r0.6.1#m-ignored-user-list),
[`m.ban`](https://matrix.org/docs/spec/client_server/r0.6.1#m-ban-recommendation),
[`m.fully_read`](https://matrix.org/docs/spec/client_server/r0.6.1#m-fully-read), and others, any
prefixed with `m.*`.

In short; this goal concerns itself with lifting any and all data structures prefixed with `m.` out
of the `c-s` and `s-s`, and into its own spec. And then allow Room Versions to refer to this spec
for the sake of brevity or separation of concern (where the room version merely adopts the official
event schemas from the schema specification, and then adopts a blanket validation policy, alongside
specific event validation logic.).

This relates to the vision of the proposal, as this goal aims to define a general database of
official data structures, which can be used in a schema-agnostic `c-s` and `s-s` specification, and
implemented and referred to by specific Room Versions.

Thus; a "Schema specification" should be published alongside all other specs, this spec outlines
data structures for `m.*`. The iterative versioning of this spec should be backwards-compatible.

#### Details

Specific wording could be applied to schemas;

- An "exhaustive" schema means that the data structure, when validated for any reason, should
  rigidly conform to the schema, and validation should fail when it does not.

- An "inexhaustive" schema means that the data structure is loosely defined, with any keys checked
  by the schema validated, but additional keys ignored (but persisted).
  - (e.g. this is interesting for `m.room.message`, which sub-categorizes itself via `msgtype`)

### 2nd goal

Secondly, `c-s`, with its ["modules"](https://matrix.org/docs/spec/client_server/r0.6.1#modules),
defines a series of specific server and client logic/behaviors.

This goal concerns itself with decoupling that logic from "global server logic" (as implied in `c-s`
and `s-s`), and instead wishes to push this into room-version-specific logic, to allow those custom
versions to concern themselves with that specific event logic.

e.g. Room Version Logic should be able to tell which users are part of a room, based on room state.
This decouples it from `m.room.member`, and instead allows any implementation to define their own
rules for membership, participation, and moderation.

e.g. [`m.room.redaction`](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-message-msgtypes)
should be room-specific logic, concerning itself with internal consistency after-the-fact when
stripping the original event of all non-critical data, by outlining server logic, and recommending
client logic.

### 3rd goal

`/sync` currently defines a myriad of keys and structures to be given to clients upon every
synchronization request, most of these keys are opinionated towards IM-specific implementations.

This goal aims to change `/sync`, and the majority of `c-s` and `s-s`, to have it not expose APIs
who's purpose is specific to room version logic, but instead provide a generalized abstract api
which room versions can use to carry data to clients and servers.

So, as a proposal, `/sync` should only return three types: Persistent Events, Empirical Events, and
Personal Server State Subscriptions.

Persistent Events primarily include new room events, new additions to the DAG tree, and any other
event that is persisted on the server.

Empirical Events included temporary events, events which are *not* persisted to the server, and only
exist for a brief moment.
- These can include events like typing notifications, or *draft: specific to_device events*.

"Personal Server State Subscriptions" include changes to PSS state that the client might be
interested in, such as own state, other user's state, or user-room state. (Read below for more).

Therefore, the "inputs" that the `c-s` spec will hereafter have are corresponding to the three types
in `/sync`; Persistent Events, Empirical Events, and Personal Server State. The `c-s` spec will
expose a generic endpoint for each.

### Details

*Speculation: also allow a specific "side-channel" with which clients can poke at rooms, but not
neccecarily send an event?*

## Personal Server State

In the 3rd goal, a new type of data was mentioned: "Personal Server State", this portion aims to
introduce that concept properly.

The Personal Server State refers to a `(target, type)` Key-Value data structure persisted on the
server, personal to the user, which can be manipulated by the corresponding user at any time. This
"state" has analogies with "room state" in the way that room state is also a Key-Value mapping.

This Personal Server State (or for brevity: PSS) aims to capture previously-opinionated data
structures like read receipts, display names, avatars, and other abstract user data.

The Value of a PPS Key can be any JSON-serializable data structure. (i.e. `object`, `bool`,
`number`, `null`, `array`, etc.)

The `target` of a PSS key can be a user, a room, or an empty string.

In the case that the `target` is a room ID, room-version-specific logic is triggered if the
room-in-question attests that the user is part of the room.

Implementations can be imagined as thus:

- With `target` being a user ID, and `type` being `m.relationship` (or similar), a "friend/block"
  system can be established, with which servers can apply additional logic depending on the
  "orientation" of both users to eachother, e.g. if both PSS define eachother as "friends", logic
  such as automatic DM approval, zero-common-rooms profile PSS queries, and other metadata can be
  allowed. Logic in a similar vein is applied with one user "blocking" the other, possibly having
  effects on clients.

- With `target` being a room ID, and `type` being `m.read`, and the value being an event reference,
  read receipts can be implemented via this method.

- With `target` being an empty string, the PSS can refer to the user's own information, such as
  profile data, presence data, or other information like announced 3PIDs (on profiles).

Servers can internally store PSS as `(user, target, type)`.

Servers can "mask" certain `type` keys to not propagate or persist, for performance, privacy, or
other reasons.

### Details

*Draft: Masking/Query authorization can be implemented via simple boolean logic and checked
cross-server, to ensure if the other server has the same "idea" for how this data should be handled.
e.g. for 3PID data, the other server can be asked if it has the "same idea" for this data, if it
checks PSS keys like privacy settings, and friend status, before allowing end-users to view the
data, this is so a homeserver that has "no idea" of these specifics can't be abused to leak data.*

*Ramble: Maybe make something like a vector/matrix clock helper which can propagate this inbetween
"hop" servers and disallow holding back PSS state announces? Internal rooms are too verbose and
persist data. PSS key-vals are always signed so ensure no forgery.*

## Outline of the resulting spec

Under these three goals, the spec gains the following roles:

The `c-s` MUST concern itself mainly with client authorization, and interfacing data with Room
Version Logic or Personal Server State.

The `s-s` MUST concern itself mainly with propagating, verifying, and receiving PDUs and EPUs, but
also resolving PSS.

The Room Version Specification, official and custom, SHOULD concern itself with implementing schema
and event validation, and otherwise not specified logic.
- A room version MUST be able to give a set of servers to propagate events to, given a room state.
- A room version MUST be able to attest if a user is participating in a room, given a room state.
- A room version CAN reject submitted data via `c-s` on the grounds of schema validation, the same
  does not apply for `s-s`.
- A room version CAN reject a DAG fork on the grounds of event validation (i.e. exclude it in the
  set of unlinked events).

The Schema Specification MUST ONLY concern itself with outlining data structures for official data
types (`m.*`).

This corresponds with the vision, with any alternative or future implementations in the matrix
network reasonably being able to communicate some form of abstract data, with `c-s`, `s-s` being
compatible for that kind of data, and behavior instead becoming emergent from room versions and PSS
relationships.

## Q/A

### Why is this needed?

Because right now, there is sentiment amongst users and core devs alike that the spec is becoming
bloated, and to cut it down is desirable.

This proposal aims to do that in a way that merely shifts the way this data is regulated and
carried, while being functionally compatible with the existing spec and current implementations in
the wild.

### Where do typing events go?

They become empirical events in rooms, specific to typing, then, there'd be a `m.typing` event key
denoting this.

Furthermore, it becomes possible to "specify" or "expand" this, the `m.typing` event can be come
specific to the action the user is taking, e.g. "X is uploading an image", "X is uploading a
document", etc.

### Where do reading receipts go?

They become PSS keys, specifically, `(room_id, "m.read")` keys, with the Value being a string of an
event reference.

This could potentially allow for "mark as unread" in the future, as read markers are only key-value
entries which can be changed at any time.

### How would displaynames/avatars work?

They become PPS keys, specifically, `("", "m.displayname")` / `("", "m.avatar")` for global or
otherwise-not-specified displayname/avatar information.

Possibly, when a user sets a PPS for a room (with these type keys), room-specific logic could (for
backwards compatibility) insert a membership event specifying the change of displayname or avatar.

### Why make PPS? Why add another data structure?

It seems there was a need for it, things like profile data was requested for a while, and expanding
the spec to encompass this was undesirable.

Thus, specifying a data structure that could encompass these types of data, and any other arbitrary
(e.g. outside the scope and idea of IM rooms in Matrix.org's vision)

### How would 3PID work?

Currently, `c-s` defines `r0/account/3pid` for operations related to 3PID.

PSS is designed for a "user bucket" type of data, having users being able to arbitrarily manipulate
server-specific data for their own account.

So allowing users to simply insert/put data onto PSS for 3PID purposes, maybe PSS can be skewed to
allow for "read-only" `target` keys, for which the server will write these on the users' behalf. For
3PID this could be a `"3pid"` key that users can read, but not write.

*Note: For this, the PSS spec would have to be altered to allow the client to retrieve a set of
"reserved" or otherwise "managed" `target` namespaces in PSS*

### How would room tagging work?

Via PSS, `(room_id, "m.tag")`, with the value being a simple string, or a list of strings, outlining
their categories.

### How will communities/groups work?

Technically, groups/communities are not part of the matrix spec (as the time of writing), however,
Element has decided to treat it as official, with execution relying on the goodwill of homeserver
implementations to adopt and implement an arbitrary spec from synapse's codebase.

There exist some other MSCs outlining communities/groups, however, for the context of this
re-imagining, communities *could* be a form of PSS, with the "P" ("Personal") removed, and instead
made "G" ("General", General Server State), however, this is a speculative idea.

Another speculative idea for this is that Communities simply become a custom room version,
`"community"`, which communicates/persists/propagates information about the community in its "room
state".


### How would "Room Version Logic" exactly work?

Currently, concepts like "auth" or "control" events, redaction, power-levels, and the
`m.room.member` event can fall under "Room Version Logic".

A room technically only has to say where events to send to, who is participating in a room (i.e. who
of the users can have "access" to rooms).

State resolution becomes a room-defined concept, it's only "change" to how events are related to in
the room being that an event simply does not get linked to one or more unlinked events. (e.g. This
being a result of a rejection of a DAG fork from a misbehaving server)

The room effectively becomes this pseudo-interface:

```py
class Room:
    def is_member(user: User) -> bool: ...
        """Attests a user is participating or otherwise has access to the room"""

    def make_event(data, sender: User) -> Event: ...
        """Validate and create Event object based off of user-sent data, can raise on failure/invalidation"""

    def trigger_pss(user: User, type_key: str, value: object): ...
        """Trigger arbitrary logic for a PSS update that targets this room"""

    def event_trigger(*events: Event, internal:bool=False) -> Optional[RoomState]: ...
        """Feed a series of events into this room,
        this can either be fed through #make_event() or federation transaction, will trigger logic to resolve internal state and return it if changed.
        Persists events to database, and sets the latest unlinked (valid) event references to be built on with #make_event"""

    def get_state(for_event: Event) -> RoomState: ...
        """Resolves state from the perspective of a specific event in the DAG graph."""

    def get_servers(for_state: State) -> List[ServerRef]:
        """Resolves a set of servers that're participating in this room from the perspective of a particular state."""

    # An internal queue that spits out events to be sent to other servers, is possibly
    # filled by #trigger_pss or #event_trigger
    out_pipe: asyncio.Queue[Event]

    # OR

    async def poll() -> Set[Event]: ...
        """Waits for new events to be generated for this room within the server, and returns them once its ready. This event should then be propagated with #get_servers."""

    def canonical_heads() -> Set[Event]: ...
        """Returns a set of unlinked last events of the currently-canonical DAG tree."""

    def all_heads() -> Set[Event]: ...
        """Returns a set of all unlinked events in the current DAG tree,
        some of these could not be accepted by the local room as of this moment"""

    def walk_dag(*heads: Event) -> Iterable[Event]:
        """Returns a reverse topologically sorted iterable of events canonical from a few DAG heads."""

    def reverse_iterable(from_event: Event, canonical:bool=True) -> Iterable[Event]:
        """Returns a sorted (new->old) iterable of events forwards from a specific event (canonical optional)"""

    def forward_iterable(from_event: Event, canonical:bool=True) -> Iterable[Event]:
        """Returns a sorted (old->new) iterable of events forwards from a specific event (canonical optional)"""

    def generator(from_heads: Optional[Set[Event]], canonical:bool=True) -> AsyncGenerator[Event]:
        """Returns a generator to be iterated on (optionally from a specific event,
        default from current heads (by #canonical_heads)) for receiving new events in a room."""

```

This is a very crude interface, but effectively, all room logic starts to only exist in
`event_trigger()`, which receives both federation and server-local generated events, persists these
to the database, and validates/rejects DAG forks based on internal validation/verification rules,
updates the latest unlinked events that the server deems canonical, and returns a room state (if
changed).

Here, `make_event` allows for local-user-facing scheme validation, and when succeeded, the event is
passed onto `event_trigger`, which "adds" this event to the state and DAG of the room, and triggers
return via internal polling for the event to be propagated.

### How would this new way of going forward with rooms change anything?

By reducing a "fundamental room" to an interface with which the server queries how to
transform/create and deliver data with state, room logic can effectively become much of anything it
wishes.

For example, with current room versions 1-6, all logic (redaction/power levels/auth events/etc.)
could be put into `event_trigger`, with optional schema validation logic in `make_event`. This
allows the room to "be a black box", have matrix only be a transport and framework around the inner
workings of that room, and have every server only having to denote if this specific "room
type/version" is supported, before concern is handed over to distributed shared internal room logic.

Validation concerns are moved over to acceptance of the DAG tree, with forking possibly happening,
but events never arriving at clients if they're not included as "canonical" by the room. Heads are
selected based on historical acceptance of forks (if these "make sense", such as e.g. with matrix
numerical room versions if a 0-power-level user suddenly bans a 100-power-level-admin), these heads
are selected for future locally-created events, and so invalid DAG forks are "politely ignored".

### What about p2p?

What *about* p2p? This proposal simply aims to put data into a new context, and abstract it's
layers, some of these layers allow definition of "servers", and doesn't care about delivery
transport or similar measures, and only aims to define a coherent framework for current and future
data to be captured by.

This proposal aims to be compatible with the "Portable Identities" proposal, by abstracting some
room-specific information in preparation.
