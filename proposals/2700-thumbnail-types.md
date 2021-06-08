# MSC2700: Thumbnail requirements for the media repo

Currently what can be thumbnailed is left as an implementation concern and not one that can be
predicted or anticipated by clients. This relatively small proposal aims to fix that.

## Proposal

**Note**: This proposal intentionally does not specify what mimetypes to return for thumbnails.
See [MSC2705](https://github.com/matrix-org/matrix-doc/pull/2705) for details on those restrictions.

This proposal does not alter how the thumbnails are generated, just that they can be generated.

Servers MUST be able to generate thumbnails for the following mimetypes:
* `image/png`
* `image/jpeg` (and `image/jpg`)
* `image/gif`

Servers SHOULD be able to generate thumbnails for the following mimetypes:
* `image/svg+xml`
* `video/H264`
* `video/mp4`

Servers SHOULD support other mimetypes where possible, such as `application/pdf` and `text/plain`.

In order to better support the server's mission in thumbnailing, clients SHOULD NOT upload
encrypted with a content type that matches the source material. Instead, clients SHOULD use
`application/octet-stream` or similar for unidentifiable/encrypted files.

Servers that cannot handle a given media's mimetype should return a `501 M_UNSUPPORTED` error. If
the server encounters an error while trying to thumbnail known media (such as a client mistakenly
uploading an encrypted file as `image/png`), it should continue to return `500 M_UNKNOWN`.

## Potential issues

The formats chosen could be overly restrictive to users, preventing modern formats for files from
gaining popularity. We can fix this by including them in recommendations and requirements.

## Alternatives

We could leave the thumbnail generation up to the server completely, however clients will then be
asking for thumbnails which might not be possible. By specifying a limited set of commonly-used file
types, we allow clients to be able to intelligently get servers to thumbnail media.

## Security considerations

Some media, such as SVGs, are vulnerable to various well-known attacks. These should be avoided by
server implementations.

## Unstable prefix

No unstable prefix is required for this MSC.

## Implementations

This MSC is inherently implemented by Synapse and matrix-media-repo already.
