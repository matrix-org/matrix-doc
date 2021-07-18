# MSC2545: Image Packs (Emoticons & Stickers)

Emoticons, or short emotes...we need them!

We also need proper stickers, too!

## Terminology
### Emoticons
Since there is a lot of confusion of how this relates to `m.emote`, why this isn't called custom emoji
etc, there it is:

`m.emote` is for emotion - and it has been incorrectly named this way. `m.action` would have been more
appropriate, as you use it to describe *actions*, not *emotions*. E.g. "/me is walking to the gym", or
"/me is happy" and *not* "/me happy".

That, however, is *not* what this MSC is about. Instead it is about emoticons, also known in short as
emotes.

Emoticons are just little images or text describing emotions or other things. Emoji are a subset of
emoticons, namely those found within unicode. Custom emoji here would actually refer to a custom emoji
font, that is your own rendering of 🦊, 🐱, etc., *not* new images. New images is what custom emoticons
are for.

Now, a client may choose to name these however they like, we already have a naming disparity between
spec and clients with groups vs communities. It is, however, imperative to name things in the spec
accurately after what they are.

### Stickers
Stickers already exist in Matrix. They are reusable images one can send, usually as a reaction sent
in the timeline to something. This MSC adds a way to distribute and define a source for a client to
send them.

## Proposal
### Emoticons in the formatted body
Emoticons have at least a shortcode and an mxc uri. They are sent as `<img>` tags currently already in
the spec, as such existing clients should already be able to render them, though not all clients currently
handle `img` tags. To allow clients to distinguish emoticons from other inline images, a new
property, `data-mx-emoticon`, is introduced. A client can chose to ignore the size attributes of emoticons
when rendering, and instead pick the size based on other circumstances. This could e.g. be used to
display emoticons in messages with only emoticons and emoji larger than usual, which is commonly found in
messengers. Such an `<img>` tag of a shortcode `emote` and an mxc uri `mxc://example.org/emote`
could look as follows:

```html
<img data-mx-emoticon src="mxc://example.org/emote" alt=":emote:" title=":emote:" height="32" />
```

Both the `alt` and the `title` attributes are specified as they serve different purposes: `alt` is
displayed if e.g. the emote does not load. `title` is displayed e.g. on mouse hover over the emote.
Thus, specifying both the `alt` and `title` attributes is required.

The `height` is just a height that looks good on most devices with the normal, default font size.
No width is displayed as to not weirdly squish non-square emotes. In order to maintain backwards-compatibility
with clients not supporting emotes, specifying the `height` is required.

If the new `data-mx-emoticon` attribute has a value it is ignored. Due to limitations of some libraries
the attribute may even look like `data-mx-emoticon=""`.

The `src` attribute *must* be an mxc url. Other URIs, such as `https`, `mailto` etc. are not allowed.

### Sending stickers
To send stickers the already speced `m.sticker` is used.

### Image types
Emoticons are recommended to have a size of about 128x128 pixels. Even though the fallback specifies
a height of 32, this is to ensure that the emotes still look good on higher DPI screens.

Stickers are recommended to have a size of up to 512x512 pixels.

Furthermore, these images should either have a mimetype of `image/png`, `image/gif` or `image/webp`.
They can be animated.

Due to the low resolution of emotes, `image/jpg`/`image/jpeg` has been purposefully excluded from this
list.

### Image pack event
The image pack event has a type of `m.image_pack`. It contains a key `images`, which is a map from a
short code to an image object. It may also contain a key `pack`, which is a pack object.

#### Pack object
The pack object consists of the following keys:
 - `display_name`: (String, optional) A display name for the pack. Defaults to the room name, if the
   image pack event is in the room. This does not have to be unique within all packs of a room.
 - `avatar_url`: (String, optional) The mxc uri of an avatar/icon to dipslay for the pack. Defautls
   to the room avatar, if the pack is in the room. If the room also does not have an avatar, or the
   image pack event is not in a room, this pack does not have an avatar.
 - `usage`: (String[], optional) An array of the usages for this pack. Possible usages are `emoticon`
   and `sticker`. If the usage is absent or empty, a usage for all possible usage types is to be assumed.
 - `attribution`: (String, optional) The attribution of this pack.

#### Image object
The image object conists of the following keys:
 - `url`: (String, requried) The mxc URL for this image
 - `body`: (String, optional) An optional body for this image, useful for the sticker body text or
   the emote alt text. Defaults to the short code.
 - `info`: (`ImageInfo`, optional) The already speced `ImageInfo` object used for the `info` block of
   `m.sticker` events.
 - `usage`: (String[], optional) An array of the usages for this image. If present and non-emtpy,
   this overrides the usage defined at pack level for this particular image.

#### Example image pack event
Taking all this into account, an example pack event may look as following:
```json
{
  "images": {
    "emote": {
      "url": "mxc://example.org/blah"
    },
    "sticker": {
      "url": "mxc://example.org/sticker",
      "usage": ["sticker"]
    }
  },
  "pack": {
    "display_name": "Awesome Pack",
    "usage": ["emoticon"]
  }
}
```

### Image sources
There are several places where a client is expected to look for these `m.image_pack` events, mainly
in their own account data and in room states.

#### User image packs
Each user can have their own personal image pack defined in their own account data, with the normal
`m.image_pack` event. The user is expected to be presented with these images in all rooms.

#### Room image packs
A room can have an unlimited amount of image packs, by specifying the `m.image_pack` state event with
different state keys. The user is expected to be presented with these images only in the room they
are defined in. To enable them to be presented in all rooms, see the section below.
An empty state key is the default pack for a room.
E.g. a discord bridge could set as state key
`de.sorunome.mx-puppet-bridge.discord` and have all the bridged emotes in said state event, keeping
bridged emotes from matrix emotes separate.

#### Image pack rooms
While room image packs are specific to a room and are only accessible within that room, image pack
rooms should be accessible from everywhere. They do not differentiate themselves from room emotes at
all, instead you set an event in your account data of type `m.image_pack.rooms` which outlines
which room image pack states are globally accessible for that user. For that, a `room` key contains
a map of room ids that map to state keys that map to an object. While this MSC does not define any
contents for this object, having this an object means greater flexibility in case of future changes.
The the contents of `m.image_pack.rooms` could look like the following:

```json
{
  "rooms": {
    "!someroom:example.org": {
      "": {},
      "de.sorunome.mx-puppet-bridge.discord": {}
    },
    "!someotherroom:example.org": {
      "": {}
    }
  }
}
```

Here three emote packs are globally accessible to the user: Two defined in `!someroom:example.org`
(one with blank state key and one with state key `de.sorunome.mx-puppet-bridge.discord`) and one in
`!someotherroom:example.org`.

### Image pack source priority and deduplicating
If a client gives image suggestions (emotes, stickers) to the user in some ordered fassion (e.g. a
ordered list where you click an entry), the order of the images should be predictable between rooms.
The ordering could look as following:
1. User image pack (images set in your own account)
2. Image pack rooms (rooms whos image packs you enabled to be accessible everywhere)
3. Room image packs (images defined in the currently open room)

Furthermore, clients are expected to deduplicate images based on their mxc url. This not only ensures
that, when viewing a room that you also have in `m.image_pack.rooms`, it won't be displayed twice,
but also if you have e.g. a bot which syncs emotes over multiple rooms, those will also be deduplicated.

### Sending
#### Emoticons
For emoticons a client could add deliminators (e.g. `:`) around around the image shortcode, meaning
that if an image has a shortcode of `emote`, the user can enter `:emote:` to send it. If there are
multiple emoticons with the same shortcode in a room the client could e.g. slugify the packs display
name and then have the user enter `:slug~emote:`. As slugs typically match `^[\w-]+$` that should
ensure complete-ability.

The alt / title text fo the `<img>` tag is expected to be the `body` of the emote, or, if absent, its
shotcode, optionally with tacked on deliminators.

#### Stickers
When sending a sticker the `body` of the `m.sticker` event should be set to the `body` defined for that
image, or its shortcode, if absent.

Furthermore, the `info` of the `m.sticker` event should be set to the `info` defined for that image,
or a blank object, if absent.

## Security Considerations
When sending an `<img>` tag in an encrypted room, the client will make a request to fetch
said image, in this case an emote. As there is no way to encrypt content behind `<img>` tags yet,
this could potentially leak part of the conversation. This is **not** a new security consideration,
it already exists. This, however, isn't much different from posting someone a link in an e2ee chat and
the recipient opens the link. Additionally, images, and thus emotes, are often cached by the client,
not even necessarily leading to an http query.

Related issue: https://github.com/matrix-org/matrix-doc/issues/2418

## Unstable prefix
The `m.image_pack` in the account data is replaced with `im.ponies.user_emotes`. The `m.image_pack` in
the room state is replaced with `im.ponies.room_emotes`. The `m.image_pack.rooms` is replaced with
`im.ponies.emote_rooms`.

Some existing implementations using `im.ponies.user_emotes` and `im.ponies.room_emotes` currently use
a dict called `short` which is just a map of the shortcode to the mxc url.

Some other implementations currently also call the `images` key `emoticons`.

## Alternatives
One can easily think of near infinite ways to implement emotes. The aspect of sending an `<img>` tag
and marking it as an emote with `data-mx-emoticon` seems to be pretty universal though, so the question
is mainly on different emote sources. For that, a separate MSC, [MSC1951](https://github.com/matrix-org/matrix-doc/pull/1951)
already exists, so it is reasonable to compare this one with that one:

### Comparison with MSC1951
MSC1951 defines a dedicated room as the only image pack source. This MSC, however, also allows you to bind image packs
to your own account, offering greater flexibility. In MSC1951 there can also only be a single image pack
pack in a room. This could be problematic in e.g. bridged rooms: You set some emotes or stickers from the matrix
side and a discord bridge would plop all the discord emotes and stickers in another pack in the same room.

The original sharing-focused idea of MSC1951 is still preserved: Once room types are a thing, you could
still easily have an image pack-only room.

MSC1951 defines a way to recommend using a pack of a different room - this MSC does not have an equivalent
to that. Instead, this MSC allows multiple image packs for a room, typically one where you already
chat in anyways. Furthermore it allows you to enable an image pack to be globally available for yourself
across all rooms you are in.

The core difference is how MSC1951 and this MSC define the image packs themselves: In MSC1951 you have to
set one state event *per image*. While this might seem like a nice idea on the surface, it doesn't
scale well. There are people who easily use and want hundreds or even thousands of image packs accessible.
A simple dict of shortcode to mxc URI seems more appropriate for this.

In general, MSC1951 feels like a heavier approach to image pack sources, while this MSC is more lightweight.

## Looking further
A couple of interesting points have been raised in the discussions of this MSC tangentially touch
custom emoticons but warrant an MSC for themselves, as they touch more on how `<img>` is working.
 - Figuring out how `<img>` should work with encrypted media.
 - Allow SVGs in the `<img>` tag. Current problem: Clients typically try to thumbnail the mxc URL,
   and most media repositories can't thumbnail SVGs. Possible solution: Somehow embed the mimetype.
 - For stickers: Recommend rendering sizes / resolutions
