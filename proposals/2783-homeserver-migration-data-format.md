# MSC2783: Homeserver Migration Data Format

The current matrix ecosystem now has multiple homeservers available for testing and use, however, as of writing this proposal,
once an admin has "picked" a homeserver implementation, you're effectively "locked in" on that homeserver implementation
for that domain, as it not possible to easily replace the implementation with another without a loss of data, or inconsistent
federation functionality.

The remedying point to this has been to "start a new server on a new domain", however,
private encrypted chats an unfederated rooms are difficult or plain impossible to transfer with this move,
and so there is a reluctance to move until the benefits outweigh this "lossy" migration method.

Currently, dendrite is gaining more and more compliance with the spec and synapse (the defacto "matrix homeserver" in features
and reliability), and conduit has an ambitious goal to be fully spec-compliant by the end of 2021. When these homeservers
become compliant, there isn't much holding back to migrate to these more performant implementations, with the
aforementioned "lossy" migration method being the only way, which could result in many "dead domains" and a hard breakage
of rooms and DMs for many.

## Proposal

This proposal aims to provide a better, lock-in free, and reliable way of migrating between implementations,
as well as be able to provide a format in which a "snapshot" backup of a server could be made.

This is supplemental to the existing spec, and this does not aim to influence the general protocol spec,
but rather provide a standard "mold" to "pour" a homeserver's data into.

This proposal aims to be extendable by custom homeserver implementations and other interested parties or documents,
be it that some data is implementation-specific, or that data is custom to MSCs or other "extended specifications".

(This proposal uses [RFC2119](https://tools.ietf.org/html/rfc2119) to indicate requirement levels. e.g. "SHOULD", "MUST", etc.)

## General Structure

The proposal mainly defines a directory structure, this directory structure can be captures in ZIP files,
RAR files, `.tar.gz` files, or any other sort of archival or indexable directory "target".

At the root of the directory structure, a file `manifest.mspf.json` exists, this is the manifest, this file MUST always exist.

The `mspf` here stands for "Matrix Server Persistance Format", this is not a custom file format,
but is suffixed before `.json` to not confuse this file with other "`manifest.json`"-identified formats.

The manifest contains information pertaining to "items", items can concern themselves with things such as room events,
queued `to_device` events, user account data, but also custom data (such as data pertaining to SSO)

All items are mapped with their java-domain-notation specifier (e.g. `org.example.subdomain`), all items are JSON `object`s.

The Item `object`s can be freely fitted for their purpose, but every Item SHOULD have their version specifier specified in the key `v`,
which can be any JSON value itself (though `int`, `array[int]` or `string` are recommended.)

All items starting their specifier with `m.` MUST be documented by the matrix spec itself, and any other specification SHALL NOT
claim a specifier with this prefix (such as MSCs and custom implementations).

However, also, when processing a manifest, *all* items prefixing with `m.` MUST be processed or otherwise handled,
when an importer encounters a `m.`-prefixed item specifier it does not understand, it must abort the import process.

So, `manifest.mspf.json` has a format of the following;

```yaml
{
  # Top-level version denotation, this is a "major version" by semver standards.
  # It is version 0, unstable, for the time of this proposal.
  "version": 0,
  "items": {
    java.domain.notation: Item
  }
}
```

And `Item` has a format of the following;

```yaml
{
  # Version denotation, Item specifications should use this when specifying their internal version.
  "v": [1, 29, 0]
  # Any other keys are undocumented here and are Item-specific.
}
```

## Directory Structure

To avoid collisions, the root directory has it's files prefixed with their corresponding Item specifiers,
and directories prefixed or nested with those specifiers.

This means that the item `org.matrix.synapse` can "own" `org.matrix.synapse.json`, "own" the directory `org.matrix.synapse/`,
and "own" `org.matrix/synapse.json`, to give some examples.

And so, for a more elaborate example, the directory structure could look like this;

```text
- manifest.mspf.json
- m.core.json
- m.events/
  - events.1.cbor
  - events.2.cbor
  - events.3.cbor
  - ...

- m.users/
  - users.1.cbor
  - users.2.cbor
  - ...

- m.e2e/
  - keys.1.cbor
  - keys.2.cbor
  - ...

- org.matrix/
  - synapse/
    - admin_data.json
    - community_data.json

  - msc/
    - 9876/
      - locations_index.idx
      - locations.cbor
```

Note: `m.` MUST NOT be split into a separate directory (i.e. `m/`).

This proposal does not specify a lookup or packer algorithm for the specific hierarchy or otherwise structure
of how Items must organize their files and directories, this is only to note that Items are free in doing it in this fashion,
if they wish.

## Initial `m.*` Items

To make this proposal (relatively) viable for use when first released, this section defines the first `m.`-prefixed
Items that come with version 0 of the manifest (and version 1 when standardized in the spec).

### `m.core` version `1`

`m.core` aims to capture the absolute "core" items of a matrix server.

It owns the file `m.core.json`, with the following structure;

XXX: Get more feedback if this is all "core" data.
```yaml
{
  # The servername part of a matrix server, required.
  "server_name": "example.com"

  # The signing key of the server.
  "signing_key": "ed25519 [...]"
}
```

### `m.rooms` version `1`

`m.rooms` aims to capture room metadata such as versions, memberships, and aliases.

It owns a the file `m.rooms.cbor`.

The file contains a mapping (`{}`) of room ID -> room details,
room details is another mapping with the following structure;

XXX: Aliases need better looking at.
```yaml
{
  # Room version, a string
  version: "1",

  # Local aliases to this room, array of strings
  aliases: [
    "#room:example.com"
  ]
}
```

### `m.events` version `1`

`m.events` aims to capture all events present in the database.

This includes local rooms, unfederated rooms, encrypted rooms, etc.

It owns the directory `m.events/`, and files `events.*.cbor`.

The files contain CBOR-encoded mappings of room ID -> array of events.

Event formats are room-version specific, and so for this proposal, they're opaque `object`s.

Event ordering isn't guaranteed, and it is not even guaranteed that all events to a room are only
saved on one file.

XXX: RoomID -> Array[Event] mapping because just making it arrays could be a lot of overhead for importers,
this way the importers can just "select" rooms from files and correctly parse version-specific event formats
from them, revert? or keep?

### `m.users` version `1`

`m.users` intends to capture all user-specific information.

This includes account data, room tags, and user devices.

It owns the directory `m.users/`, and files `users.*.cbor`.

The files contain CBOR-encoded mappings of user ID -> user details.

A user ID key mapping MUST only exist *once* across all files.

User details is another mapping with the following structure;

```yaml
{
  # Password hash, a string
  # XXX: Figure out format??? How would this even properly migrate between servers?
  #  its very likely that a "bolted down" hash format can cause security problems,
  #  and it's possible the receiving server doesn't have or want to have the password hash
  #  variants in question.
  password_hash: "",

  # A UNIX timestamp for when the user has created this account.
  created_at: 0,

  # A 'roomID (string) -> {tag (string) -> content (object)}' mapping
  room_tags: {
    "!abc:example.org": {
      "m.tag": {}
    }
  },

  # A mapping of DeviceID -> Device
  devices: {
    "DEADBEEF": {
      # A freeform string, can be null
      display_name: "UwU Matrix Tesseract client (Tesla)",

      # A boolean for if the device is hidden from user profiles or not.
      # XXX: I picked this from the synapse postgres DB table, feedback?
      hidden: false
    }
  }
}
```

### `m.e2e.to_device` version `1`

`m.e2e.to_device` aims to capture all in-flight/undelivered `to_device` events.

XXX: I'm not sure if this should be under `e2e`, thoughts?

XXX: Does this also have to include outbound `to_device` events that havent been delivered yet?

It owns the files `to_device.*.cbor` under directory `m.e2e/`.

XXX: TODO; structure of files, array? mapping?

### `m.e2e.keys` version `1`

`m.e2e.keys` aims to capture all E2E-encryption-key related data.

XXX: Need expertise for this, I don't know how much or what specifically i should or could capture here.

## Potential issues

Forward-compatibility is a huge note, as Items are versioned, and non-spec keys could exist for a long time,
a fairly lossless process must be applied to ensure that older specifiers (within reason) can be resolved with ease.

When going from an unstable prefix (`org.matrix.msc`) to a stable one (`m.`), importers should decide if they want to support the
unstable prefix, this is thus not guaranteed and is on a case-by-case and importer basis if these are supported.

Some "edge data" can get lost, such as received transactions, "event edges", optimized identification of state events, and some
of these optimizations would need to be resolved while importing.

The extend to which this proposal goes to add new definitions of data which is already defined in the spec somewhere else can be
superfluous, and perceived as "spec bloat".

## Alternatives

One alternative is to write and maintain one-way one-time migration scripts, which would convert one implementation's database into another's,
these would be relatively costly to maintain for multiple implementations, as maintainers are forced to choose which scripts to maintain and
which implementations to "bless".

## Security considerations

Having a copy of the exported archive is akin to having full access to the database and signing key of a server at any time,
thus this data should be handled carefully.
