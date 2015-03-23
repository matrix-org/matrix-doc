Application Service API
=======================

The Matrix client-server API and server-server APIs provide the means to
implement a consistent self-contained federated messaging fabric. However, they
provide limited means of implementing custom server-side behaviour in Matrix
(e.g. gateways, filters, extensible hooks etc).

Defining a standard API to allow such extensible functionality to be implemented
irrespective of the underlying homeserver implementation is key to enabling
these services.

Client-Server Services
----------------------

.. TODO-spec
  Overview of bots

Passive Application Services
----------------------------
"Passive" application services can only observe events from a given home server.
They cannot prevent events from being sent, nor can they modify the event being
sent.

In order to observe events from a home server, the application service needs
to register itself and tell the home server what kinds of events it wants
to receive.

Application Service -> Home Server API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This contains home server APIs which are used by the application service.

Registration API
++++++++++++++++

This API registers the application service with its host homeserver to offer its
services.

Inputs:
 - Credentials (e.g. some kind of string token)
 - Namespace[users]
 - Namespace[room aliases]
 - Namespace[room IDs]
 - URL base to receive inbound comms
 - Filter ID to apply when receiving inbound comms (optional)
Output:
 - The credentials the HS will use to query the AS with in return. (e.g. some 
   kind of string token)
Side effects:
 - The HS will start delivering events to the URL base specified if this 200s.
API called when:
 - The application service wants to register with a brand new home server.
Notes:
 - An application service can state whether they should be the only ones who 
   can manage a specified namespace. This is referred to as an "exclusive" 
   namespace. An exclusive namespace prevents humans and other application 
   services from creating/deleting entities in that namespace. Typically,
   exclusive namespaces are used when the rooms represent real rooms on
   another service (e.g. IRC). Non-exclusive namespaces are used when the
   application service is merely augmenting the room itself (e.g. providing
   logging or searching facilities).
 - Namespaces are represented by POSIX extended regular expressions in JSON. 
   They look like::

     users: [
       {
         "exclusive": true,
         "regex": "@irc\.freenode\.net/.*"
       }
     ]
 - The filter ID in this request will be applied to push-based inbound
   communications, in a similar way to how filter IDs are applied to the
   client-server pull-based sync API.

::

 POST /register
 
 Request format
 {
   url: "https://my.application.service.com/matrix/",
   as_token: "some_AS_token",
   filter_id: "some filter id",
   namespaces: {
     users: [
       {
         "exclusive": true,
         "regex": "@irc\.freenode\.net/.*"
       }
     ],
     aliases: [
       {
         "exclusive": true,
         "regex": "#irc\.freenode\.net/.*"
       }
     ],
     rooms: [
       {
         "exclusive": true,
         "regex": "!irc\.freenode\.net/.*"
       }
     ]
   }
 }
 
 
 Returns:
   200 : Registration accepted.
   400 : Namespaces do not conform to regex
   401 : Credentials need to be supplied.
   403 : AS credentials rejected.
 
 
   200 OK response format
 
   {
     hs_token: "string"
   }
   
Unregister API
++++++++++++++
This API unregisters a previously registered AS from the home server.

Inputs:
 - AS token
Output:
 - None.
Side effects:
 - The HS will stop delivering events to the URL base specified for this AS if 
   this 200s.
API called when:
 - The application service wants to stop receiving all events from the HS.
 
::

  POST /unregister

  Request format
  {
    as_token: "string"
  }


Home Server -> Application Service API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This contains application service APIs which are used by the home server. All
application services MUST implement these APIs.

User Query
++++++++++

This API is called by the HS to query the existence of a user on the Application
Service's namespace.

Inputs:
 - User ID
 - HS Credentials
Output:
 - Whether the user exists.
Side effects:
 - User is created on the HS by the AS via CS APIs during the processing of this request.
API called when:
 - HS receives an event for an unknown user ID in the AS's namespace, e.g. an
   invite event to a room.
Notes:
 - When the AS receives this request, if the user exists, it must create the user via
   the CS API.
 - It can also set arbitrary information about the user (e.g. display name, join rooms, etc)
   using the CS API.
 - When this setup is complete, the AS should respond to the HS request. This means the AS 
   blocks the HS until the user is created.
 - This is deemed more flexible than alternative methods (e.g. returning a JSON blob with the
   user's display name and get the HS to provision the user).
Retry notes:
 - The home server cannot respond to the client's request until the response to
   this API is obtained from the AS.
 - Recommended that home servers try a few times then time out, returning a
   408 Request Timeout to the client.
   
::

 GET /users/$user_id?access_token=$hs_token
 
 Returns:
   200 : User is recognised.
   404 : User not found.
   401 : Credentials need to be supplied.
   403 : HS credentials rejected.
 
 
   200 OK response format
 
   {}
   
Room Alias Query
++++++++++++++++
This API is called by the HS to query the existence of a room alias on the 
Application Service's namespace.

Inputs:
 - Room alias
 - HS Credentials
Output:
 - Whether the room exists.
Side effects:
 - Room is created on the HS by the AS via CS APIs during the processing of 
   this request.
API called when:
 - HS receives an event to join a room alias in the AS's namespace.
Notes:
 - When the AS receives this request, if the room exists, it must create the room via
   the CS API.
 - It can also set arbitrary information about the room (e.g. name, topic, etc)
   using the CS API.
 - It can send messages as other users in order to populate scrollback.
 - When this setup is complete, the AS should respond to the HS request. This means the AS 
   blocks the HS until the room is created and configured.
 - This is deemed more flexible than alternative methods (e.g. returning an initial sync
   style JSON blob and get the HS to provision the room). It also means that the AS knows
   the room ID -> alias mapping.
Retry notes:
 - The home server cannot respond to the client's request until the response to
   this API is obtained from the AS.
 - Recommended that home servers try a few times then time out, returning a
   408 Request Timeout to the client.
 
::

 GET /rooms/$room_alias?access_token=$hs_token
 
 Returns:
   200 : Room is recognised.
   404 : Room not found.
   401 : Credentials need to be supplied.
   403 : HS credentials rejected.
 
 
   200 OK response format
 
   {}

Pushing
+++++++
This API is called by the HS when the HS wants to push an event (or batch of 
events) to the AS.

Inputs:
 - HS Credentials
 - Event(s) to give to the AS
 - HS-generated transaction ID
Output:
 - None. 

Data flows:

::

 Typical
 HS ---> AS : Home server sends events with transaction ID T.
    <---    : AS sends back 200 OK.
    
 AS ACK Lost
 HS ---> AS : Home server sends events with transaction ID T.
    <-/-    : AS 200 OK is lost.
 HS ---> AS : Home server retries with the same transaction ID of T.
    <---    : AS sends back 200 OK. If the AS had processed these events 
              already, it can NO-OP this request (and it knows if it is the same
              events based on the transacton ID).
            

Retry notes:
 - If the HS fails to pass on the events to the AS, it must retry the request.
 - Since ASes by definition cannot alter the traffic being passed to it (unlike
   say, a Policy Server), these requests can be done in parallel to general HS
   processing; the HS doesn't need to block whilst doing this.
 - Home servers should use exponential backoff as their retry algorithm.
 - Home servers MUST NOT alter (e.g. add more) events they were going to 
   send within that transaction ID on retries, as the AS may have already 
   processed the events.
    
Ordering notes:
 - The events sent to the AS should be linearised, as they are from the event
   stream.
 - The home server will need to maintain a queue of transactions to send to 
   the AS.

::

  PUT /transactions/$transaction_id?access_token=$hs_token
 
  Request format
  {
    events: [
      ...
    ]
  }

Client-Server v2 API Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Passive application services can utilise a more powerful version of the 
client-server API by identifying itself as an application service to the
home server.

Identity assertion
++++++++++++++++++
The client-server API infers the user ID from the ``access_token`` provided in 
every request. Application services can use their ``as_token`` instead, and 
specify the virtual user they wish to be acting on behalf of. For real users, 
this would require additional permissions granting the AS permission to 
masquerade as a matrix user.

Inputs:
 - Application service token (``access_token``)

 Either:
   - User ID in the AS namespace to act as.
 Or:
   - OAuth2 token of real user (which may end up being an access token) 
Notes:
 - This will apply on all aspects of the CS API, except for Account Management.
 - The ``as_token`` is inserted into ``access_token`` which is usually where the
   client token is. This is done on purpose to allow application services to 
   reuse client SDKs.

::

 /path?access_token=$token&user_id=$userid

 Query Parameters:
   access_token: The application service token
   user_id: The desired user ID to act as.
   
 /path?access_token=$token&user_token=$token

 Query Parameters:
   access_token: The application service token
   user_token: The token granted to the AS by the real user

Timestamp massaging
+++++++++++++++++++
The application service may want to inject events at a certain time (reflecting
the time on the network they are tracking e.g. irc, xmpp). Application services
need to be able to adjust the ``origin_server_ts`` value to do this.

Inputs:
 - Application service token (``as_token``)
 - Desired timestamp
Notes:
 - This will only apply when sending events.
 
::

 /path?access_token=$token&ts=$timestamp

 Query Parameters added to the send event APIs only:
   access_token: The application service token
   ts: The desired timestamp

Server admin style permissions
++++++++++++++++++++++++++++++
The home server needs to give the application service *full control* over its
namespace, both for users and for room aliases. This means that the AS should
be able to create/edit/delete any room alias in its namespace, as well as
create/delete any user in its namespace. In order to create virtual users, the
application service needs to:

- Work around captchas.
- Have a 'passwordless' user.

This involves bypassing the registration flows entirely. This is achieved by
including the AS token on a ``/register`` request, along with a login type of
``m.login.application_service`` to set the desired user ID without a password.

::

  /register?access_token=$as_token
  
  Content:
  {
    type: "m.login.application_service",
    user: "<desired user localpart in AS namespace>"
  }

Application services which attempt to create users or aliases *outside* of
their defined namespaces will receive an error code ``M_EXCLUSIVE``. Similarly,
normal users who attempt to create users or alises *inside* an application
service-defined namespace will receive the same ``M_EXCLUSIVE`` error code,
but only if the application service has defined the namespace as ``exclusive``.

ID conventions
~~~~~~~~~~~~~~
.. NOTE
  - Giving HSes the freedom to namespace still feels like the Right Thing here.
  - Exposing a public API provides the consistency which was the main complaint
    against namespacing.
  - This may have knock-on effects for the AS registration API. E.g. why don't
    we let ASes specify the *URI* regex they want?

This concerns the well-defined conventions for mapping 3P network IDs to matrix
IDs, which we expect clients to be able to do by themselves.

User IDs
++++++++
Matrix users may wish to directly contact a virtual user, e.g. to send an email.
The URI format is a well-structured way to represent a number of different ID
types, including:

- MSISDNs (``tel``)
- Email addresses (``mailto``)
- IRC nicks (``irc`` - https://tools.ietf.org/html/draft-butcher-irc-url-04)
- XMPP (xep-0032)
- SIP URIs (RFC 3261)

As a result, virtual user IDs SHOULD relate to their URI counterpart. The
mapping from URI to user ID is expressed as a C-S API on the HS which takes
URIs and responds with user IDs. Home servers can internally map URIs to 
user IDs in whatever way they desire.

::

  GET /_matrix/appservice/v1/uris/user?uri=$url_encoded_uri
  
  Returns 200 OK:
  {
    user_id: <complete user ID on local HS>
  }
  
  Returns 404:
  {
    errcode: "M_NOT_FOUND",
    error: "URI is not mapped to any application service on this home server."
  }

Room Aliases
++++++++++++
Third party rooms which can be expressed as URIs can be exposed so that Matrix users 
can join them directly, e.g. IRC rooms. It is not desirable to expose every kind of
URI -> Room mapping though, as some of these rooms may be "private" e.g. mailto, tel. 
Rooms which are publicly accessible (e.g. IRC rooms) can be exposed as an alias by
the application service. Private rooms (e.g. sending an email to someone) should not
be exposed in this way, but should instead operate using normal invite/join semantics.
The ID conventions outlined below are only valid for public rooms which 
expose room aliases.

::

  GET /_matrix/appservice/v1/uris/alias?uri=$url_encoded_uri
  
  Returns 200 OK:
  {
    alias: <complete room alias on local HS>
  }
  
  Returns 404:
  {
    errcode: "M_NOT_FOUND",
    error: "URI is not mapped to any application service on this home server."
  }
  
Event fields
++++++++++++
We recommend that any gatewayed events should include an ``external_uri`` field
in their content to provide a way for Matrix clients to link into the 'native'
client from which the event originated.  For instance, this could contain the
message-ID for emails/nntp posts, or a link to a blog comment when gatewaying
blog comment traffic in & out of Matrix.

Active Application Services
----------------------------

.. TODO-spec
  API that provides hooks into the server so that you can intercept and
  manipulate events, and/or insert virtual users & rooms into the server.

