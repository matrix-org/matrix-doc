# MSC2785: Event notification attributes and actions

   * [Background: the problems with push rules](#background-the-problems-with-push-rules)
   * [Proposal](#proposal)
      * [Event notification attributes](#event-notification-attributes)
         * [Events received by the same user that sent them](#events-received-by-the-same-user-that-sent-them)
         * [Configuration data for notification attributes](#configuration-data-for-notification-attributes)
         * [m.keyword](#mkeyword)
         * [m.mention](#mmention)
         * [m.invite](#minvite)
         * [m.room_upgrade](#mroom_upgrade)
         * [m.voip_call](#mvoip_call)
         * [m.msg](#mmsg)
         * [m.dm](#mdm)
      * [Event notification actions](#event-notification-actions)
         * [Mapping from attributes to actions](#mapping-from-attributes-to-actions)
      * [Special handling for encrypted events](#special-handling-for-encrypted-events)
      * [APIs for updating the configuration](#apis-for-updating-the-configuration)
         * [GET /_matrix/client/r0/notification_attribute_data/global/keywords](#get-_matrixclientr0notification_attribute_dataglobalkeywords)
         * [PUT /_matrix/client/r0/notification_attribute_data/global/keywords](#put-_matrixclientr0notification_attribute_dataglobalkeywords)
         * [GET /_matrix/client/r0/notification_attribute_data/global/mentions](#get-_matrixclientr0notification_attribute_dataglobalmentions)
         * [PUT /_matrix/client/r0/notification_attribute_data/global/mentions](#put-_matrixclientr0notification_attribute_dataglobalmentions)
         * [TODO: APIs for manipulating notifications profiles](#todo-apis-for-manipulating-notifications-profiles)
      * [Backwards compatibility](#backwards-compatibility)
      * [Outstanding issues to be resolved](#outstanding-issues-to-be-resolved)
   * [Potential issues](#potential-issues)
   * [Alternatives](#alternatives)
      * [Extend use of push rules](#extend-use-of-push-rules)
   * [Security considerations](#security-considerations)
   * [Unstable prefix](#unstable-prefix)

## Background: the problems with push rules

["Push rules"](https://matrix.org/docs/spec/client_server/r0.6.1#push-rules)
provide an interface which allows Matrix clients and users to
configure various actions to be performed on receipt of certain events, such as
showing a pop-up notification or playing a sound.

Originally, push rules were intended to be interpreted only by homeservers
(they would direct the server how to "push" the event to mobile devices via a
push gateway). Later, as encrypted events became more common, and desktop
clients wanted to offer native notifications, it also became necessary for
clients to be able to process push rules.

Experience has shown that push rules do not have enough flexibility to provide
the features expected by users. This proposal suggests an alternative data
model and API set which could be used for configuring notifications.

## Proposal

We break down the notifications process into two distinct phases. Firstly, the
homeserver and/or client analyses each event and assigns a set of _attributes_
to the events. Secondly, the homeserver/client follows a set of rules which
define which _actions_ should be performed for a given set of attributes -
where the rules can vary by room.

### Event notification attributes

The first step is to analyse each event as it arrives, and assign zero or more
*event notification attributes* to that event. This must be done by both
homeservers (to support http or email "push"), *as well as* by any client which
wants to support this notification system. The attributes assigned may vary
between users, so homeservers must follow this algorithm for each user who
receives an event.

Event notification attributes consist of an identifier matching the [common
namespaced identifier grammar](https://github.com/matrix-org/matrix-doc/pull/2758).
The algorithm for assigning each attribute is defined in detail in following
sections; a summary follows here:

 * `m.keyword`: The event contains one of the user's registered "notification
   keywords".
 * `m.mention`: The event contains a "mention" of the user's userid, etc.
 * `m.invite`: The event is an invitation to a room.
 * `m.room_upgrade`: The event is a notification that a room has been upgraded.
 * `m.voip_call`: The event is an invitation to a VoIP call.
 * `m.dm`: The event was in a Direct Message room.
 * `m.msg`: The event contains a visible body.

#### Events received by the same user that sent them

Events sent by a user are not expected to cause any notification actions when
they are received by that same user (whether on the same or a different
device), so are excluded from this process.

#### Configuration data for notification attributes

The assignment of event notification attributes has a limited amount of
configuration. This information is stored in an
[`account_data`](https://matrix.org/docs/spec/client_server/r0.6.1#id125) event
of type `m.notification_attribute_data`, and with content with the following
structure:

```json
{
  "keywords": ["foo", "bar", "longer string"],
  "mentions": {
     "displayname": true,
     "mxid": true,
     "localpart": true,
     "room_notif": true
  }
}
```

This event can be set at the global level. (Room-level overrides will be a
future extension.)

The properties within the event content are defined as follows:

 * `keywords`: an array of strings which form "notification keywords". See
   `m.keyword` below. If `keywords` is absent, the list is implicitly empty.

 * `mentions`: an object containing booleans which define which events should
   qualify for `m.mention` attributes. See `m.mention` below. Each of the four
   settings above (`displayname`, `mxid`, `localpart`, `room_notif`) defaults
   to `false` if not present.

   If the whole `mentions` property is absent, all the inner attributes take
   their default values (ie, `false`).

Homeservers should check the content of any uploaded
`m.notification_attribute_data` events, and reject any malformed events with a
400 error and `M_BAD_JSON`. However, implementations should be resilient to
malformed data.

#### `m.keyword`

Indicates that the event contained one of the user's configured "notification
keywords". Implementations should determine whether to set this attribute as
follows.

Any event with no `body` property, or an empty `body` property, or a `body` property
which is not a string, should *not* match.

Otherwise, the `body` of the event is compared with the user's current
`keywords` list from the `m.notification_attribute_data` event, using a
case-insensitive, unicode-normalised search for whole words. If any of the
strings in the `keywords` list matches, the `m.keyword` attribute should be
set.

If any entry in the `keywords` list is not a simple string, that entry is
ignored, and other entries in the list are treated normally. If there is no
`keywords` property in the `m.notification_attribute_data` event (or it is not an
array), then no event will match.

[UAX#29](https://unicode.org/reports/tr29/#Word_Boundaries) describes
algorithms for determining word boundaries for whole word search; we recommend
that implementations follow the specifications there as closely as possible for
consistency between implementations (but it may be appropriate for some
implementations to use simpler algorithms, or change the algorithm depending on
the user's preferred language).

To ensure that different unicode representations of the same character match,
implementations should case-fold and unicode-normalise both the event body and
the search keywords before
comparing. The [Unicode normalization
FAQ](https://unicode.org/faq/normalization.html) recommends the NFC
normalization form for this purpose.

#### `m.mention`

Indicates that the event contains a "mention" of the user's name or id.
Implementations should determine whether to set this attribute as follows.

Any event with no `body` property, or an empty `body` property, or a `body` property
which is not a string, should *not* match.

Otherwise, the `body` of the event is inspected for whole-word matches. The
words to be matched are controlled by the `mentions` property in the user's
`m.notification_attribute_data` event:

 * `displayname`: a case-folded, unicode-normalised match for the user's
   display name in the room containing the event as given by the `displayname`
   property of their `m.room.member` event. If the `m.room.member` event does
   not contain a `displayname` property, there is no match.

 * `mxid`: an exact, case-sensitive match for the user's complete Matrix user ID.

 * `localpart`: a case-*insensitive* match for the local part of the user's
   mxid. (MXIDs cannot contain non-ascii characters, so unicode denormalisation
   is redundant.)

 * `room_notif`: a case-*insensitive* match for the string `@room`, provided
   the sender of the event has power level greater or equal to that required
   for `notifications`.

#### `m.invite`

Indicates a room invite for the recipient (ie, an `m.room.member` event for the
user with `membership: invite`).

#### `m.room_upgrade`

An `m.room.tombstone` state event with an empty `state_key`.

#### `m.voip_call`

An `m.call.invite` non-state event.

#### `m.msg`

Any event with a `body` attribute which is a non-empty string.

#### `m.dm`

An event which occurs in a Direct Message room (that is, a room which appears
in the user's
[`m.direct`](https://matrix.org/docs/spec/client_server/r0.6.1#m-direct)
`account_data` event.

### Event notification actions

Having assigned attributes to events, the next step is for implementations to
pick actions based on those attributes.

Event notification actions also have identifiers using the the [common
namespaced identifier
grammar](https://github.com/matrix-org/matrix-doc/pull/2758). The following
actions are defined initially:

 * `m.notify`: clients should show a "native notification" appropriate to the
   platform. For example, a webapp might show a [desktop
   notification](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API).
   Mobile devices also have conventions for such notifications:
   [Android](https://developer.android.com/guide/topics/ui/notifiers/notifications),
   [iOS](https://support.apple.com/en-gb/HT201925).

   Servers should also send pushes to the user's registered pushers for each
   event with the `m.notify` action. This supports mobile clients (via the `http`
   pusher mechanism and the [push
   API](https://matrix.org/docs/spec/push_gateway/r0.1.1#post-matrix-push-v1-notify))
   as well as supporting email notifications for missed messages (via the
   `email` pusher mechanism).

   XXX: should we send actions/attributes over push?

   This action also causes the event to be returned via future calls to the
   [`/notifications`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-notifications)
   API endpoint.

 * `m.sound`: Clients should play an audible alert for this event. It is up to
   the client implementation to decide which sound to play based on the content
   of the event (and it is expected that different client implementations will
   want to use different sounds).

   It is also expected that there will be no audible alert if there is no
   visible UI (eg, in the case of a mobile client where that client is
   backgrounded and there is no accompanying `m.notify`).

 * `m.highlight`: Clients should "highlight" the room containing the event in
   some way. Note that this is distinct from rooms containing other unread
   messages. (For example, Element Web displays a red badge in the room list
   for a highlight, and uses a bold font for rooms with unread messages.)

   Note also that this does not necessarily imply that the event causing the
   action should be "highlighted" in the timeline: clients wishing to offer
   such a user experience are expected to parse the event bodies themselves and
   compare against the user's keyword and mention settings.

#### Mapping from attributes to actions

The mapping from attributes to actions depends on the user's "notifications
profile". This is a setting on the user's account which is stored in an
`account_data` event of type `m.notifications_profile`, and with content with
the following structure:

```json
{
    "profile": "normal"
}
```

In future, per-device overrides of this setting could be supported. No facility
to override at the room level is expected.

The `profile` property refers to an `account_data` event of type
`m.notifications_profile.<profile>`, and is composed of the characters `[a-z]`,
`[0-9]`, `-`, and `_`.

The `m.notifications_profile.<profile>` event has the following content
structure:

```json
{
  "actions": {
    "m.notify": [
        "m.mention", "m.keyword", "m.invite", "m.room_upgrade",
        "m.voip_call", ["m.dm", "m.msg"]
    ],
    "m.sound": [
        "m.mention", "m.keyword", "m.invite", "m.room_upgrade",
        "m.voip_call", ["m.dm", "m.msg"]
    ],
    "m.highlight": ["m.mention", "m.keyword"]
  }
}
```

Each entry in the `actions` property is the name of an action, and a list of
the notification attributes which trigger it. Each entry in the list is either
a single attribute which will trigger the action, or a list of attributes which
must *all* be satisfied to trigger the action.

An absent `actions` property means the same as an empty one: no actions are
triggered by any events. Similarly, if the profile referred to in the
`m.notifications_profile` event does not exist, then no actions are triggered.

An `m.notifications_profile.<profile>` event can also be set at the room level,
using the same structure. This gives overrides specific to that room. If an
action is listed in the room-level `account_data` event, then the list of
attributes which trigger that action is replaced by the data from the
room-level event. For example, given the following room-level
`m.notifications_profile.normal` event:

```json
{
  "actions": {
    "m.notify": [
        "m.mention", "m.keyword", "m.invite", "m.room_upgrade",
        "m.voip_call", "m.msg"
    ],
    "m.sound": []
  }
}
```

then, for events in that room:
 * `m.notify` is triggered by all events with any of the listed attributes
   including `m.msg`.
 * `m.sound` is never triggered.
 * The attributes triggering `m.highlight` are taken from the global event.

Homeservers should check the structure of any uploaded
`m.notifications_profile` and `m.notifications_profile.<id>` events, and reject
any malformed events with a 400 error and `M_BAD_JSON`. However,
implementations should be resilient to malformed data. Homeservers should allow
unrecognised actions or attributes to be referenced in the mapping, to allow
future extension.

The `none` profile id is reserved, and servers should not allow clients to
upload `m.notifications_profile.none` events. This can be used to disable all
notifications without discarding other configuration that the user may have
set.

We don't specify a "default" notification profile, leaving it up to the server
implementation to provide sensible defaults. The example shown above is
anticipated to be a good starting point.

### Special handling for encrypted events

Encrypted events necessitate some special handling.

Firstly, clients must decrypt events before assigning notification
attributes. They can then proceed as normal with the rest of the algorithm. (In
practice, they may be able to optimise this process: for example, some
attributes such as `m.dm` can be can be calculated without decryption; if the
user's notification profile has no mappings which are dependent on the
decrypted content of an event, there is no need to decrypt.)

Homeservers cannot decrypt events, so must proceed as if every event could
cause a notification. In particular:

 * For HTTP pushers, homeservers must send a push for each encrypted event
   which *could* cause an `m.notify` action once decrypted (so, for example,
   the server can elide pushes for any room where the `m.notify` action list
   is empty for that user).

 * Handling of encrypted events for email pushers is left as an implementation
   choice.

If more flexibility is required here in future, we could consider extending the
[`POST /_matrix/client/r0/pushers/set`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-pushers-set)
API to allow clients to configure the desired behaviour.

### APIs for updating the configuration

A number of APIs are defined to allow the configuration data to be atomically
manipulated and interrogated at a finer level. These are defined as follows.

#### `GET /_matrix/client/r0/notification_attribute_data/global/keywords`

The body of the response to this request is the user's current global keyword
list, as follows:

```json
{
  "keywords": ["foo", "bar", "longer string"]
}
```

The `keywords` attribute is always present, even if the list is empty.

#### `PUT /_matrix/client/r0/notification_attribute_data/global/keywords`

This endpoint replaces the user's global keyword list. The request body takes
the form:

```json
{
  "keywords": ["foo", "bar", "longer string"]
}
```

It is invalid to make this request with no `keywords` attribute.

On success, the response is an empty object:

```json
{}
```


#### `GET /_matrix/client/r0/notification_attribute_data/global/mentions`

The body of the response to this request is the user's current global mentions
settings, as follows:

```json
{
  "mentions": {
     "displayname": true,
     "mxid": true,
     "room_notif": true,
  }
}
```

All of the attributes defined above are required, even if they have their default
values.

#### `PUT /_matrix/client/r0/notification_attribute_data/global/mentions`

This endpoint updates the user's global mentions settings. The request body takes
the form:

```json
{
  "mentions": {
     "displayname": true,
     "mxid": true,
     "localpart": true,
     "room_notif": true
  }
}
```

Any attributes that are absent are reset to their defaults (ie, `false`). It is
invalid to omit the entire `mentions` attribute.

On success, the response is an empty object:

```json
{}
```

#### TODO: APIs for manipulating notifications profiles

TBD: do we need anything here, or do clients just twiddle the account_data
event directly?

### Backwards compatibility

We deprecate the entire
[push rules](https://matrix.org/docs/spec/client_server/r0.6.1#push-rules) system,
including the
[`/pushrules`](https://matrix.org/docs/spec/client_server/r0.6.1#push-rules-api)
API endpoints for configuring push rules, and the
[`m.push_rules`](https://matrix.org/docs/spec/client_server/r0.6.1#push-rules-events)
`account_data` event. (Note that the
[`/pushers`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-pushers)
and
[`/notifications`](https://matrix.org/docs/spec/client_server/r0.6.1#listing-notifications)
APIs are unchanged).

In order to support clients using the existing pushrules system as best we can,
we do the following:

 * Servers map users' existing pushrules as best they can onto notification
   attribute settings and a notifications profile.
 * Any attempt to change pushrules results in an HTTP error (403?).
 * Read APIs return the last known state of pushrules. (For users created after
   the switch to the new system, the read APIs return the default
   state).
 * Likewise, the `m.push_rules` account_data event is populated with the last
   known, or default, pushrules state.

To allow a smooth migration, clients must support both the old pushrules and
the new notification attributes/actions system until such time as they choose
to drop support for older server versions.

### Outstanding issues to be resolved

* Synapse currently has a
  [hack](https://github.com/matrix-org/synapse/blob/v1.19.2/synapse/push/httppusher.py#L304-L311)
  which sets the "priority" of pushes based on some apparently arbitrary
  heuristics. We can no doubt replicate that hack, but its presence suggests
  that we may need to figure out how to prioritise pushes, and possibly allow
  its configuration.

## Potential issues

* If a user has lots of profiles, an initial sync will include a bunch of
  redundant data.
* Should we worry about clients fighting over the notification profile
  namespace?

## Alternatives

### Extend use of push rules

Before this proposal, we gave considerable thought to how we might extend the
use of Push Rules to meet user expectations.

Whilst in theory they are very flexible,
it is often necessary to use tens of rules to express simple-sounding
requirements. To give some examples:

 * Suppose the user wants to configure certain rooms to be "highlighted" when
   their name is mentioned, but they do not want to hear an audible alert in
   those rooms. (In other rooms, they want both a highlight *and* and audible
   alert.)

   "Mentions" are implemented by eight separate push rules, including rules to
   filter out mentions in `m.room.notice` and edit events. Each "keyword" gets
   its own rule too. So for that one room, where we want to change the
   behaviour of mentions and keywords, we would have to repeat each of those
   8+N rules.

 * Suppose the user configures a particular room so that they receive a visible
   notification and an audible alert for each message. Later, the user disables
   audible alerts at the account level; this means that the account-level
   "mention" and "keyword" rules are reconfigured so that there is no audible
   alert.

   The problem concerns how to handle the user's original room-level
   configuration. There are two unsatisfactory options:

   * Leaving the room configuration in place would mean that they would mean
     that the user would get audible notifications for all messages in that
     room *except* mentions and keywords.

   * Removing the room configuration would at least give consistent behaviour,
     but it will be surprising for the user that their room-level configuration
     is affected by account-level configuration.

Whilst it is *possible* to create sets of push rules that meet the user's
expectations, it then becomes very difficult to go from the long list of rules
back to the user's intentions to populate a configuration interface. This is
further exacerbated by the fact that different clients might take the same set
of user intentions and populate the push rules in slightly different ways.

Long, detailed lists of push rules would also make it very difficult to extend
Matrix in the future without breaking users' existing push rules. For example:
a currently proposed change to the push rules implementation is that
`m.reaction` events should not cause a visible notification by default (see
[MSC2153](https://github.com/matrix-org/matrix-doc/pull/2153)). This would be
an order of magnitude harder to do if each user had hundreds of different
copies of the default push rules, fine-tuning the behaviour for each room.


## Security considerations

None identified at this time.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during
development:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`m.notification_attribute_data` | `account_data` event type | `org.matrix.msc2785.notification_attribute_data`
`m.notifications_profile` | `account_data` event types | `org.matrix.msc2785.notifications_profile`
`/_matrix/client/r0/notification_attribute_data/...` | API endpoints | `/_matrix/client/unstable/org.matrix.msc2785/notification_attribute_data`
