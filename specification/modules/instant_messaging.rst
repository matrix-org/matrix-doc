Instant Messaging
=================

.. _module:im:

This module adds support for sending human-readable messages to a room. It also
adds support for associating human-readable information with the room itself
such as a room name and topic.

Events
------

{{m_room_message_event}}

{{m_room_message_feedback_event}}

Usage of this event is discouraged for several reasons:
 - The number of feedback events will grow very quickly with the number of users
   in the room. This event provides no way to "batch" feedback, unlike the
   `receipts module`_.
 - Pairing feedback to messages gets complicated when paginating as feedback
   arrives before the message it is acknowledging.
 - There are no guarantees that the client has seen the event ID being
   acknowledged.


.. _`receipts module`: `module:receipts`_

{{m_room_name_event}}

{{m_room_topic_event}}

{{m_room_avatar_event}}

m.room.message msgtypes
~~~~~~~~~~~~~~~~~~~~~~~

Each `m.room.message`_ MUST have a ``msgtype`` key which identifies the type
of message being sent. Each type has their own required and optional keys, as
outlined below. If a client cannot display the given ``msgtype`` then it SHOULD
display the fallback plain text ``body`` key instead.

{{msgtype_events}}


Client behaviour
----------------

Clients SHOULD verify the structure of incoming events to ensure that the
expected keys exist and that they are of the right type. Clients can discard
malformed events or display a placeholder message to the user. Redacted
``m.room.message`` events MUST be removed from the client. This can either be
replaced with placeholder text (e.g. "[REDACTED]") or the redacted message can
be removed entirely from the messages view.

Events which have attachments (e.g. ``m.image``, ``m.file``) SHOULD be
uploaded using the `content repository module`_ where available. The
resulting ``mxc://`` URI can then be used in the ``url`` key.

.. _`content repository module`: `module:content`_

Recommendations when sending messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients can send messages using ``POST`` or ``PUT`` requests. Clients SHOULD use
``PUT`` requests with `transaction IDs`_ to make requests idempotent. This
ensures that messages are sent exactly once even under poor network conditions.
Clients SHOULD retry requests using an exponential-backoff algorithm for a
certain amount of time T. It is recommended that T is no longer than 5 minutes.
After this time, the client should stop retrying and mark the message as "unsent".
Users should be able to manually resend unsent messages.

Users may type several messages at once and send them all in quick succession.
Clients SHOULD preserve the order in which they were sent by the user. This
means that clients should wait for the response to the previous request before
sending the next request. This can lead to head-of-line blocking. In order to
reduce the impact of head-of-line blocking, clients should use a queue per room
rather than a global queue, as ordering is only relevant within a single room
rather than between rooms.

.. _`transaction IDs`: `sect:txn_ids`_

Local echo
~~~~~~~~~~

Messages SHOULD appear immediately in the message view when a user presses the
"send" button. This should occur even if the message is still sending. This is
referred to as "local echo". Clients SHOULD implement "local echo" of messages.
Clients MAY display messages in a different format to indicate that the server
has not processed the message. This format should be removed when the server
responds.

Clients need to be able to match the message they are sending with the same
message which they receive from the event stream. The echo of the same message
from the event stream is referred to as "remote echo". Both echoes need to be
identified as the same message in order to prevent duplicate messages being
displayed. Ideally this pairing would occur transparently to the user: the UI
would not flicker as it transitions from local to remote. Flickering cannot be
fully avoided in the current client-server API. Two scenarios need to be
considered:

- The client sends a message and the remote echo arrives on the event stream
  *after* the request to send the message completes.
- The client sends a message and the remote echo arrives on the event stream
  *before* the request to send the message completes.

In the first scenario, the client will receive an event ID when the request to
send the message completes. This ID can be used to identify the duplicate event
when it arrives on the event stream. However, in the second scenario, the event
arrives before the client has obtained an event ID. This makes it impossible to
identify it as a duplicate event. This results in the client displaying the
message twice for a fraction of a second before the the original request to send
the message completes. Once it completes, the client can take remedial actions
to remove the duplicate event by looking for duplicate event IDs. A future version
of the client-server API will resolve this by attaching the transaction ID of the
sending request to the event itself.


Calculating the display name for a user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients may wish to show the human-readable display name of the room member who
send a message, and in lists of room members. However, different members may
have conflicting displaynames; care should be taken to ensure that displaynames
are disambiguated before showing them to the user.

To ensure this is done consistently across clients, clients SHOULD use the
following algorithm to calculate a disambiguated display name for a given user:

1. Inspect the ``m.room.member`` state event for the relevant user id.
2. If the ``m.room.member`` state event has no ``displayname`` field, or if
   that field has a null value, use the raw user id as the display name.
3. If the ``displayname`` is unique among members of the room with
   ``membership: join``, use the given ``displayname`` as the user-visible
   display name
4. The given ``displayname`` must be disambiguated using the user id, for
   example "displayname (@id:homeserver.org)". Clients MAY format the display
   name differently, provided both components are present.

Developers should take note of the following when implementing the above
algorithm:

* A corollary of this algorithm is that the user-visible display name of one
  member can be affected by changes in the state of another member. For
  example, if ``@user1:matrix.org`` is present in a room, with ``displayname:
  Alice``, then when ``@user2:example.com`` joins the room, also with
  ``displayname: Alice``, *both* users must be given disambiguated display
  names. Similarly, when one of the users then changes their display name,
  there is no longer a clash, and *both* users can be given their chosen
  display name.

  Clients should be alert to this possibility and ensure that all affected
  users are correctly renamed.

* Furthermore, because the display name of a room may be based on the display
  name of users (see `Calculating the display name for a room`_), the display
  name of a room may also be affected by changes to the membership of a room.

* A naïve implementation of this algorithm can be inefficient: if the entire
  user list is searched for clashing displaynames, this leads to an O(N^2)
  implementation for building the list of room members, which is very slow for
  rooms with large numbers of members.

  It is recommended that client implementations maintain a hash table mapping
  from ``displayname`` to a list of room members using that displayname; this
  can then be used for efficient calculation of whether disambiguation is
  needed.

A future version of the client-server API will make this process easier for
clients by indicating whether or not a ``displayname`` is unique.


Displaying membership information with messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients may wish to show the display name and avatar URL of the room member who
sent a message. This can be achieved by inspecting the ``m.room.member`` state
event for that user ID (see `Calculating the display name for a user`_).

When a user paginates the message history, clients may wish to show the
**historical** display name and avatar URL for a room member. This is possible
because older ``m.room.member`` events are returned when paginating. This can
be implemented efficiently by keeping two sets of room state: old and current.
As new events arrive and/or the user paginates back in time, these two sets of
state diverge from each other. New events update the current state and paginated
events update the old state. When paginated events are processed sequentially,
the old state represents the state of the room *at the time the event was sent*.
This can then be used to set the historical display name and avatar URL.


Calculating the display name for a room
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients will need to show a human-readable name for a room. There are a number
of possibilities for choosing a useful name. To ensure that rooms are named
consistently across clients, clients SHOULD use the following algorithm to
choose a name:

1. If the room has an `m.room.name`_ state event, use the name given by that
   event.
#. If the room has an `m.room.canonical_alias`_ state event, use the alias
   given by that event.
#. If neither of the above events are present, a name should be composed based/sys/class/backlight/intel_backlight/brightness
   on the members of the room. Clients should consider `m.room.member`_ events
   for users other than the logged in user, with ``membership: join`` or
   ``membership: invite``.

   i. If there is only one such event, the display name for the room should be
      the `disambiguated display name`_ of the corresponding user.

   #. If there are two such events, they should be lexicographically sorted by
      their ``state_key`` (i.e. the corresponding user IDs), and the display
      name for the room should be the  `disambiguated display name`_ of both
      users: "<user1> and <user2>", or a localised variant thereof.

   #. If there are three or more such events, the display name for the room
      should be based on the disambiguated display name of the user
      corresponding to the first such event, under a lexicographical sorting
      according to their ``state_key``: "<user1> and <N> others", or a
      localised variant thereof.

   .. TODO-spec
     Sorting by user_id certainly isn't ideal, as IDs at the start of the
     alphabet will end up dominating room names: they will all be called
     "Arathorn and 15 others". Ideally we might sort by the time when the user
     was first invited to, or first joined the room. But we don't have this
     information.

#. If the room has no ``m.room.name`` or ``m.room.canonical_alias`` events, and
   it has no active members other than the current user, the there are no
   active members, the Room ID of the room should be used as the display name.

.. _`disambiguated display name`: `Calculating the display name for a user`_

Clients MUST NOT use `m.room.aliases`_ events as a source for room names, as
aliases are not necessarily suitable for display.

.. TODO-spec
  How can we make this less painful for clients to implement, without forcing
  an English-language implementation on them all?


Server behaviour
----------------

Homeservers SHOULD reject ``m.room.message`` events which don't have a
``msgtype`` key, or which don't have a textual ``body`` key, with an HTTP status
code of 400.

Security considerations
-----------------------

Messages sent using this module are not encrypted. Messages can be encrypted
using the `E2E module`_.

Clients should sanitise **all displayed keys** for unsafe HTML to prevent Cross-Site
Scripting (XSS) attacks. This includes room names and topics.

.. _`E2E module`: `module:e2e`_

