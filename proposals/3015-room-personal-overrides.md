# MSC3015: Room state personal overrides 

Very often users want to personally rename rooms to see it in list like they wants, especially for DM rooms. But room
name is shared thing, so if they rename it for yourself, all other members will see this rename too. 

Examples of problem: 

1. Very often other people want to rename DM rooms with me and can do this, because we both are admins. So they set the
   alternative name of that DM room (eg `Korepov Alexey` instead of `Alexey Murz Korepov`) - this works well on their
   side. But, as result on my side, I see that room in my rooms list with my name, instead of remote user name.

2. The user has two DM rooms with different Matrix users, but both have name "Alice" without avatar. As result they see
   two identical rooms in the list with same name and it is unclear which room is which.
   If attempting to solve this problem via renaming rooms, the problem described in 1 occurs.

3. This problem often happens for rooms from bridged networks, when we talk with same person via different networks, and
   want to mark each room personally. This can be solved via adding suffixes with remote network name to room name on
   Bridge side, but people want to change other parts of room name too. For example, one person can have different names
   in each network (eg "Alexey Korepov" on VK, "Korepov Alexey" on Skype, "Alex" on WhatsApp, "Murz" on Telegram), and I
   want to see all rooms with him as similar names, and also maybe attach personal avatar to that rooms.
   
4. Some networks (eg IRC, Slack) also have no per-room avatars, so they are bridged with empty or identical avatars, that
   makes harder to diffirentiate them in avatar-only list of rooms, so users want to override the avatars personally too.

Most of other modern messengers (Telegram, Skype, Viber, WhatsApp) already have this feature, but only for DM rooms via
reusing smartphone's addressbook to store personal names of contacts. And moving from that messengers to Matrix confuses
the people, because they can't rename personal chats in his own list like before.

# Proposal

For solve this problem I propose to use [room's account
data](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-user-userid-rooms-roomid-account-data-type)
item with same key as overriden state event type, but with `override.` prefix, to store personal overrides of needed 
state any room for each user individually, and overriden content, here is example for room name and avatar overrides:

**`override.m.room.name`**
```json
{
  "name": "The room name"
}
```
**`override.m.room.avatar`**
```json
{
  "info": {
    "h": 398,
     "mimetype": "image/jpeg",
     "size": 31037,
     "w": 394
  },
  "url": "mxc://example.org/JWEIFJgwEIhweiWJE"
}
```

By default those items are absent. They are added only when user make the personal override, and cleared if user
remove the personal name for room (or make it empty). Regarding to spec, the account data's key can't be deleted,
so if user wants to remove the personal override (aka "Reset to default"), the value of the key should become 
empty (`{}`).

Those overrides can be used for all types of rooms: DMs (to rename personal contacts or set custom photo to avatar, 
add notes to topic), public rooms (to set desired personal name, eg in user's native language), public Spaces, etc.

For not allow to override bad things, I think we must define an allowlist of state types, that can be overriden:
- `m.room.name`
- `m.room.avatar`
- `m.room.topic`
- and maybe also `m.room.pinned_events` for implement personal pinning?

Also we can allow even `m.room.member` for personally override room members names and avatars too. But for this task
may be better to wait for user profiles implementation from [MSC1769: Extensible profiles as rooms](https://github.com/matrix-org/matrix-doc/pull/1769),
to override profile info values via same technic like in regular rooms, this will allow even complements the remote 
profiles: add personal phone number for your contact, that missed in public profile and know only by you, leave personal
notes about that contact, etc.

# Client support

## Displaying:

When client displays the room information (eg in room list), for all allowlisted state keys it should lookup the 
corresponding room's account data key with `override.` prefix, if it exists and not empty - replace the content
of that state event to overriden before rendering. Clients may show both values (global and personal) and explain
that this room have an overriden personal value, that is seen only for current user.

## Adding, removing, renaming:

Clients should provide a way to privately override allowed room state values and clearly explain the difference 
between global and personally overriden values.

In room list this can be implemented via "Rename room personally" or "Set personal name for room" menu item in
right-click menu, and similar way for avatar.

In room settings page personal name can be implemented via button "Set personal name for this room", which will be
available even if user have no permission to change the room name, and same for avatar. If personal value is filled,
it should be shown near the global room value, with ability to remove it.

# Server support

This MSC does not need any changes on server side.

# Potential issues

1. User can set a personal value that is identical to the current global room value. This may cause confusion as the
   client will not see future global value changes. Clients should consider providing the user a suggestion to remove
   personal override for follow future renames of room. And for other renames - explain that personal override will not 
   follow the future changing of global value.

# Alternatives

1. Instead of setting personal name for rooms via
   [room's account_data](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-user-userid-rooms-roomid-account-data-type)
   we can set personal names directly for Matrix users (mxid), like other messengers (Telegram, WhatsApp, etc) doing.
   This will give similar behavior for DM rooms, but will make impossible to set personal names of rooms with several
   users (or DM rooms with bots), and intersects with per-room display names feature. And this way will be better to
   implement together with "[Contacts](https://github.com/vector-im/roadmap/issues/10)" feature, which is planned in
   Element and in issue [Contact List & Renaming Contacts](https://github.com/matrix-org/matrix-doc/issues/2936).

# Unstable prefix

Clients should use `org.matrix.msc3015.[m.state.type].override` for room account data key instead of proposed, while this
MSC has not been included in a spec release.
