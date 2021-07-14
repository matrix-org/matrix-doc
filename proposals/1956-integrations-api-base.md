# MSC1956: Integrations API

"Integration managers" are applications that help clients bring integrations (bridges, bots, widgets, etc)
to users. This can be for things like setting up an IRC bridge or adding a Giphy bot to the room. Integration
managers have been popularized by Riot, however other clients also have support for concept as well although
to a lesser extent.

Integration managers are important to the Matrix ecosystem as they help abstract away the underlying integration
and allow providers of the integratiosn to manage access to them. For example, there are multiple XMPP bridges
available in the Matrix ecosystem and an integration manager is in the best position to handle the different APIs
each exposes, generalizing the API exposed to clients. Similarly, the integration manager could charge for access
to specific integrations such as sticker packs or per-user access to a bridge.

This proposal introduces a new Matrix API: the "Integrations API" (or "Integrations Specification") which covers
how integration managers and integrations themselves cooperate with clients. Typically these kinds of extensions
to Matrix would be put into the Client-Server API, however the integration manager is not typically the same as
the user's homeserver and is therefore ideal to be specified indepdently.


## Glossary

Due to the introduction of a new API, some common terminology is to be established:

An **Integration Manager** (or *Integrations Manager*, or simply *Manager*) is an application which assists users
and/or clients in setting up *Integrations*.

**Integrations** are something the *Integration Manager* exposes, such as *Bots*, *Bridges*, and *Widgets*.

A **Bot** is typically a Matrix user which provides a utility service, such as Github Notifications or reaction
GIFs.

A **Bridge** is typically an Application Service which proxies events between Matrix and a 3rd party platform,
such as IRC. Bridges may also operate in a single direction and have other features like *Puppeting*, which are
not covered here. For information on the various types of bridging, please see the
[reference guide](https://matrix.org/docs/guides/types-of-bridging.html).

**Widgets** are embedded web applications in a Matrix client. These are split into two types: **Account Widgets**
and **Room Widgets**. *Account Widgets* are specific to a particular Matrix user and not shared with other users
whereas *Room Widgets* are shared with the members of the room they reside in.

A **Trusted Integration Manager** is an *Integration Manager* which the client has deemed trustworthy by its own
criteria. For example, this may be defined as being known as an account widget, discovered by .well-known, or
being set in the client's configuration. By proxy, an **Untrusted Integration Manager** is the opposite.

The **Integration Manager API** is the set of HTTP endpoints which clients can use to interact with a given
*Integration Manager*.

The **Widget API** is the set of `postMessage` APIs which are used for clients and *Widgets* to communicate with
each other when embedded.

The **Integrations API** is the set of both the *Integration Manager API* and *Widget API* as well as any other
details which affect *Widgets* or *Integration Managers* and their interactions with clients.


## Proposal

A new Integrations API be introduced into Matrix which consists of the components listed in this proposal.

**Components**:

* API Standards (see later section of this proposal)
* Discovery - [MSC1957](https://github.com/matrix-org/matrix-doc/pull/1957)
* Widgets
  * Includes [MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236)
  * Includes [MSC1958](https://github.com/matrix-org/matrix-doc/pull/1958)
  * Includes [MSC1960](https://github.com/matrix-org/matrix-doc/pull/1960)
  * MSC for extensions and alterations not yet defined
    * ***TODO: MSC for each or group them by subject?***
  * The first version of the Widget API is to be `0.1.0`, with the existing `0.0.x` versions being flagged as
    development versions which are otherwise unspecified.
* Sticker picker and custom emoji
  * Includes [MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951)
  * Includes [MSC1959](https://github.com/matrix-org/matrix-doc/pull/1959)
* Authentication in integration managers - [MSC1961](https://github.com/matrix-org/matrix-doc/pull/1961)
* Terms of service / policies - [MSC2140](https://github.com/matrix-org/matrix-doc/pull/2140)
* Integration manager specific APIs
  * MSC and scope not yet defined

***TODO: Define where paid integrations, OAuth, etc all fit if at all.***
***TODO: Finalize what goes into this spec.***


## Proposed API standards

All HTTP APIs in this specification must consume and produce JSON unless otherwise indicated. Errors emitted by
these APIs should follow the standard error responses defined by other APIs in Matrix. Some common error responses
implementations may encounter are:
* `403` `{"errcode":"M_UNKNOWN_TOKEN","error":"Invalid token"}`
* `400` `{"errcode":"M_MISSING_PARAM","error":"Missing 'matrix_server_name'"}`
* `400` `{"errcode":"M_INVALID_PARAM","error":"'matrix_server_name' must be a string"}`
* `400` `{"errcode":"M_NOT_FOUND","error":"The sharable URL did not resolve to a pack"}`


## Tradeoffs

Specifying a whole new set of APIs means introducing another complex system into Matrix, potentially causing
confusion or concerns about the architecture of Matrix or its implementations. It is believed by the author that
having a dedicated set of APIs for this system within Matrix is important to reduce the burden on homeserver
authors and to support client authors in their ambitions to grow Matrix through bridges, bots, etc.

It is also questionable if integration managers should be a concept within Matrix as the APIs which clients would
be interacting with can be generically exposed by the integrations themselves without the need for a manager. The
manager's role in this specification is to provide clients with the opportunity to quickly get themselves connected
with the larger Matrix ecossytem without adding the burden of designing their own interface. The majority of the
APIs are defined such that a client is able to put their own UI on top of the manager instead of embedding that
manager if desired by the client.


## Potential issues

Clients which support today's ecosystem of integration managers have a lot of work to do to support this proposal
in all its parts. In addition, integration managers themselves have a decent amount of work in order to become
compliant. The exercise of this proposal is not to make development harder for the projects in the ecosystem, but
to standardize on a set of APIs which bridge the gap between managers while also patching inadequacies in the current
systems.


## Security considerations

Each proposal which branches off this proposal has its own set of security considerations. As a whole, clients are
expected to make decisions on which integration managers are trusted, and integration managers are encouraged to do
the same with clients and integrations.

----

## How all of this is meant to work (versus before)

This portion of the proposal is not required reading - it is supplemental information to help explain how integration
managers work in a world with this API and prior. This is also meant to be moderately high level and doesn't go into
the specific API endpoints one would call.

### Integration managers today (pre-API)

Integration managers are very much a Riot concept that has lead to enough utility to make it worth putting the idea
in the spec. An integration manager is typically just a UI for interacting with bridges/bots/widgets instead of having
to do all the bits manually or through a command line-like interface. Riot defines an integration manager as a set
of URLs: one for the UI (`ui_url`) and one for its API (`rest_url`). There are other URLs that also take place, but
they're covered in more detail later on in this text.

Before an integration manager can even be shown to the user, an authentication dance must take place. This is to
acquire an authentication token (wrongly named a `scalar_token` in Riot) - this token is then provided to the integration
manager where applicable via a `scalar_token` query string parameter. The auth dance involves getting an OpenID token
from the homeserver for the user, passing that to the integration manager via its API URL, and getting back a token
it can then use for future requests. The integration manager internally takes the OpenID token and verifies it by
doing a federated request to the homeserver - this is how it claims the token and gets a user ID back. This is also
why homeservers generally need working federation in order to use integrations, at least until recently when Synapse
could support exposing the OpenID claim endpoint without the rest of federation (Modular and similar deployments use
this).

The entire auth dance is done in the background, so the user doesn't see this happening. If any of the steps go wrong,
the user is warned that the integration manager is offline/inaccessible. After the auth dance, Riot does a terms of
service check to ensure the user has accepted all applicable policies. It does this by using the API URL to get the
authentication token owner's information (`/account`) which can return an error if there are unaccepted policies. If
there are policies to accept, Riot prompts before continuing. Provided the user accepts all the policies, Riot moves
on to rendering the integration manager window using the UI URL as a base. Depending on what the user clicked depends
on how the URL is constructed. Typically users would click the 4/9 squares in the context of the room, so a generic
URL referencing the "homepage" of the manager and the room ID is supplied to the manager. The user's authentication
token for the manager is also included in the URL.

The integration manager then takes all the information from the URL and starts to render the UI. In this case, it would
be rendering the homepage so it asks its backend for information about integrations it supports and starts trying to
figure out which ones are feasible. In the process, it queries Riot itself for some information (bot membership, room
publicity, room member count, etc) - this is done over a special `postMessage` API named `ScalarMessaging` (which is
not really Scalar-specific). Note that this API is different from the Widget `postMessage` API - more on that in a bit.

The ScalarMessaging API acts in the background and allows the integration manager to check the state of things as well
as perform actions. For example, when the user wants to add a bot to the room the manager will use the ScalarMessaging
API to determine if the bot is already in the room, and if it isn't it will use ScalarMessaging to cause the user to
invite the bot to the room. The expectation is generally that the bot will auto-accept invites without needing the
integration manager or Riot to interfere. When the bot is being removed from the room, it is not kicked through the API.
Instead, the integration manager calls its backend which impersonates the bot to leave the room.

The ScalarMessaging API is locked down enough to ensure only the integration manager can interact with it.

When the user finally wants to close the integration manager, they can click outside of it to have Riot dismiss the dialog
or they can click a close button within the integration manager which uses the ScalarMessaging API to close itself.

The other thing the ScalarMessaging class lets integration managers do is add widgets into the room and onto the user's
account. Widgets added by an integration manager are almost always wrapped by the integration manager itself. Widgets
are simply URLs that are rendered in iframes, so when the integration manager wraps a widget it means there's the top
level iframe supplied by Riot and another iframe supplied by the integration manager's wrapper. The wrapper usually
provides some features like being able to talk the Widget `postMessage` API (here on out known as the Widget API)
and a fullscreen button. Dimension, Scalar's opensource "competitor", doesn't require any authentication in order to
load this widget wrapper however Scalar does. Riot solves this by having a "widget URL whitelist" in the configuration
for when to provide an authentication token to the widget through its URL.

Scalar has two methods of checking for an authentication token, both of which are used to try and avoid the dreaded
"Forbidden" error page. The first is simply using the authentication token it was provided by the client. The second
involves cookies that are scoped to the Scalar domain. Typically the cookie is set after a token has been successfully
used (as provided by the client). The cookies helps avoid the forbidden error page when Riot decides it can't send
the authentication token to the widget/manager (typically when people change to Dimension or another integration manager).

Dimension uses a similar scheme for ensuring it has a token available, though it uses localstorage in place of cookies.
When both the provided and stored token fail, Dimension uses Riot's OpenID exchange API to acquire a new token by asking
the user for permission to share their identity. This is supposed to be used as a last resort, given Dimension only needs
a token to determine the user's stickerpacks and nothing more (for widgets).

It is worth noting that widgets are designed such that the integration manager gets no special treatment, however in
practice integration manager widgets are very difficult to manage from a client perspective, primarily for authentication
reasons. Widgets are simply supposed to be iframes with no dealing of tokens from a spec perspective.

The sticker picker is a particularly interesting widget in that it's at the user's account level and not in a room. By
nature of being a widget, it is supposed to be independent of the integration manager however in practice users find it
confusing when their integration manager changes and their sticker picker is the "old" one. This is something that can
usually be mitigated by the client (removing/replacing the sticker picker widget when the user asks to change their
integration manager), but so far no client has opted to do so.

The sticker picker widget uses a capabilities subsystem in the Widget API to get permission to send events (stickers)
on behalf of the user. Sticker pickers are one of the widgets which require authentication so the widget can show the
user the sticker packs they have enabled. Riot currently has the capabilities exchange happen in the background, though
it could expose it as a dialog to the user.

The final aspect of integration managers in the current ecosystem is conference calls: Riot uses a Jitsi widget to make
a conference call. Because different integration managers have different opinions on how the Jitsi widget should be declared,
Riot supports a configuration option to change the base URL of the Jitsi widget before it gets added to the room state.
The Jitsi URL in the config almost always points to an integration manager which wraps the widget.

### Integration managers in a post-API world

This proposal defines an API for how integration managers are supposed to work, taking into consideration user expectations,
technical limitations, and other issues with the current state of affairs. Most critically, this new API brings forth a
new authentication scheme for integration managers (and therefore widgets) by making somewhat radical changes to the way
things work.

The first major change is that integration managers become widgets. This is confusing at first, but if we run the thought
experiment for a bit it starts to make some sense. Widgets already have a well-specified API they can use to talk to the
client, and with some modifications (proposed here) the same API can be used to run an integration manager. This proposal
builds on the capabilities system to add additional actions needed by integration managers, such as adding readonly views
of the room membership and ability to invite users. This does away with the existing API which is not as well specified.

Widgets under this proposal also lose their authentication tokens, which means integration managers also lose an authentication
token. Authentication tokens are not completely gone though: the APIs to get them still exist for reasons described a bit
later on, and widgets can use the now-specified OpenID exchange API to acquire a token if it needs one. There's additionally
a provision within the proposal to allow clients to skip the prompt under some circumstances, such as when dealing with a
sticker picker or integration manager - these kinds of widgets are likely to need/request OpenID information for good reason
so the client can do so quietly in the background without nagging the user. Other widgets, like custom widgets, are expected
to prompt for confirmation from the user.

With this new authentication system, clients no longer need to track a whitelist of widget URLs to append tokens to and
generally don't need to track the tokens for themselves. Terms of service acceptance is also expected to be done by the
widgets (including integration manager) themselves, though smarter clients like Riot can try and optimize for it by still
doing the auth&check dance.

This proposal also defines a set of APIs for clients to interact with the integration manager directly, avoiding the use
of iframes where applicable. The theory is that clients wanting to control the integrations experience can do so by invoking
the integration manager's API on top of the client's native UI/UX. An example of where this might be worthwhile for Riot is
the sticker picker: instead of rendering an iframe and having to deal with a lot of complicated APIs, Riot could instead
just do the auth dance and get all the information it needs from the widget. A similar approach could be taken for adding
an IRC bridge to a room: if the client were driving the manager's API, it could offer a button instead of rendering a whole
iframe.

To handle the Jitsi use case, this proposal introduces a "make me a widget" API. The API exists on integration managers to
construct a widget for the client, doing away with Riot's Jitsi URL in the config.

Integration managers like Scalar can still require an authentication token to render the actual widget by having a small
wrapper which uses the OpenID exchange API. The wrapper should also persist the token somewhere (cookies/localstorage) so
it can load the next time unobtrusively.

Fundamentally the power an integration manager has is unchanged by this proposal, though how they perform actions is vastly
different, hopefully for the better.
