# Asynchronous media uploads
Sending media to Matrix currently requires that clients first upload the media
to the content repository and then send the event. This is a problem for some
use cases, such as bridges that want to preserve message order, as reuploading
a large file would block all messages.

## Proposal
This proposal proposes a way to send the event containing media before actually
uploading the media, which would make the aformentioned bridge message order
preservation possible without blocking all other messages behind a long upload.

In the future, this new functionality could be used for streaming file
transfers, as requested in [#1885].

### Content repository behavior
The proposal adds two new endpoints to the content repository API and modifies
the download endpoint.

#### `POST /_matrix/media/r0/create`
Create a new MXC URI without content. Like `/upload`, this endpoint requires
auth and returns the `content_uri` that can be used in events.

The request body should be an empty JSON object. In the future, the body could
be used for metadata about the file, such as the mime type or access control
settings (related: [MSC701]).

To prevent spam, servers should limit calls to this endpoint if the user has
created many media IDs without uploading any content to them. The error code
for such a spam limit is `M_TOO_MANY_IDS_ASSIGNED`. Servers should also provide
configuration options to let high-traffic clients like application services
bypass these limits. The `rate_limited` flag in the appservice registration is
one potential way to do this.

##### Example response
```json
{
  "content_uri": "mxc://example.com/AQwafuaFswefuhsfAFAgsw"
}
```

#### `PUT /_matrix/media/r0/upload/{serverName}/{mediaId}`
Upload content to a MXC URI that was created earlier. If the endpoint is called
with a media ID that already has content, the request should be rejected with
the error code `M_CANNOT_OVERWRITE_MEDIA` and HTTP status code 409. This endpoint
requires auth.

If the upload is successful, an empty JSON object and status code 200 is
returned. If the serverName/mediaId combination is not known or not local, an
`M_NOT_FOUND` error is returned. For other errors, such as file size, file type
or user quota errors, the normal `/upload` rules apply.

#### Changes to the `/download` endpoint
Two new query parameters are added: `max_stall_ms` and `allow_stream`.

* `max_stall_ms` is an integer that specifies the maximum number of milliseconds
  that the client is willing to wait for the upload to start (or finish, when
  streaming is not enabled). The default value is 10000 (10 seconds).
* `allow_stream` is a boolean that specifies whether or not the content
  repository should stream data as it comes in from the sender. Defaults to
  `true`.

When another client tries to download media that is currently being uploaded,
the content repository should send already uploaded data and stream new data as
it comes in from the sender.

If the upload is not started after the time limit, the content repository
should return a `M_NOT_YET_UPLOADED` error. The error may include an additional
`retry_after_ms` field to suggest when the client should try again.

If streaming is not supported by the server, or if it's disabled with the query
parameter, the content repository should act as if the upload has not started
until the upload is finished.

## Tradeoffs

## Potential issues
Other clients may time out the download if the sender takes too long to upload
media.

## Security considerations

## Unstable prefix
While this MSC is not in a released version of the spec, implementations should
use `net.maunium.msc2246` as a prefix and as a `unstable_features` flag in the
`/versions` endpoint.

* `POST /_matrix/media/unstable/net.maunium.msc2246/create`
* `PUT /_matrix/media/unstable/net.maunium.msc2246/upload/{serverName}/{mediaId}`
* `?net.maunium.msc2246.max_stall_ms`
* `?net.maunium.msc2246.allow_stream`

[#1885]: https://github.com/matrix-org/matrix-doc/issues/1885
[MSC701]: https://github.com/matrix-org/matrix-doc/issues/701
