# MSC3244: Room version capabilities

When a new room version is introduced there is a delay before it becames the default
version. This delay is related to support of this new room version across the federation.
If a Home Server were to switch the new version as default to early, it will lock out all other users
that are on Home Servers that do not understand this version.

But however the new room version might add an interesting feature that some client on some Home
Servers might want to use earlier. One solution might be for the client to explicitly request a
version when creating a room but it's a bad practice to force a room version.

If the client is forcing a room version, and server side a new version is added (that support the needed
feature) the client will still use the old one until it's updated.

As an example v7 is introducing `knock` but it's not default yet, it would be nice for client to 
start using it until it is supported by the default version and to also use the latest stable version that
supports this feature in the future.

The goal of this MSC is to give the client a way to have more information on the supported features of room
versions available on a given server, to give more feedback to users during room creation as well as
in the room settings section.

## Proposal

The __m.room_versions capability__  [`/_matrix/client/r0/capabilities`]([https://matrix.org/docs/spec/client_server/r0.6.1#m-room-versions-capability])
endpoint could be decorated to provide more information on room version capabilities.

Actual capabilities response:
````
{
  "capabilities": {
    "m.room_versions": {
      "default": "6",
      "available": {
        "1": "stable",
        "2": "stable",
        "3": "stable",
        "4": "stable",
        "5": "stable",
        "6": "stable",
        "org.matrix.msc2176": "unstable",
        "org.matrix.msc3083": "unstable"
      }
    },
    "m.change_password": {...}
  }
}
````

Proposed modification.
In the following hypothetical sample, 3 new versions has been introduced (7, 8 and 9) but 6 is still the default.

````
{
  "capabilities": {
    "m.room_versions": {
      "default": "6",
      "available": {
        "1": "stable",
        "...,
        "6": "stable",
        "7": "stable",
        "8": "stable",
        "9": "stable",
        "org.matrix.msc6789": "unstable",
      },
      "room_capabilities": {
          "knock" : {
              "preferred": "7",
              "support" : ["7"]
          },
          "restricted" : {
              "preferred": "9",
              "support" : ["8", "9"]
          }
      }
    }
  }
}
````

A new object is added under `room_capabilities`, each key is the name of a capability.
This object provides the list of room versions supporting this capability as well as the preferred version to use.


As part of this MSC, two capabilities are defined:
- `knock` for knocking join rule support [MSC2403](https://github.com/matrix-org/matrix-doc/pull/2403)
- `restricted` for restricted join rule support [MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083)

## Client recommendations:

__Notice__: In real world usage most of the time clients should not specify a room version when creating
a room, and should let the Home Server select the correct one (via their knowledgeable server admin).
This is an advanced mechanism to start using feature early.

When presenting room settings, clients should use capabilities in order to display the correct UI. 

For example if the room support knocking, the client should add this option in the join rule chooser
(and if not only show `Invite Only` and `Public` for example).

When creating a room, the client could check if the needed feature is supported by the server before creating.

If the feature is not supported, the client could inform the user that this type of room can't be created
as well as an information message explaining how to contact the home server admin.

If the feature is supported by the default room version, then just continue as usual.

If the feature is supported but by a stable room version that is not the default one, the client should
then request to use the preferred version (`preferred`) that supports the feature, in the create room call:

````
POST /_matrix/client/r0/createRoom HTTP/1.1
Content-Type: application/json

{
  "preset": "....",
  "name": "....",
  "topic": "....",
  "creation_content": { ... }
  "room_version": "8"
}
````

In the hypothetical scenario where multiple capabilities would be needed (e.g mscXX1 and mscXX2), and have different `preferred` versions, clients can then pick one of the stable version that appears in both `support` arrays.

Notice that, it is not recommended to use an unstable room version even if it's the only one supporting a given feature.
It should be reserved for development. This MSC is only about default version not about unstable.


## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`room_capabilities` | event type | `org.matrix.msc3244.room_capabilities`
