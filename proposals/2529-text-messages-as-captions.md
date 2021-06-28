# Use existing m.room.message/m.text events as captions for images

## Background

There is a demand to be able to apply a text caption to an image, as is
possible in other chat platforms. In Matrix this is not possible, so people
will generally send two events: one `m.image`, then a `m.text` event
immediately afterward to simulate a caption.

Better would be to able to explicitly mark an event as a caption.

## Proposal

Allow an optional `m.relates_to` field in the `content` field of a text message
event.

Example:

```
...
  "content": {
    "body": "Caption text",
    "msgtype": "m.text",
    "m.relates_to": {
            "event_id": "$(some image event)",
            "rel_type": "m.caption"
        }
  },
```

If a client recognises the `rel_type`, they can render the caption with the
image rather than as a separate message in the timeline.

The benefit of this is that if a client doesn't support or recognise the
`m.caption`, it can ignore the relation and just render the message inline.

This would not require aggregation from the server since there will always be a
need to send the event separately anyway.

## Potential issues

* Not sure how this relates to the broader questions discussed in MSC1849
* This is catering to a narrow use-case requirement. There may be a more general solution available
* Would MSC1767 (extensible events) obsolete this?
