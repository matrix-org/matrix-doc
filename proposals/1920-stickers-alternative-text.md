# Alternative texts for stickers

The current `m.sticker` event definition includes `body` as a description field for the
sticker. This allows clients to attach a short description of the sticker in an
event. So far this field has mainly been used to give a literal description of
what is being shown on the image (in the same way an alternative text would do),
but the specification says it can also be "a message to accompany and further
describe the sticker".

On the one hand it may improve the user experience to use this field for a short
text that accompanies the image rather than describing it, on the other hand
it's important for accessiblity, and also clients that don't support stickers
(or media in general), to have something to use as a down-to-earth description
of what's shown in the sticker.

## Proposal

Add a new optional `alt_text` field to the `m.sticker` event definition which
contains the alternative text to the image. A `m.sticker` event would look like:

```json
{
    "type": "m.sticker",
    "content": {
        "url": "mxc://matrix.org/mRJacbBEPAJczvOltdhABxSv",
        "info": {
            "h": 256,
            "mimetype": "image/png",
            "size": 21957,
            "thumbnail_info": {
                "h": 256,
                "mimetype": "image/png",
                "size": 21957,
                "w": 222
            },
            "thumbnail_url": "mxc://matrix.org/mRJacbBEPAJczvOltdhABxSv",
            "w": 222
        },
        "alt_text": "The white Matrix logo over a black hexagon",
        "body": "Matrix!"
    }
}
```

In the absence of the `alt_text` field, clients must use the `body` as an
alternative text.

## Tradeoffs

The `alt_text` field could be a required one, which would be best for
accessiblity, but it would break compatibility with the existing `m.sticker`
events.

## Conclusion

In general, adding a way to attach an alternative text to every media in Matrix
would be a great improvement for accessiblity, but this is out of the scope of
this MSC.
