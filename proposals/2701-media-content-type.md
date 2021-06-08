# MSC2701: Media and the `Content-Type` relationship

Currently clients and servers handle the `Content-Type` header differently depending on implementation.
This proposal aims to simplify and standardize what they should be doing instead.

## Proposal

The `Content-Type` header becomes explicitly specified as the source of truth for the media which is
being uploaded. When this is not provided, servers MUST assume the type is `application/octet-stream`.

Servers can still sniff the content type for restriction purposes, however when serving the file back
to callers the `Content-Type` header must remain intact.

The `Content-Type` header used during upload MUST be echoed back on `/download`. For existing media
this obviously may not be possible, however most clients have uploaded media with the right `Content-Type`
in good faith so far.

## Potential issues

As mentioned, some media may have been uploaded with the wrong type or with an interpretted one. It
is presumed that media up until this point is roughly close enough to be considered backwards
compatible.

Servers which do opt to sniff the content type will run into issues when the media is encrypted. Encrypted
media has a possibility of falsely flagging as another content type even when specified by the caller
as a binary blob.

## Alternatives

We could continue to allow unexpected behaviour, however in the spririt of standardization this feels
wrong.

## Security considerations

Some content types have known or possible vulnerabilities when served with specific types. Servers
SHOULD be cautious of potential mismatches, potentially blocking uploaders if the sniffed type does
not reasonably match the provided type.

The risk of a wrong `Content-Type` being used for malicious purposes is considered acceptable by this
proposal due to the fact that an attacker can always package their content in an approved/plausible
container, such as a ZIP file.

## Unstable prefix

No unstable prefix is required for this MSC thanks to backwards compatibility.

## Implementations

Currently matrix-media-repo and Synapse are both known to do this echoing.
