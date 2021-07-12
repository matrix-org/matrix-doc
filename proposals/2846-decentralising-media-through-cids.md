# MSC2846: Decentralising media through CIDs
<sup>Authored by Jan Christian Grünhage and Andrew Morgan</sup>

Currently, the Media API is less decentralised than most other aspects of
Matrix. When the homeserver that uploaded a piece of content goes down, the
content is not visible from homeservers that didn't fetch it beforehand. This is
because the MXC URLs are made up of the server name of the sending server and an
opaque media ID. We can't fetch media from servers other than the origin server
because we there is no signature or hash included to verify the integrity of the
file. This proposal modifies the media ID to be a
[CID](https:/github.com/multiformats/cid) (content ID), which (among other
things) includes a hash of the file. This allows us to verify the integrity of
the file both on the server side and the client side.

## Current behaviour
### Sending
![Current flow for sending](images/2846-sending-current.jpeg)


### Receiving
![Current flow for receiving](images/2846-receiving-current.jpeg)

## Proposal
### Data structures
We propose MXC URLs change from `mxc://<server>/<opaque ID>` to
`mxc://<server>/<CID>`. We include the server here for backwards compatibility
reasons, so that old servers and clients would still work as before, and also as
a primary source for downloading the media. If that fails, the server needs a
hint on where to get the media from instead, which the client may send to the
server as a query parameter.

### Sending
![Proposed flow for sending](images/2846-sending-proposed.jpeg)

As you can see, this is very similar to what happens on existing clients and
servers. The client behaviour *can* change (in terms of verification of file
integrity), but a client that does not change its behaviour will still work as
expected. Clients can additionally verify that the MXC URL they received from
the server actually represents the file that was originally sent.

The server should not use v0 CIDs, it should always use v1 CIDs (until we change
that in the future). This is because v1 CIDs have lots of benefits over their v0
counterpart. The server may implement any number of supported hashes from the
multihash spec for decoding (bikeshedding opportunity: Do we want to recommend
hashes here that we don't recommend sending, for making the switch to other
hashes easier in the future?), but it should stick to reasonably widespread
hashes for files it is sending (bikeshedding opportunity: What do these include?
https://github.com/multiformats/multicodec/blob/master/table.csv has a list of
all hashes supported by the multihash spec. SHA2 and SHA3 should be safe bets).

### Receiving
![Proposed flow for receiving](images/2846-receiving-proposed.jpeg)

Again very similar to what happens in the current state. You can drop old
implementations into this just fine, everything will continue to work.  New
implementations will be able to verify additional hashes and try more fallbacks
for fetching content.

The server trying more fallbacks requires that the client hints to their server
where the content might be located. This should be done by query parameters on
the download request. There's two options here:
 - A pair of room and event ID, given via the `room` and `event` query
   parameters.
 - A list of explicit fallback servers, via the `via` query parameter.

Giving a room and event ID is preferrable, but for some contexts it might be
better to explicitly give fallback servers. (Bikeshedding opportunity: What
usecases would this be? Avatars? Or do we want to remove this option completely?)

The client usually trusts its own server at least somewhat, so it doesn't need
to verify the CID of the file served there, but the server needs to verify the
CID of the file returned by the remote to prevent malicious remotes from serving
invalid content for rooms that they participate in.

##### Potential remotes
1. Origin encoded in the MXC URL.
2. If the client has supplied explicit fallback servers, try those in the order
   the client supplied them in.
3. If the client has supplied a room+event ID combo as a hint:
	1. Try the servers that used to be in the room back then and still are.
	2. Try the servers that are in the room now but weren't back then.
	3. Try the servers that used to be in the room but aren't anymore. These are
	   tried last to make sure servers leaving a room aren't put under any
	   unnecessary load from that room anymore.

## Potential issues
 - Multihash and CID are not wide spread outside of IPFS and Protocol Labs.
   There's implementations for a few languages, but this might be an at least
   somewhat limiting factor. Less difficult than E2EE, but still not trivial.

## Alternatives/Related MSCs
1. [**MSC2706**](https://github.com/matrix-org/matrix-doc/pull/2706) proposes to
   use IPFS directly, but in a similarily backwards compatible way to how we're
   changing MXC URLs here. MSC2706 does make authenticating media worse, because
   it publishes the file to IPFS and that is easy to scrape, but that also means
   that fallback nodes are automatically found. Public files in this MSC *could*
   be put into IPFS in the future, maybe as an updated version of MSC2706,
   without changing the MXC URL format again, as we'd already have CIDs here.
1. [**MSC2703**](https://github.com/matrix-org/matrix-doc/pull/2703) specifies a
   grammar for media IDs, which could be problematic for us here. It specifies
   that media IDs must be opaque, as well as a maximum of 255 characters in
   length. This is in conflict to this MSC (and also MSC2706), because we do
   encode information in the media ID, which servers and clients do want to
   decode. It contains a hash, which should be used to verify the integrity of
   the file that was fetched. The other possible conflict with that MSC is the
   character limit of 255 characters, which should not affect this MSC, because
   a CID is normally 60 characters, but that depends on what the CID actually
   looks like. In the future, a CID based on a much longer multihash could mean
   we run into issues here, but this is fairly unlikely, as that would mean hash
   lengths of over a thousand bits.
1. [**MSC2834**](https://github.com/matrix-org/matrix-doc/pull/2834) proposes to
   replace MXC URLs with custom hash identifier + hash strings. This is very
   similar to what we're doing here, with the difference of not reusing
   pre-existing methods like multihash and CIDs. Also, by removing the server
   name from the MXC URL, it breaks backwards compatibility on the server side,
   and for clients which attempt to parse the MXC URL.
1. **MSCNaN** proposes authentication of media endpoints using events attached
   to the media files. As this MSC also does, it proposes sending the room and
   event ID as query parameters when downloading. Its authentication would also
   help with the potential issue of leaking file contents, as discussed in the
   security considerations section.

## Security considerations
 - Without authentication, this enables fetching of files you know the hash of
   (assuming the hash you know is one the media repo of your server supports).
   This is potentially problematic, as hashes of things are leaked in places
   where access to files are not always leaked as well. For example, git commit
   IDs are SHA1 hashes of the objects, so a commit ID could lead to the whole
   repo (up to that commit) being leaked when the objects end up in matrix's
   media repo. This is a fairly far fetched usecase, but it's still an indicator
   that this might be problematic.  MSCNaN would help here.

## Backwards compatibility concerns
Clients/Servers not implementing this MSC should continue to work normally. New
events sent with non-CID media IDs should not pose a problem either, because
they wouldn't be parsed as CIDs successfully. If they actually are parsed as
CIDs successfully but aren't valid, that's either a huge coincidence, or, a lot
more likely, a malicious MXC URL. In that case, it would just fail, which is not
worse than what malicious MXC URLs can already do right now.
