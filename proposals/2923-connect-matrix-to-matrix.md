# MSC2923: Matrix to Matrix connections

[Portal rooms](https://matrix.org/bridges/#libpurple) are a fantastic way for a network/platform/ecosystem/community to be exposed to Matrix. The naming happens automatically and creates a new room on Matrix to bridge everyone across. Some examples are the IRC freenode bridge (`#freenode_#channelname:matrix.org`) and the Gitter bridge (`#org_repo:gitter.im`) (bridges that transparently expose a whole ecosystem).

One problem is some communities can span across multiple platforms which means there are multiple Matrix portal rooms for the same topic. Example:

 - `#freenode_#crystal-lang:matrix.org`
 - `#crystal-lang_crystal:gitter.im`

It would be great if these rooms could be connected all together and reduce the fragmentation even more. Chatting in Gitter would reach freenode automagically. The goal of this MSC is to come up with a solution to solve this problem.



## Proposal

Add a mechanism to homeservers to be able connect and ferry messages back and forth from another Matrix room.

For the Cerulean threading proposal, there was a mention of adding a mechanism to send a message to both your timeline and thread room at the same time. This seems kind of similar, sending one event and ending up in multiple.


### Potential solutions


#### Message pointer reference events

When someone sends a message to a room, we also send a pointer reference event to the connected room which marks that messages place in the DAG.

The pointer reference events get filled in before we pass it on to the client.

Since [federated peeking](https://github.com/matrix-org/matrix-doc/issues/913) isn't available yet, for people not joined to the connected room, we can show a placeholder for the pointer reference event telling the user that they need to join the other room in order to see the message.


#### Connection layer on top of the DAG

To avoid mixing messages between rooms at the DAG level, this could be a connection layer on top supported by the homeserver. Rooms would continue to be separate at that level, but the client would still see a room with messages mixed in from both rooms.

This however presents a problem in that it's difficult to splice together two different rooms as the DAG is used for ordering. You'd need some way to interject messages in a way that works. And then you can have things like replies/relationships which would be cross room, and would cause all sorts of headaches.




## Potential issues


#### Connecting private and public rooms

Can someone connect a private and public room together?


#### E2EE rooms

How do e2e rooms work? Since the message is encrypted and only the devices can decrypt, the homeserver can't just ferry an encrypted message over and expect the others to be able to decrypt.

Potentially, we could  have the client send the message to all of the connected rooms individually.



## Alternatives

#### Consolidate to a single room

This option works today and doesn't require any additonal change.

Bridges could use the same internal room ID and just add their portal alias on top of the existing room. This requires a lot of manual poking on the bridges side to get setup and additional work if rooms are already created on each side like adding `m.room.tombstone` to point people to the new correct place.

Since, we don't want to handle every request manually. this also requires every single bridge to solve the problem of adding self-service plumbing to individual rooms.


#### Matrix to Matrix bridge

Create a new bridge which can bridge a Matrix room to another Matrix room.

This solution is flexible to solve any scenario but this functionality could also be built into the homeserver.

This also requires more burden on people having to host their own bridge.



## Security considerations

People might not realize their message is being shared more broadly to another audience. Also relating to a private room being connected to a public room.

Make sure there is a two-way negotiation system where admins of both rooms can approve of connecting the rooms. This is to prevent bad actors at `#badroom:evilcorp.com` connecting themselves to `#matrix:matrix.org` and causing hell.



## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*
