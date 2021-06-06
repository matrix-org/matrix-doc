# MSC2812: Role-based power structures

**Caution to the reader**: this is presently an information dump from my thoughts on how this
could work. It needs a lot of validation and work before it's ready as a proper proposal.

Currently Matrix operates off a power level structure where higher numbers have more power in a
room and lower numbers (with zero being a typical default) have the least power. This structure
can be used to represent a number of systems and can allow for a form of roles (moderator, admin,
etc) to be represented, though can be challenging to bridge to other platforms.

A true role-based power structure, in the eyes of this proposal, would be one which is more of a
permissions model rather than power model - a user could be granted a ban permission to ban other
members of the room, but could be denied all other typical moderator functions.

## Proposal

In a future room version...

**Note**: All identifiers are to follow [MSC2758](https://github.com/matrix-org/matrix-doc/pull/2758)
in this proposal.

Roles are declared using `m.role` state events where the state keys are arbitrary identifiers used
to differentiate between roles. An example `m.role` event's `content` would be:

```json
{
  "m.name": {
    "en": "Administrator"
  },
  "m.permissions": {
    "m.ban": {"m.allowed": true},
    "m.roles": {
      "m.change": ["org.example.sponsors"],
      "m.assign": ["*"],
      "m.revoke": []
    }
  },
  "org.example.colour": "#f00"
}
```

The content is highly extensible/namespaced to permit additional fields being added by implementations
which may be interested, such as (in the example) a colour to represent the role. Role names have
translation support, and must at least have an English definition for consistency reasons. Language codes
are per [BCP47](https://tools.ietf.org/html/bcp47), with `en` being representative of English.

Roles are only required to have an English name. By default, a role has no permissions associated with
it. This can be used to simply categorize members of a role for easy identification rather than granting
them any specific power - such examples may be wanting to identify supporters of a project within a room.

Note: groups (or communities) might also be used to categorize members within a room through flair. The
difference with roles is that they'd typically affect organization/grouping within the room list rather
than at a per-message level as flair currently does.

Permissions are identifiers with an associated object which varies depending on the permission itself.
Most permissions will have a single `m.allowed` boolean property (which defaults to `false`). The
proposed `m.*` namespace of permissions are defined later in this proposal with their relevant
specifications.

When using this roles system, `m.room.power_levels` serves zero meaning including for the purposes of
authorization rules. The changes to the authorization rules are defined later in this proposal.

### Identifying members in a role

On the applicable user's `m.room.member` state event, a new field of `m.roles` is added to be an array
of role IDs (state keys for `m.role` state events). For example:

```json
{
  "type": "m.room.member",
  "sender": "@alice:example.org",
  "content": {
    "membership": "join",
    "displayname": "Alice",
    "m.roles": [
      "m.admin",
      "org.example.supporter"
    ]
  },
  "state_key": "@alice:example.org",
  "origin_server_ts": 1579809459351,
  "event_id": "$tKStv-i0ympmbHEhnxZxwSkXJP5r-0Svf19HACNYKG4",
  "room_id": "!example:example.org"
}
```

Adding/removing (changing) roles associated with a user is protected by a permission - see the proposed
permissions later in this proposal for more information.

### Default permissions structure

Upon creation of a room, the server creates a default `m.role` state event with state key `m.admin`.
This role consists of all permissions being granted as per each permission's specification. This
role is automatically assigned to the room creator when they join for the first time, and the
authorization rules will be modified to allow this.

Permissions are otherwise granted as per their defaults to all users without any roles defined on
their membership event. By default, members do not get any roles associated with them upon joining
the room (with the exception of the room creator, as outlined above).

### Execution order / inheritence

Users can perform an action if any of their roles permit it. Roles do not have inheritence under this
proposal, though in future it may be possible to do so. Instead, it is recommended that applications
needing inheritence will create smaller, more specific, roles and assign those as needed.

### Proposed initial permissions

The following permissions are proposed to be included in the spec. They are all direct correlations
to the existing `m.room.power_levels` fields.

#### Common permission format

For simple permissions (ones that can be represented as an allowed/disallowed flag), the following
permission body is used:

```json
{
  "m.allowed": true
}
```

By default, unless indicated otherwise, `m.allowed` is `false`. When `true`, users with the applicable
role are able to perform the specified action.

#### `m.invite`

Whether or not a user can be invited to the room by someone with the applicable role.

This uses the common permission format and is **disallowed** by default. When the server creates the `m.admin`
role, this would be explicitly set to allowed.

#### `m.ban`

Whether or not a user can be banned from the room by someone with the applicable role.

This uses the common permission format and is **disallowed** by default. When the server creates the `m.admin`
role, this would be explicitly set to allowed.

#### `m.kick`

Whether or not a user can be kicked from the room by someone with the applicable role.

This uses the common permission format and is **disallowed** by default. When the server creates the `m.admin`
role, this would be explicitly set to allowed.

#### `m.redact`

Which senders can have their events redacted by someone with the applicable role. Like `redact` in the
power level structure, this only affects other people than the sender - the event sending permissions
cover restricting self-redaction.

The permission body for this would be:

```json
{
  "m.senders": [
    "@*:example.org"
  ]
}
```

The `m.senders` is an array of [globs under MSC2810](https://github.com/matrix-org/matrix-doc/pull/2810)
for which senders can have their events redacted by users with the applicable role. By default, this
array will be empty to denote that users do not have permission to redact other people's messages. When
the server creates the `m.admin` role, this would be explicitly set to `["*"]` to denote that anyone
may have their messages redacted by users in the applicable role.

#### `m.events`

Which room events (state and otherwise) can be sent by users with the applicable role.

The permission body for this would be:

```json
{
  "m.state": [
    {"type": "*", "m.allowed": true}
  ],
  "m.room": [
    {"type": "m.room.message", "m.allowed": true},
    {"type": "*", "m.allowed": false}
  ]
}
```

Room events are split into two kinds: `m.state` for state events, and `m.room` for all other room events.
Note that EDUs like presence and typing notifications are not (currently) handled by this proposal. Each
kind of event is an array of rules which are executed in order - the first rule that matches as allowed
will permit the user to send the applicable event.

The `type` within the rule is a glob ([MSC2810](https://github.com/matrix-org/matrix-doc/pull/2810)).

`m.allowed` is simply an indicator for whether or not event types matching the given rule are allowed.

Both the `type` and `m.allowed` properties are required on rules, however `m.state` and `m.room` are
not required and have the following defaults:

* `m.state` defaults to an implicit `{"type": "*", "m.allowed": false}` rule. When the array is explicitly
  empty, this deny rule persists.
* `m.room` defaults to an implicit `{"type": "*", "m.allowed": true}` rule. When the array is explicitly
  empty, an implicit deny rule of `{"type": "*", "m.allowed": false}` is present. This is to ensure that
  announcement-only rooms can be created by simply specifying `"m.room": []`.

When the server creates the default `m.admin` role, the following permission body is to be used:

```json
{
  "m.state": [
    {"type": "*", "m.allowed": true}
  ],
  "m.room": [
    {"type": "*", "m.allowed": true}
  ]
}
```

#### `m.notifications`

Which kinds of notifications users in the applicable role are able to trigger.

The permission body for this would be:

```json
{
  "m.room": true
}
```

The key of the object is the notification kind (with `m.room` being the `@room` permission level), and the
value is whether or not the role allows it to be triggered. By default, all notifications are disallowed.

When the server creates the default `m.admin` role, the `m.room` permission must be set as `true`.

#### `m.roles`

Whether or not users in the applicable role are able to add/change roles or add/remove them to users.

The permission body for this would be:

```json
{
  "m.change": [
    "org.example.*",
  ],
  "m.assign": [
    "m.admin"
  ],
  "m.revoke": [
    "*"
  ]
}
```

All three properties are arrays of globs ([MSC2810](https://github.com/matrix-org/matrix-doc/pull/2810))
which are matched against role IDs (state keys of `m.role` events). All 3 arrays default to empty, implying
that all related actions are denied. Arrays are ordered and are matched as first-allowed wins.

`m.change` denotes which roles a user in the applicable role will be able to modify the properties of.
For example, if the array lists `m.admin` then users in the role will be able to modify the name, permissions,
and other properties of the `m.admin` role. This can mean that the user might be able to modify a role they
are currently assigned to.

`m.assign` denotes which roles a user in the applicable role will be able to assign (add) to users in
the room. This would be done through the `m.roles` property of the target user's membership event. The user
is able to target themselves.

`m.revoke` is the opposite of `m.assign`: it is which roles users in the applicable role will be able
to *remove* from a user's `m.roles` array on their membership event. Users are still able to target themselves
here.

When the server is creating the default `m.admin` role, the following permission body is to be used:

```json
{
  "m.change": ["*"],
  "m.assign": ["*"],
  "m.revoke": ["*"]
}
```

### Use-case adoption

Not all rooms will require the changes proposed here, and thus it may be important to support the existing
power levels structure in parallel. Some potential solutions for this include sending state events into
a room to indicate the switch of systems, however this could potentially cause problems with authorization
if a server were to miss an event. This proposal offers an awkward, but hopefully viable, solution that
may be extended to other similar features in the future.

Room versions reserved by the Matrix protocol ending with `.1` are indicative of the server supporting
the principles of that room version with the role system proposed here used in place of `m.room.power_levels`.
For the purposes of authorization rules, this proposal does not support room versions 1 through 5 as
currently reserved by the specification - the minimum viable set of authorization rules are a modified
v6 set as described later in this proposal.

The specification will remain responsible for defining what the `.1` version of a room version looks like,
when new versions are being introduced.

**Rationale**: The specification reserves room versions consisting of `[0-9.]` for use by the protocol,
but does not reserve anything using `[a-z\-]` as otherwise allowed by room versions. Ideally, the protocol
would have reserved a dash and some letters to assist with denoting various features that may be included
in a given room version, however `.1` works just as well.

For clarity: room version `6.1` would mean the room uses a role-based permission system while room version
`6` uses the existing power levels structure. When room version `7` is introduced through an MSC, it would
also define a `7.1` with any modifications required to continue supporting a role-based approach.

This proposal does not include a solution for custom room versions intentionally. Implementations using
custom room versions are welcome to invent their own scheme for identifying role-based approach usage.

### Expected server behaviour for profile/membership changes

***TODO - This needs defining***

### Precise changes to v6's authorization rules

Using room version 6 as a reference for authorization rules, the authorization rules for this MSC
would be as follows.

For determining whether a given user in a given room has a given permission:

* If the user's membership is not `join`, the user does not have any permissions.
* For each role ID defined by the `m.roles` array (default empty, ordered) on the user's membership event:
  * If there is no associated `m.role` state event in the room, skip.
  * If the `m.role` state event does not have an English name, skip.
  * Interpret the permission on the `m.role` state event to a single boolean flag to denote whether
    the user is allowed (true) or disallowed (false) to continue.
    * For unknown permission types (eg: custom namespaces), the default is to imply disallowed.
  * If the user is granted (allowed) the permission, return true to let the user continue the action.
  * If no roles have granted (allowed) the permission, return false to deny the user's action.

For authorizing events themselves:

***TODO - This needs defining***

## Potential issues

Roles are controversial as a power scheme and moderation structure - this is why the proposal actively
tries to keep the `m.room.power_levels` around. A roles approach is often better bridged to some
platforms (like Discord), whereas a power levels approach has a much stronger use case for others.
Similarly, it can be argued by several communities that roles are more natural feeling while other
communities will argue that power levels are more natural - it's largely a matter of preference and
community-specific interactions which define which is "better".

This roles approach is quite confusing as well and may lead to several implementation issues. This
MSC, and the relevant specification if this MSC makes it that far, should include examples ranging
from simple to complex for implementations to test against. As the ecosystem makes more general use
of a roles-based approach, those examples should be updated to better represent what is available
in the wild.

As already discussed, the room version identification approach is suboptimal but appears to be a
good enough compromise pending larger discussions with members of the ecosystem. Refer to that
section for more information.

## Alternatives

Roles are already an alternative to existing permissions model. By extension, there are several other
systems which may be valuable and have their own merits. The intention of this proposal is to
demonstrate an opt-in style permissions systems for the rooms/communities which have a requirement
to use such a system. It is not proposed that this system become the default under any circumstance
for all of Matrix.

## Security considerations

Changing the entire permissions system is dangerous and could lead to multiple security vulnerabilities.
Many have been already solved or considered by the existing power level system, and where possible
those semantics have been brought into this proposal.

TODO: There's certainly more words that can be put here, such as why roles are the way they are.

## Unstable prefix

Implementations should use a room version of `org.matrix.msc2812` while this MSC is not in a published
version of the specification. Because all the events would be isolated to this highly customized
room version, there is no requirement to avoid the usage of the `m.*` namespace.
