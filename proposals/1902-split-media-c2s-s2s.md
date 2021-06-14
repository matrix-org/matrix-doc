# Splitting the media repo into a client-side and server-side component

Currently Matrix relies on media being pulled from servers using the same set
of endpoints which clients use. This has so far meant that media repository
implementations cannot reliably enforce auth on given resources, and implementations
are left confused/concerned about the lack of split in the endpoints.

## Proposal

Instead of using `/_matrix/media` for both servers and clients, servers must now use
`/_matrix/federation/v1/remote_media` and clients must use `/_matrix/client/r0/media`.

To support backwards compatibility and logical usage of the media repo, only downloads
and thumbnails will be available over the new federation prefix. The remaining endpoints
will only be available through the client-server API.

The mapping of each endpoint would look like:

| Old | Client-Server | Federation |
|-----|---------------|------------|
| `/_matrix/media/:version/download/:origin/:mediaId` | `/_matrix/client/r0/media/download/:origin/:mediaId` | `/_matrix/federation/v1/remote_media/download/:origin/:mediaId` |
| `/_matrix/media/:version/thumbnail/:origin/:mediaId` | `/_matrix/client/r0/media/thumbnail/:origin/:mediaId` | `/_matrix/federation/v1/remote_media/thumbnail/:origin/:mediaId` |
| `/_matrix/media/:version/upload` | `/_matrix/client/r0/media/upload` | N/A |
| `/_matrix/media/:version/preview_url` | `/_matrix/client/r0/media/preview_url` | N/A |
| `/_matrix/media/:version/config` | `/_matrix/client/r0/media/config` | N/A |

No schema changes are proposed to the endpoints, aside from the obvious pathing differences.

### Federation endpoints

Because media is not (currently) actively federated, the endpoint is named "remote_media"
to imply it is not a resource the target server is expected to have.

The federation endpoints will require standard [request authentication](https://matrix.org/docs/spec/server_server/r0.1.4#request-authentication).

### Client-server endpoints

With the exception of `/download` and `/thumbnail`, all media endpoints require authentication.
We could require access tokens on media, however [MSC701](https://github.com/matrix-org/matrix-doc/issues/701)
and similar are better positioned to handle the problem.

## Changes required by known implementations

Clients and servers will have to adopt the new endpoints entirely. It is expected that
existing implementations will continue to use the legacy routes for a short time while
these changes gain popularity in the ecosystem.

In a prior version of this proposal it was suggested to use `/_matrix/media/v1` for
server-server communication with the authentication requirements described here, however
due to some clients still using `/_matrix/media/v1` (despite the endpoint changing to be
`/_matrix/media/r0` some versions ago) it is not feasible to support backwards compatibility
with the authenticated endpoints.

## References

* [MSC701](https://github.com/matrix-org/matrix-doc/issues/701) - Access control and
  GDPR for the media repo.
* [matrix-doc#1341](https://github.com/matrix-org/matrix-doc/issues/1341) - Concerns
  with servers using the client-server endpoints to download media over federation.

## Unstable prefix

While this MSC is not in a released version of the spec, use `unstable/org.matrix.msc1902` in place
of the version. For example, `/_matrix/client/r0/media/config` becomes
`/_matrix/client/unstable/org.matrix.msc1902/media/config`.
