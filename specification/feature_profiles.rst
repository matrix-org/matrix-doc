.. Copyright 2016 OpenMarket Ltd
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

Feature Profiles
================

.. _sect:feature-profiles:

Matrix supports many different kinds of clients: from embedded IoT devices to
desktop clients. Not all clients can provide the same feature sets as other
clients e.g. due to lack of physical hardware such as not having a screen.
Clients can fall into one of several profiles and each profile contains a set
of features that the client MUST support. This section details a set of
"feature profiles". Clients are expected to implement a profile in its entirety
in order for it to be classified as that profile.

Summary
-------

===================================== ========== ========== ========== ========== ==========
  Module / Profile                       Web       Mobile    Desktop       CLI     Embedded
===================================== ========== ========== ========== ========== ==========
 `Instant Messaging`_                  Required   Required   Required   Required   Optional
 `Presence`_                           Required   Required   Required   Required   Optional
 `Push Notifications`_                 Optional   Required   Optional   Optional   Optional
 `Receipts`_                           Required   Required   Required   Required   Optional
 `Typing Notifications`_               Required   Required   Required   Required   Optional
 `VoIP`_                               Required   Required   Required   Optional   Optional
 `Content Repository`_                 Required   Required   Required   Optional   Optional
 `Managing History Visibility`_        Required   Required   Required   Required   Optional
 `Server Side Search`_                 Optional   Optional   Optional   Optional   Optional
 `Server Administration`_              Optional   Optional   Optional   Optional   Optional
 `Event Context`_                      Optional   Optional   Optional   Optional   Optional
 `Third Party Networks`_               Optional   Optional   Optional   Optional   Optional
===================================== ========== ========== ========== ========== ==========

*Please see each module for more details on what clients need to implement.*

.. _Instant Messaging: `module:im`_
.. _Presence: `module:presence`_
.. _Push Notifications: `module:push`_
.. _Receipts: `module:receipts`_
.. _Typing Notifications: `module:typing`_
.. _VoIP: `module:voip`_
.. _Content Repository: `module:content`_
.. _Managing History Visibility: `module:history-visibility`_
.. _Server Side Search: `module:search`_
.. _Server Administration: `module:admin`_
.. _Event Context: `module:event-context`_
.. _Third Party Networks: `module:third-party-networks`_

Clients
-------

Stand-alone web (``Web``)
~~~~~~~~~~~~~~~~~~~~~~~~~

This is a web page which heavily uses Matrix for communication. Single-page web
apps would be classified as a stand-alone web client, as would multi-page web
apps which use Matrix on nearly every page.

Mobile (``Mobile``)
~~~~~~~~~~~~~~~~~~~

This is a Matrix client specifically designed for consumption on mobile devices.
This is typically a mobile app but need not be so provided the feature set can
be reached (e.g. if a mobile site could display push notifications it could be
classified as a mobile client).

Desktop (``Desktop``)
~~~~~~~~~~~~~~~~~~~~~

This is a native GUI application which can run in its own environment outside a
browser.

Command Line Interface (``CLI``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a client which is used via a text-based terminal.

Embedded (``Embedded``)
~~~~~~~~~~~~~~~~~~~~~~~

This is a client which is embedded into another application or an embedded
device.

Application
+++++++++++

This is a Matrix client which is embedded in another website, e.g. using
iframes. These embedded clients are typically for a single purpose
related to the website in question, and are not intended to be fully-fledged
communication apps.

Device
++++++

This is a client which is typically running on an embedded device such as a
kettle, fridge or car. These clients tend to perform a few operations and run
in a resource constrained environment. Like embedded applications, they are
not intended to be fully-fledged communication systems.

