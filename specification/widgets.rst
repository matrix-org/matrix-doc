.. Copyright 2020 The Matrix.org Foundation C.I.C.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Widgets
=======

{{unstable_warning_block_WIDGETS_RELEASE_LABEL}}

Widgets are client-side embedded applications which can communicate with Matrix clients. Widgets
are often used to present information to users and allow them to more interactively collaborate.

Due to platform constraints, unreasonable implementation effort, and client-specific design choices,
widgets are optional in Matrix. Clients are encouraged to support widgets if possible and reasonable,
though degraded behaviour, such as "open in browser" links, is considered acceptable by this
specification.

.. contents:: Table of Contents
.. sectnum::

Changelog
---------

.. topic:: Version: %WIDGETS_RELEASE_LABEL%
{{widgets_changelog}}

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

For the full historical changelog, see
https://github.com/matrix-org/matrix-doc/blob/master/changelogs/widgets.rst

Other versions of this specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following other versions are also available, in reverse chronological order:

- `HEAD <https://matrix.org/docs/spec/widgets/unstable.html>`_: Includes all changes since the latest versioned release.

API Standards
-------------

Throughout this specification, a "client" is referred to as something which is rendering/supporting
("hosting") widgets. Widgets are unique in that they can be considered a client when referred to in
a typical network setting, though this specification ensures that a widget is always referred to as
a "widget" and the term "client" is solely reserved for the widget's host application. Note that
widgets can be hosts to widgets - deciphering which role is which in this context is left as an
exercise for the reader.

The mandatory baseline for a widget is a typical website with the optional communication protocol
described here. When communicating with a Matrix client, the mandatory baseline is the `JavaScript
postMessage API <https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage>`_ using the
protocol described by this specification. In the future more accessible transports for clients will
be considered as optional extensions, such as using operating system-specific hooks.

All objects exchanged over the Widget (``postMessage``) API are JSON objects.

In essence, widgets are typically iframes or the platform equivilant to a website which are accessible
in the client.

All of the schemas in this specification are intended to be referenced by name, and thus can safely
be used in auto-generated implementations which rely on stable naming.

Widget Kinds
------------

Widgets currently can exist in the following places:

* Within rooms, accessible by members/observers of the room.
* For a particular user, accessible only by that user.

{{definition_widgets_shared_props}}

Room Widgets
~~~~~~~~~~~~

Room widgets are defined by state events in the room, and are as such accessible to anyone who is
able to see the state of the room. Widgets can individually apply additional access restrictions
such as preventing non-joined members of the room from accessing the widget's functionality.

Clients MUST NOT show room widgets to the user unless the user is viewing that room or unless the
widget has set an appropriate always-on-screen request through the Widget API.

The ``state_key`` for a room widget MUST match the widget's ``id``. Due to this association, new
widgets in the room must use a unique ``state_key`` (and therefore ``id``). Widgets can be
updated by sending a new state event for the widget's ``state_key``.

Invalid room widgets MUST NOT be shown to users. This is also how widgets are removed from a room:
send a new state event for the same widget ID with at least the ``url`` and/or ``type`` missing
from the event content. Once Matrix allows for state events to be properly deleted then doing so
to the widget state event will be just as valid to remove it from the room.

.. WARNING::
    Do not store sensitive information such as tokens, secrets, or passwords
    in the widget data as it can be viewed by anyone who can see the room state.

{{m_widget_event}}

Account Widgets
~~~~~~~~~~~~~~~

Account widgets are defined in the user's account data, and are as such only visible to them.
Widgets can individually apply additional access restrictions as needed. Account widgets are
not linked to any particular room.

Account widgets are represented under the ``m.widgets`` account data event as a map of widget ID
to definition. As such, the widget's ``id`` must be unique within this object's properties. The
definition for an account widget is nearly equivilant to a room widget's state event representation,
using the ``type``, ``state_key``, ``sender``, and ``content`` fields of the state event.

Account widgets can be added by adding a new key to the ``m.widgets`` account data, edited by
modifying the appropriate ``AccountWidget`` definition, or deleted by simply removing the appropriate
property from the ``m.widgets`` acount data.

.. WARNING::
    Do not store sensitive information such as tokens, secrets, or passwords
    in the widget data as it is not secure or encrypted.

{{m_widgets_event}}


Rendering
---------

Widgets SHOULD be rendered using an iframe or platform equivilant. Clients can use platform-specific
rendering for widgets if they are confident in being able to do so, such as in the case of most
video conference widgets.

Clients SHOULD ask for permission to load a widget from the user prior to presenting the widget. If
the user was the last ``sender`` of a widget (not the ``creatorUserId``), the prompt can be skipped.
This prompt is strongly encouraged to ensure that users do not inadvertently send their information
to a third party. Private information such as the user's name, avatar, or IP address can be sent as
a result of how widgets work, and thus clients should attempt to prevent users from sending this
information unknowingly.

URL Templating
~~~~~~~~~~~~~~

The widget's URL is a template of what the client should render and should never be parsed by the
client to determine what the parameters are. All widgets make use of the ``data`` object to store
configuration-like values, which is also where clients should inspect for values needed to render
any UI.

Variable names for the template are the keys of the ``data`` object, with the values being the same
values of the object. Variables are included unencoded in the URL for population by the client, which
MUST use appropriate escaping to ensure the URL will be as valid as possible.

For example, given a ``data`` object like this::

  {
    "hello": "world",
    "answer": 42
  }

and a ``url`` of ``https://example.com?var1=$hello&answer=$answer`` the client MUST come up with
a URL of ``https://example.com?var1=world&answer=42`` to render. Complex types, such as objects and
arrays, for variable values do not have defined behaviour - widget creators are encouraged to stick
to "simple" types like numbers, strings, and booleans. Template variables can appear anywhere in the
URL.

Nested variables are not supported, and as such clients should be careful in their templating
approach. For example, if ``hello`` in the above example ``data`` was set to ``$answer``, the literal
value ``$answer`` would be included in the widget URL rather than ``42``.

As mentioned, clients must also encode values on behalf of the widget creator to maintain a valid
URL as much as possible. For example, ``test:value`` could become ``test%3Avalue`` when used as a
template variable value.

A few default variables, which MUST take priority over the same names in ``data``, are:

* ``matrix_user_id`` - The current user's ID.
* ``matrix_room_id`` - The room ID the user is currently viewing, or an empty string if none applicable.
* ``matrix_display_name`` - The current user's display name, or user ID if not set.
* ``matrix_avatar_url`` - The current user's avatar URL as reported in their profile, or and empty
  string if not present. This shouldn't be the ``mxc://`` form of the user's avatar, but instead the
  full HTTP URL to the ``/media/download`` endpoint for their avatar from the Client-Server API.
* ``matrix_widget_id`` - The widget's ID to allow the widget to communicate effectively with the client.

.. WARNING::
   The ``matrix_user_id`` variable MUST NOT be assumed to be the current authenticated user due to
   how trivial it is to provide false details with. Widgets which need to store per-user details
   or private information will need to verify the user's identity in some other way.

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~~

Clients SHOULD check to ensure that widgets are valid URLs *after* templating but *before* rendering
or asking for permission to load. Invalid URLs from the client's perspective should not be shown to
the user and can be treated as though no ``url`` was present (i.e.: a deleted/invalid widget).

Clients MUST NOT attempt to render widgets with schemes other than ``http:`` and ``https:``. Widgets
using alternative schemes, including template variables as schemes, are considered invalid and thus
should be ignored. This is to prevent widget creators from using ``javascript:`` or similar schemes
to gain access to the user's data.

Clients SHOULD apply a sandbox to their iframe or platform equivilant to ensure the widget cannot
get access to the data stored by the client, such as access tokens or cryptographic keys. More
information on origin restrictions is in the Widget API's security considerations section.

Clients should be aware of a potential `CSRF <https://owasp.org/www-community/attacks/csrf>`_
opportunity due to clients making arbitrary ``GET`` requests to URLs. Typical sites should not
be using ``GET`` as a state change method, though it is theoretically possible.

Widget Types
------------

A widget's ``type`` can be one of the following specified types or a custom type which preferably
uses the Java package naming convention as a namespace. Types prefixed with the ``m.`` namespace
are reserved by this specification.

Besides the ``type`` itself, widget types influence the widget's ``data`` by requiring specified
keys to exist. It is expected that the widget will use these keys as variables for their URL, though
this specification does not require such behaviour. Clients SHOULD treat widgets without the
required ``data`` properties for the types specified here as invalid widgets, thus not rendering
them.

Clients MUST treat widgets of unknown types as ``m.custom``, unless it is impossible for the client
to render the widget kind in that way. For example, custom widgets at the per-user rather than
per-room level might not be possible and thus can be treated as invalid (ignored).

Clients are not required to support all of these widget types (with the implied exception of
``m.custom``) as they can all be safely represented as ``m.custom`` widgets. Similarly, if a
widget fails the schema requirements for its ``type`` then it should be treated as ``m.custom``
by the client.

Custom/Basic Widgets
~~~~~~~~~~~~~~~~~~~~

Custom widgets are the most basic form of widget possible, and represent the default behaviour
for all widgets. They have an explicit widget ``type`` of ``m.custom``, though any
unknown/unsupported widget type for the client will be treated as a custom widget. They have
``data`` matching ``CustomWidgetData``.

{{definition_widgets_custom_data}}

Jitsi Meet Conferences
~~~~~~~~~~~~~~~~~~~~~~

`Jitsi Meet <https://jitsi.org/jitsi-meet/>`_ conferences can be held on a per-room basis with
a widget ``type`` of ``m.jitsi`` and ``data`` matching ``JitsiWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of room widgets.

{{definition_widgets_jitsi_data}}

Stickerpickers
~~~~~~~~~~~~~~

Stickerpickers are user widgets which allow the user to send ``m.sticker`` events to the current
room using the Widget API described by this specification. They have a widget ``type`` of
``m.stickerpicker`` and ``data`` which matches ``StickerpickerWidgetData``.

.. Note::
   Though technically possible, this widget type should not be used outside of user widgets.

{{definition_widgets_stickerpicker_data}}

Widget Wrappers
---------------

Most widgets in the wild are "wrapped" with some website that provides added functionality or
handles the Widget API communications. They have no formal specification as they are implicitly
handled as part of rendering widgets. As such, they also have no specific requirements to have
any particular behaviour.

A wrapper typically appears on a widget as a ``url`` pointing to a resource which then embeds
the content within another iframe. This allows the widget to be gated by authentication or be
more easily embedded within Matrix (as would be the case for Spotify and similar widgets - the
content to be embedded does not translate directly to a Matrix widget and instead needs a bit
of help from a wrapper to embed nicely).

Widget API
----------

The widget API is a bidirectional communication channel between the widget and the client, initiated
by either side. This communication happens over the `JavaScript postMessage API
<https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage>`_.

The API is split into two parts: ``fromWidget`` (widget -> client) and ``toWidget`` (client -> widget).
Both have the same general API shape: A request, called an ``action``, is sent to the other party
using the ``WidgetApiRequest`` schema. The other party then processes the request and returns an
object matching ``WidgetApiResponse``.

All communication is done within a "session", where the first message sent to either side indicates
the start of the session. Only the client can close/terminate a session by unloading/reloading the
widget.

The ``data`` of a ``WidgetApiRequest`` varies depending on the ``action`` of the request, as does the
``response`` of a ``WidgetApiResponse``.

{{definition_widgets_api_request}}

{{definition_widgets_api_response}}

Timeouts
~~~~~~~~

All requests sent over the API require a response from the other side, even if the response is to
just acknowledge that the request happened. Both widgets and clients should implement timeouts on
their requests to avoid them hanging forever. The default recommended timeout is 10 seconds, after
which the request should be considered not answered and failed. Requests can be retried if they are
failed, though some actions do not lend themselves well to idempotency.

Error Handling
~~~~~~~~~~~~~~

When the receiver fails to handle a request, it should acknowledge the request with an error response.
Note that this doesn't include timeouts, as the receiver will not have had an error processing the
request - it simply did not receive it in time.

An error response takes the shape of a ``WidgetApiErrorResponse``.

{{definition_widgets_api_error}}

Versioning
~~~~~~~~~~

The Widget API version tracks the version of this specification (``r0.1.0`` is Widget API version
``0.1.0``, for example). Both widgets and clients can perform a request with action of
``supported_api_versions`` (``SupportedVersionsActionRequest``) to get the other side's list of
supported versions (``SupportedVersionsActionResponse``). The sender SHOULD NOT use actions which
are unsupported by the intended destination. In the event that the sender and destination cannot
agree on a supported version, either side should abort their continued execution

Actions in this specification list which version they were introduced in for historical purposes.
Actions will always be backwards compatible with prior versions of the specification, though the
specification from time to time may add/remove actions as needed.

In order for a widget/client to support an API version, it MUST implement all actions supported
by that version. For clarity, all actions presented by this document at a given version are
supported by that version. Implicitly, the actions to request supported API versions are mandatory
for all implementations.

.. Note::
   For historical purposes, ``0.0.1`` and ``0.0.2`` are additionally valid versions which implement
   the same set as ``0.1.0`` (the first version of this specification).

{{definition_widgets_supported_versions_action_request}}

{{definition_widgets_supported_versions_action_response}}

Initiating Communication
~~~~~~~~~~~~~~~~~~~~~~~~

Immediately prior to rendering a widget, the client MUST prepare itself to handle communications
with the widget. Typically this will result in setting up appropriate event listeners for the
API requests.

If the widget was set up with ``waitForIframeLoad: false``, the widget will initiate the
communication by sending a ``fromWidget`` request with ``action`` of ``content_loaded`` (see below).
If  ``waitForIframeLoad`` was ``true``, the client will initiate communication once the iframe or
platform equivilant has loaded successfully (see ``waitForIframeLoad``'s description).

Once the client has established that the widget has loaded, as defined by ``waitForIframeLoad``,
it initiates a capabilities negotiation with the widget. This is done using the ``capabilities``
action on the ``toWidget`` API.

The capabilities negotiated set the stage for what the widget is allowed to do within the session.
Clients MUST NOT re-negotiate capabilities after the session has been established.

Prior to the session being initiated, neither side should be sending actions outside of those
required to set up the session. Version checking can happen at any time by either side, though
the initiator of the session should be left responsible for the first version check. For example,
if the client is waiting for a ``content_loaded`` action then the widget should be the one to
request the supported API versions first. Once a version check has been started by one side, it is
implied that the other side can do the same.

A broad sequence diagram for ``waitForIframeLoad: false`` is as follows::

  +---------+                                 +---------+
  | Client  |                                 | Widget  |
  +---------+                                 +---------+
      |                                           |
      | Render widget                             |
      |--------------                             |
      |             |                             |
      |<-------------                             |
      |                                           |
      |          `supported_api_versions` request |
      |<------------------------------------------|
      |                                           |
      | `supported_api_versions` response         |
      |------------------------------------------>|
      |                                           |
      | `supported_api_versions` request          |
      |------------------------------------------>|
      |                                           |
      |         `supported_api_versions` response |
      |<------------------------------------------|
      |                                           |
      |                  `content_loaded` request |
      |<------------------------------------------|
      |                                           |
      | Acknowledge `content_loaded` request      |
      |------------------------------------------>|
      |                                           |
      | `capabilities` request                    |
      |------------------------------------------>|
      |                                           |
      |                   `capabilities` response |
      |<------------------------------------------|
      |                                           |
      | Approve/deny capabilities                 |
      |--------------------------                 |
      |                         |                 |
      |<-------------------------                 |
      |                                           |

A broad sequence diagram for ``waitForIframeLoad: true`` is as follows::

  +---------+                                +---------+
  | Client  |                                | Widget  |
  +---------+                                +---------+
      |                                          |
      | Render widget                            |
      |--------------                            |
      |             |                            |
      |<-------------                            |
      |                                          |
      |                                          | iframe loading
      |                                          |---------------
      |                                          |              |
      |                                          |<--------------
      |                                          |
      |      Implicit `onLoad` event from iframe |
      |<-----------------------------------------|
      |                                          |
      | `supported_api_versions` request         |
      |----------------------------------------->|
      |                                          |
      |        `supported_api_versions` response |
      |<-----------------------------------------|
      |                                          |
      |         `supported_api_versions` request |
      |<-----------------------------------------|
      |                                          |
      | `supported_api_versions` response        |
      |----------------------------------------->|
      |                                          |
      | `capabilities` request                   |
      |----------------------------------------->|
      |                                          |
      |                  `capabilities` response |
      |<-----------------------------------------|
      |                                          |
      | Approve/deny capabilities                |
      |--------------------------                |
      |                         |                |
      |<-------------------------                |
      |                                          |

After both sequence diagrams, the session has been successfully established and can continue as
normal.

Verifying Capabilities
++++++++++++++++++++++

The client MUST have a mechanism to approve/deny capabilities. This can be done within the client's
code, not involving the user, by using heuristics such as the origin and widget type, or it can be
done by involving the user with a prompt to approve/deny particular capabilities.

The capabilities negotiation does not specify a way for the client to indicate to the widget which
capabilities were denied. The widget SHOULD only request the bare minimum required to function and
assume that it will receive all the requested capabilities. Clients SHOULD NOT automatically approve
all requested capabilities from widgets.

Whenever a widget attempts to do something with the API which requires a capability it was denied,
the client MUST respond with an error response indicating as such.

Any capabilities requested by the widget which the client does not recognize MUST be denied
automatically. Similarly, a client MUST NOT send requests to a widget which require the widget
to have been aprroved for a capability that it was denied access to. Clients MUST NOT approve
capabilities the widget did not request - these are implicitly denied.

A complete list of capabilities can be found in the `Available Capabilities`_ section.

Available Capabilities
~~~~~~~~~~~~~~~~~~~~~~

The following capabilities are defined by this specification. Custom capabilities can only be
defined via a namespace using the Java package naming convention.

Screenshots
+++++++++++

``m.capbility.screenshot`` can be requested by widgets if they support screenshots being taken
of them via the ``screenshot`` action. Typically this is only used to verify that the widget API
communications work between a client and widget. Widgets cannot use this capability to initiate
screenshots being taken of them - clients must request screenshots with the ``screenshot`` action.

Sticker Sending
+++++++++++++++

``m.sticker`` can be requested by widgets if they would like to send stickers into the room the
user is currently viewing. This should be implicitly approved by clients for ``m.stickerpicker``
widgets.

Always On Screen
++++++++++++++++

``m.always_on_screen`` can be requested by widgets if they would like to be able to use the
``set_always_on_screen`` action. This should be implicitly approved by clients for ``m.jitsi``
widgets (see the action's spec for more information).

OpenID Connect Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Widgets can request OpenID Connect credentials from the client (which in turn requests them from the
homeserver) to validate that the current user is who they say they are. The credentials are validated
out of band from the client to ensure the client is not able to falsify them.

There is no required capability for using this flow, however clients SHOULD prompt the user to
approve the widget's request to validate their identity. This prompt can have a "always remember for
this widget"-style checkbox on it, which is supported by the API exchange. Including the user in the
approval prompt does mean that the request is at risk of timing out, and as such there is a two part
exchange involving the client and widget.

The request is always initiated by the widget using the ``fromWidget`` ``get_openid`` action. This
is either responded to immediately with an OpenID Connect token, an indication of the request being
blocked, or an indication that the user is making a decision. When a user makes a selection, the
client uses the ``toWidget`` API to send a ``openid_credentials`` action with the relevant state.

After the widget receives the token from the client, it should validate it with the federation API.
Typically this means handing it off to a backend service which will validate the token and return
another credential the widget can use for future requests.

.. WARNING::
   Like with the OpenID Connect endpoints described by the Client-Server API and Federation API, it
   is important that the widget ensure the user ID returned by the server matches the server name
   given in the token from the client.

When needed, the client MUST call ``/_matrix/client/%CLIENT_MAJOR_VERSION%/user/{userId}/request_token``
to get the needed token to pass through to the widget.

A typical diagram of this flow is::

   +-------+                                         +---------+                                +---------+                               +---------------+                                                  +-------------+
   | User  |                                         | Client  |                                | Widget  |                               | WidgetBackend |                                                  | Homeserver  |
   +-------+                                         +---------+                                +---------+                               +---------------+                                                  +-------------+
      |                                                  |                                          |                                            |                                                                 |
      |                                                  | Establish Widget API session             |                                            |                                                                 |
      |                                                  |----------------------------------------->|                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |             Establish Widget API session |                                            |                                                                 |
      |                                                  |<-----------------------------------------|                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |            fromWidget get_openid request |                                            |                                                                 |
      |                                                  |<-----------------------------------------|                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  | ack with state "request"                 |                                            |                                                                 |
      |                                                  |----------------------------------------->|                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |      Ask if the widget can verify their identity |                                          |                                            |                                                                 |
      |<-------------------------------------------------|                                          |                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      | Approve                                          |                                          |                                            |                                                                 |
      |------------------------------------------------->|                                          |                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  | Call /_matrix/client/{version}/user/{userId}/request_token                            |                                                                 |
      |                                                  |-------------------------------------------------------------------------------------------------------------------------------------------------------->|
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |                                          |                                            |                                            OpenID Connect token |
      |                                                  |<--------------------------------------------------------------------------------------------------------------------------------------------------------|
      |                                                  |                                          |                                            |                                                                 |
      |                                                  | toWidget openid_credentials request      |                                            |                                                                 |
      |                                                  |----------------------------------------->|                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |           ack with empty response object |                                            |                                                                 |
      |                                                  |<-----------------------------------------|                                            |                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |                                          | Send received token for validation         |                                                                 |
      |                                                  |                                          |------------------------------------------->|                                                                 |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |                                          |                                            | Federated call to /_matrix/federation/v1/openid/userinfo        |
      |                                                  |                                          |                                            |---------------------------------------------------------------->|
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |                                          |                                            |                                                User information |
      |                                                  |                                          |                                            |<----------------------------------------------------------------|
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |                                          |                                            | Verify returned user information                                |
      |                                                  |                                          |                                            |---------------------------------                                |
      |                                                  |                                          |                                            |                                |                                |
      |                                                  |                                          |                                            |<--------------------------------                                |
      |                                                  |                                          |                                            |                                                                 |
      |                                                  |                                          |             Successful validation response |                                                                 |
      |                                                  |                                          |<-------------------------------------------|                                                                 |
      |                                                  |                                          |                                            |                                                                 |

``toWidget`` API
~~~~~~~~~~~~~~~~~~

The ``toWidget`` API is reserved for communications from the client to the widget. Custom
actions can be defined by using the Java package naming convention as a namespace.

Capabilities
++++++++++++

:Introduced in: ``0.1.0``

As part of the capabilities negotiation, the client sends a request with an action of
``capabilities`` (``CapabilitiesActionRequest``) to the widget, which replies with the requested
set of capabilities (``CapabilitiesActionResponse``).

{{definition_widgets_capabilities_action_request}}

{{definition_widgets_capabilities_action_response}}

Screenshots
+++++++++++

:Introduced in: ``0.1.0``

If the widget is approved for use of the ``m.capbility.screenshot`` capability, the client can
send a ``screenshot`` action (``ScreenshotActionRequest``) to request an image from the widget
(returned as a ``ScreenshotActionResponse``).

.. Note::
   This is typically only used to verify that communication is working between the widget and client.

.. WARNING::
   Widgets have an ability to send extremely large files and non-images via this action. Clients
   should only enable support for screenshots in a trusted environment, such as when a widget
   developer is making use of the client to test their widget.

{{definition_widgets_screenshot_action_request}}

{{definition_widgets_screenshot_action_response}}

Widget Visibility
+++++++++++++++++

:Introduced in: ``0.1.0``

The client can indicate to the widget whether it is visible or not to the user with the ``visbility``
action request (``VisibilityActionRequest``). If the widget does not receive visibility information,
it must assume that it is visible to the user.

Typically this action is not used on room widgets as they are visible implicitly to the user when
they view that room. Account widgets, however, often get rendered in the background by the client
and thus can be hidden/shown at times.

.. Note::
   Stickerpicker widgets and similar often make the best use of this to reload the user's available
   content when the widget gets shown again.

This action should only be sent when visibility of the widget to the user changes.

{{definition_widgets_visibility_action_request}}

{{definition_widgets_visibility_action_response}}

OpenID Connect Credential Information
+++++++++++++++++++++++++++++++++++++

:Introduced in: ``0.1.0``

.. Note::
   This section assumes the reader has the prior knowledge established by the
   `OpenID Connect Authentication <#openid-connect-authentication>`_ section.

This action is used by the client to indicate that the user has made a selection regarding the
prompt to confirm if the widget can verify their identity.

If approved, the request will contain the OpenID Connect token the widget will have to verify. If
defined, the request will indicate as such.

{{definition_widgets_openid_credentials_action_request}}

{{definition_widgets_openid_credentials_action_response}}

``fromWidget`` API
~~~~~~~~~~~~~~~~~~

The ``fromWidget`` API is reserved for communications from the widget to the client. Custom actions
can be defined by using the Java package naming convention as a namespace.

Indicating Content Loaded
+++++++++++++++++++++++++

:Introduced in: ``0.1.0``

In some rendering cases, the widget is expected to send a ``content_loaded`` action request taking
the shape of ``ContentLoadedActionRequest``. The widget can send this any time, even when not
required for establishing the session. Widgets SHOULD NOT send this action after the session has
been established.

{{definition_widgets_content_loaded_action_request}}

{{definition_widgets_content_loaded_action_response}}

Sending Stickers
++++++++++++++++

:Introduced in: ``0.1.0``

If the widget is approved for use of the ``m.sticker`` capability, the widget can send ``m.sticker``
action requests (``StickerActionRequest``) to have the client post an ``m.sticker`` event to the
room the user is currently viewing. If the room is encrypted, the client is responsible for
encrypting the widget's implied event.

The stickers widgets produce MUST meet the requirements of stickers in ``m.sticker`` events. For
creating the sticker event, the client uses the ``name`` or ``description`` from the request
in the event's ``body``, and otherwise copies the ``url`` and ``info`` values from the request
to the event directly (potentially with some validation).

{{definition_widgets_sticker_action_request}}

{{definition_widgets_sticker_action_response}}

Always On Screen
++++++++++++++++

:Introduced in: ``0.1.0``

If the widget is approved for use of the ``m.always_on_screen`` capability, the widget can request
that the client keep it always on screen with a ``set_always_on_screen`` action request
(``StickyActionRequest``).

Widgets by default are *not* always on screen, and only one widget at a time can be always on the
screen. Typically this is used by video conferencing widgets to ensure that the call is not disrupted
when the user switches rooms, and as such clients SHOULD ignore the restriction regarding only
rendering widgets when the user is viewing that room while the widget has requested to be always on
screen.

{{definition_widgets_sticky_action_request}}

{{definition_widgets_sticky_action_response}}

Requesting OpenID Connect Tokens
++++++++++++++++++++++++++++++++

:Introduced in: ``0.1.0``

.. Note::
   This section assumes the reader has the prior knowledge established by the
   `OpenID Connect Authentication <#openid-connect-authentication>`_ section.

This action is used by the widget to ask the client to start the OpenID Connect token exchange.
The client has three possible responses:

* A ``state`` of ``allowed`` alongside the OpenID Connect token. This is typically used if the user
  indicated that the widget is always allowed to verify their identity.
* A ``state`` of ``blocked``. This is typically used when the user has indicated that the widget
  can never verify their identity.
* A ``state`` of ``request``. This indicates that the client is asking the user for permission and
  will follow up with an appropriate ``toWidget`` ``openid_credentials`` request later.


{{definition_widgets_get_openid_action_request}}

{{definition_widgets_get_openid_action_response}}

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~~

The Widget API can allow for significant control of a client/widget, and thus needs to be secured
as much as possible. Clients should refuse/ignore requests and responses from origins other than
the widget's rendered origin, and should verify that the widget ID matches the expected value.
Widgets have a harder time of determining the origin, though they can rely on techniques like
``window.parent`` to ensure they are talking/responding to the right place.
