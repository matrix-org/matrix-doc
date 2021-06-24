# MSC2881: Message Attachments

*This MSC is especially for media image attachments to message, but I try to make it extendable for multiple attachment types (files, videos, and in future - external URLs, links to other Matrix events, etc). So, in most of examples, I am using "image", but it means, that, instead of image, there may be another attachment type.*

In the current implementation each media (file, image, video) can be sent only via a separate event to the room. But in most cases even one media is not sent alone, it must be commented via some text by the sender. So the user often wants to attach some images (one or several) directly to their text message when composing it, not after or before it.

And now the user can send images only before the message (or after it) as a separate message, but they can't attach images during the composing process to send them when the text is finished, together with the text message in one event.

On the display side, when the user sends multiple images, the problem is that each image is displayed alone, as separate event with full width in timeline, not linked to the message, and not grouped to the gallery.

Messages with multiple attachments now already implemented in many messengers, for example - in Skype, Slack, VK Messenger. And Matrix, because lack of support, now have problems with bridging those messages to Matrix rooms.


## Proposal

### Option one "Best fallback"

For solve described problem, I propose to add `m.attachment` relation type to current events, that will point to other media events in room, which must be shown as attachment to current event, and `is_attachment: true` marker field to all media, that was send to be an attachment for some message.

With having this feature, Matrix client should allow users to attach one or multiple media (images, video, files) to message on client side, without instant sending of them to room, and send them together with text message.

When user press "Send" button, Matrix client do the upload of all media, that user attached to message, as separate events to room (how it is done now), before sending message with typed text. And after sending of all attachments is finished, client send message with aggregating event, using `m.relates_to` field (from the [MSC2674: Event relationships](https://github.com/matrix-org/matrix-doc/pull/2674)), that points to all previously sent events with media, to group them into one gallery.

For exclude showing those events in modern clients before grouping event added, I propose extend separate media events via adding "marker" field `is_attachment: true`, if clients got this value - they must exclude showing this media in timeline, and shows them only in gallery with grouping event.

Example of media event, that send before aggregating event:
```json
{
  "msgtype": "m.image",
  "body": "Image 1.jpg",
  "info": {
    "mimetype": "image/jpg",
    "size": 1153501,
    "w": 963,
    "h": 734,
  },
  "is_attachment": true,
  "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg"
},
```
And aggregating event, to send after all message attachments:
```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Here is my photos and videos from yesterday event",
    "m.relates_to": [
      {
        "rel_type": "m.attachment",
        "event_id": "$id_of_previosly_send_media_event_1"
      },
      {
        "rel_type": "m.attachment",
        "event_id": "$id_of_previosly_send_media_event_2"
      }
    ]
  }
}
```

For edits of "message with attachments" we can reuse same "m.relates_to" array via simply adding `"rel_type": "m.replace"` item to it, here is example:
```json
    "m.relates_to": [
      {
        "rel_type": "m.attachment",
        "event_id": "$id_of_previosly_send_media_event_1"
      },
      {
        "rel_type": "m.replace",
        "event_id": "$id_of_original event"
      },
      {
        "rel_type": "m.attachment",
        "event_id": "$id_of_previosly_send_media_event_2"
      }
    ]
```

For delete (redact action) message with attachments, we must also apply `redact` action to each message attachment event too.

#### Fallback:

I see no serious problems with fallback display of attachments. For Matrix clients, that don't yet support this feature, the attachments will be represented as separate media events, like the user upload each attachment separately, before sending main message.

### Option two "Best implementation"

As lite alternative to option one, we can send only one event with direct links to all attached media, instead of sending separate event for each attachment, because it will give less "spam" for room. Eg when user is sending message with 20 attachments - it will send only one event to room, instead of 21 like in option one implementation. But the main problem with this option is *fallback*.

This can be done together with [MSC1767: Extensible events in Matrix](https://github.com/matrix-org/matrix-doc/pull/1767) with adding new type `m.attachments`, which will contain the group of attached elements.

Each element of `m.attachments` array has a structure like a message with media item (`m.image`, `m.video`, etc), here is example of the message with this field:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Here is my photos and videos from yesterday event",
    "m.attachments": [
      {
        "msgtype": "m.image",
        "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg",
        "body": "Image 1.jpg",
        "info": {
          "mimetype": "image/jpg",
          "size": 1153501,
          "w": 963,
          "h": 734,
        }
      },
      {
        "msgtype": "m.video",
        "url": "mxc://example.com/KUAQOe1GECk2TgdtedkftISg",
        "body": "Video 2.mp4",
        "info": {
          "mimetype": "video/mp4",
          "size": 6615304,
          "w": 1280,
          "h": 720,
        }
      }
    ]
  }
}
```

#### Fallback

For fallback display of attachments in old Matrix clients, we can attach them directly to `formatted_body` of message, here is HTML representation:
```html
<p>Here is my photos and videos from yesterday event</p>
<div class="mx-attachments">
  <p>Attachments:</p>
  <ul>
    <li><a href="https://example.com/_matrix/media/r0/download/example.com/KUAQOesGECkQTgdtedkftISg">Image 1.jpg</a></li>
    <li><a href="https://example.com/_matrix/media/r0/download/example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18">Video 2.mp4</a></li>
  </ul>
</div>
```
and JSON of `content` field:
```json
"content": {
    "msgtype": "m.text",
    "body": "Here is my photos and videos from yesterday event\nAttachments:\nhttps://example.com/_matrix/media/r0/download/example.com//KUAQOesGECkQTgdtedkftISg\nhttps://example.com/_matrix/media/r0/download/example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18",
    "format": "org.matrix.custom.html",
    "formatted_body": "<p>Here is my photos and videos from yesterday event</p>\n<div class=\"mx-attachments\"><p>Attachments:</p>\n<ul>\n<li><a href=\"https://example.com/_matrix/media/r0/download/example.com//KUAQOesGECkQTgdtedkftISg\">Image 1.jpg</a></li>\n<li><a href=\"https://example.com/_matrix/media/r0/download/example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18\">Video 2.mp4</a></li>\n</ul></div>"
  }
```
And modern clients, that have support of the attachments feature, will cut the `div.mx-attachment` tag and replace it to rich gallery block with thumbnails of attachments.

If [MSC2398: proposal to allow mxc:// in the "a" tag within messages](https://github.com/matrix-org/matrix-doc/pull/2398) will be merged before this, we can replace `http` urls to direct `mxc://` urls, for support servers, that don't allow downloads without authentication and have other restrictions.

**If we will come up with better fallback display, maybe bring this option as main suggestion?**


## Client support

### Compose recommendations:

In the message composer, on "upload file" or "paste file from clipboard" event, the Matrix client must not instantly upload the file to the server, but the client must show its thumbnail in the special area, with the ability to remove it and to add more media. *Alternatively, it can start uploading instantly to improve the speed of the following message sending process, but there is no way to delete media in Matrix API yet ([MSC2278: Deleting attachments for expired and redacted messages](https://github.com/matrix-org/matrix-doc/blob/matthew/msc2278/proposals/2278-deleting-content.md), so server will store each file, even if it is not attached to the message.*

On "message send" action, Matrix client must upload each attached media to server, get `mxc` of it, post an event to room, and attach its `event_id` to current message contents in `m.relates_to` array (option one); or collect all `mxc` urls in `m.attachments` array on option two.

If the user uploads only one media and leaves the message text empty, media can be sent as regular `m.image` or similar message, like in current implementation.

Editing interface can be represented exactly like the composer interface, where user have the textarea for input message text, and area with all current attachments as tiny thumbnails, in which he can rearrange attachments, remove one of current attachments (that will remove its line from array of `m.relates_to` and do the `redact` action on corresponding event with media in option one, or remove item from `m.attachments` in option two; and delete media file using [MSC2278](https://github.com/matrix-org/matrix-doc/blob/matthew/msc2278/proposals/2278-deleting-content.md)), add new attachment (that will upload it as new event with refer to it in edited message `m.relates_to` array in option one / added to `m.attachments` in option two).


### Display recommendations:

On the client side, attachments can be displayed as grid of clickable thumbnails, like the current `m.image` events, but with a smaller size, having fixed height, like a regular image gallery. On click, Matrix client must display media in full size, and, if possible, as a gallery with "next-previous" buttons. Also clients can implement collapse/expand action on gallery grid.

If the message contains only one attachment, it can be displayed as full-width thumbnail in timeline, like current `m.image` and `m.video` messages.

Example of composer interface implementation with multiple attachments we can lookup in [Slack](https://slack.com/), [VK Messenger](https://vk.com/messenger), [Skype](https://skype.com).

For prevent showing of attachments as regular media in timeline before main aggregating event will be added to room, clients should visually hide media events, that have `"is_attachment": true` value, to display them later in gallery, but can already start downloading of attachments thumbnails, for speed-up display of them in gallery.

Together with [MSC2675: Serverside aggregations of message relationships](https://github.com/matrix-org/matrix-doc/pull/2675) all attachments will can be even aggregated on server side.

## Server support

This MSC does not need any changes on server side.


## Potential issues

1. On bad connection to server Matrix client can send attachments as events with `"is_attachment": true` but not send final `m.message` event, this will lead to posting invisible media to room. This can be solved on client side via caching unsent group of events, and repeat sending when connection will be recovered.

2. In option one - individual media event, to which `m.message` refers, can be deleted (redacted) after. As result, `m.message` will contain relation to redacted event. In this situation Matrix clients can exclude this item from display.

3. In option one - there are no restrictions, that message with attachments can refer only to other events, that have `"is_attachment": true`, because this is not too easy to control, and in theory user can post message, that can refer to other media, owned by other users, and `redact` event will try to delete them. But the API should restrict regular user to redact events of other users (if he isn't moderator), so those `redact` actions should already be successfully ignored by server.

4. If client attach too much media to one message, he can got rate limiting problem on server side. This can be solved via splitting and delaying send of attachments, to match server rate limits.

## Alternatives

1. An alternative can be embedding images (and other media types) directrly into message body via html tags to "body" field (`<a href>` or `<img src>`), but this will make composing, extracting and stylizing of the attachments harder.

2. Next alternative is reuse [MSC1767: Extensible events in Matrix](https://github.com/matrix-org/matrix-doc/pull/1767) for attaching and grouping media attachments, but in current state it requires only one unique type of content per message, so we can't attach, for example, two `m.image` items into one message. So, instead of separate current issue, we can extend [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) via converting `content` to array, to allow adding several items of same type to one message, [here](https://github.com/matrix-org/matrix-doc/pull/1767/files#r532373829) is my comment with this suggestion.

3. There are also [MSC2530: Body field as media caption](https://github.com/matrix-org/matrix-doc/pull/2530) but it describes only text description for one media, not several media items, and very similar [MSC2529: Proposal to use existing events as captions for images](https://github.com/matrix-org/matrix-doc/pull/2529) that implement same thing, but via separate event. But if we send several medias grouped as gallery, usually one text description is enough for most cases, also this MSC can be the replacement of #2530 / #2529, when user send text + only one media item. And the main problem with those MSC, that in most cases, it is the image that is the comment to the text message, and not vice versa, as implied in the phrase "image caption" from those MSC, [here is my comment about this in that MSC](https://github.com/matrix-org/matrix-doc/pull/2529#issuecomment-736638196).

We still can implement both things together (my *MSC2881* as one main text with as attachments + separate short *caption texts* for each attachment via [MSC2530](https://github.com/matrix-org/matrix-doc/pull/2530)), but this will give very complex UI for manage attachments in Matrix clients, so, I think, Matrix don't need so complex feature and only one text for all attachments will be enouth, for manage full-featured "Photos Albums" with descriptions and comments we already have more suitable tools.

4. Other alternative can be posting `m.message` event at first, and link all attachments to it later via `m.relates_to` field, something like this:
```json
{
  "msgtype": "m.image",
  "body": "Image 1.jpg",
  "info": {
    "mimetype": "image/jpg",
    "size": 1153501,
    "w": 963,
    "h": 734,
  },
  "m.relates_to": [
    {
      "rel_type": "m.attachment_to",
      "event_id": "$id_of_main_message"
    }
  ],
  "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg"
},
```      
But this way will give harder way to render of main message event, because Matrix clients must do the search of all attached events manually in timeline, and server will be unable to aggregate them to main message.


## Future considerations

In future, we may extend the `m.attachments` field with new types to allow attaching external URL as cards with URL preview, oEmbed entities, and other events (for example, to forward the list of several events to other room with the user comment).


## Unstable prefix
Clients should use `org.matrix.msc2881.m.attachments`, `org.matrix.msc2881.m.attachment` and `org-matrix-msc2881-mx-attachments` strings instead of proposed, while this MSC has not been included in a spec release.
