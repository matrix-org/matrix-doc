# Matrix Media Information API

Authored by Travis Ralston (@turt2live)

Knowing how large a given piece of content actually is before downloading it can
be useful for clients, particularly clients on metered connections. The same API
can provide further detailed information about the content so that the other
party can make informed decisions.

This proposal is to address [matrix-doc#703](
https://github.com/matrix-org/matrix-doc/issues/703) with added bits.

### Note from the author / use case

This has been implemented in some capacity in my own media repository project
for a while. This proposal aims to formalize the API so it can be used by others
and not just an exclusive feature.

The original use case for this API was to identify media on the server side
rather than the client side. In particular, a sticker pack creation bot I’ve
been working on needed to ensure that people weren’t trying to create sticker
packs of PDFs or non-images.

## Proposal

New endpoint: `/_matrix/media/r0/info/<origin>/<media_id>`

The endpoint should always return very basic information about the content:

```
{
   "size": 102400,
   "content_type": "application/octet-stream"
}
```

The content repository must attempt to identify the content independently of
user-supplied content types. This may lead to slight differences in what the
original upload was claimed to be, however it is important for
clients/applications which would like to know what the actual file type is. If
the content repository cannot identify the type, it must return
application/octet-stream.

The size is just the size in bytes.

Beyond that, the content repository may wish to include further optional
information. Some common file types are defined below. If the content repository
does decide to return additional information, it must follow these structures.
All of the additional properties are optional, therefore allowing
implementations to return partial responses for some content (eg: dimensions of
an image but nothing about thumbnails).

Images

```
{
   "size": 102400,
   "content_type": "image/png",
   "width": 1920,
   "height": 1080,
   "thumbnails": [
       {"width": 96, "height": 96, "ready": true}
   ]
}
```

The width and height should be fairly obvious. The thumbnails are the thumbnails
that the content repository would prefer to generate or already has on hand. The
ready flag indicates whether or not the server has already cached that size.

Videos

```
{
   "size": 102400,
   "content_type": "video/mp4",
   "width": 1920,
   "height": 1080,
   "thumbnails": [
       {"width": 96, "height": 96, "ready": true}
   ],
   "duration": 120.5
}
```

Videos use an extension of images, adding a duration field. The duration is the
duration of the video in seconds.

Audio

```
{
   "size": 102400,
   "content_type": "audio/mp3",
   "duration": 120.5
}
```

The duration is the duration of the audio in seconds.

## Potential issues

This doesn’t define a lot of file types, but should cover the bases for most
content. Given the content types are optional, clients may not rely on the
information being present anyways.

This would also be yet another HTTP call that clients would have to perform.
