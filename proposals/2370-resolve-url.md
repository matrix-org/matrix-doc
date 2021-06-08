# Resolve URL API

(This document is heavily based on
https://docs.google.com/document/d/1bbX1yxNETmMa-AxBGjIpb4lNoTuc3vjGXmbZWrNBlzM/edit)

Users sometimes want to upload images to Matrix rooms that they see on other
web pages; currently, the way for them to do that is to download the image and
upload it to their homeserver.  However, this is inefficient, especially for
users with constrained bandwidth, as the user's homeserver could simply
download the image itself.

In addition, users sometimes want to drag-and-drop images from web pages to
their Matrix client to send them.  However, for web-based clients, doing so
only gives them the URL of the image, and [due to CORS
restrictions](https://github.com/vector-im/riot-web/issues/3015#issuecomment-348802045),
the client cannot download the image to re-upload it.

Web-based clients have a similar problem if they want to [automatically resolve
`<img>`
tags](https://github.com/vector-im/riot-web/issues/7100#issuecomment-408651555)
entered by a client from an HTTP(S) URL to an `mxc:` URL.

## Proposal

Add a new endpoint to resolve a URL.

Example:

Request:
```
POST /_matrix/media/r0/resolve_url
Content-Type: application/json
Authentication: Bearer <access token>

{
  "url": "<media-url>"
}
```

Response:
```
Content-Type: application/json

{
  "content_uri": "mxc://<server-name>/<media-id>",
  "content_type": "<MIME type of the URL>"
}
```

This endpoint requires authentication.  It causes the homeserver to download
the resource located at the specified URL, place it in the media repository,
and return the `mxc:` URL for the resource, along with the MIME type.

Errors can occur when processing the request.

* If the resource cannot be downloaded due to the URL returning a 404 error, the
  endpoint should respond with an `M_NOT_FOUND` error and HTTP code 404.
* If the resource cannot be downloaded due to the URL returning another error,
  the endpoint should respond with an `M_UNKNOWN` error and HTTP code 400.
* If the resource cannot be downloaded because it has been blacklisted, it should
  respond with an `M_FORBIDDEN` error and HTTP code 403.
* If the resource is larger than the homeserver's limit, it should
  respond with an `M_TOO_LARGE` error and HTTP code 400.

## Security considerations

This endpoint can be used to turn a homeserver into an HTTP proxy, so measures
need to be taken to mitigate this.

* Only authorized users should be allowed to call this endpoint.
* This endpoint should be rate limited.
* Homeservers may wish to restrict the MIME types that it is willing to
  download (for example, only images).
* Homeservers should allow administrators to blacklist URL patterns and IP
  addresses to prevent users from being able to access resources that are only
  available on an internal network.

Since the homeserver downloads the file, this will not work for trying to
upload encrypted files for end-to-end encrypted rooms.

## Unstable prefix

Unstable implementations should use the
`/_matrix/media/unstable/org.matrix/resolve_url` endpoint.

Additionally, servers implementing this feature should advertise that they do
so by exposing a `org.matrix.resolve_url` flag in the `unstable_features` part
of the `/versions` response.
