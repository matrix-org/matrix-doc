# Configuration to Control Crawling

Since Matrix is decentralised, there is no single directory where all rooms are
listed.  Some people are trying to solve this by creating bots that crawl
public Matrix rooms to list in a directory, giving users a place where they can
search for rooms.  This is similar to how users rely on search engines to find
web pages.

However, although a room might be publicly available, room administrators might
not want the room to be indexed, or may not want certain aspects of a room to
be crawled.  With web pages, the site owner can specify their preferences to
crawlers using a [file placed in a well-known
location](https://en.wikipedia.org/wiki/Robots_exclusion_standard).

This proposal defines a way in which crawling and indexing preferences can be
expressed for Matrix rooms.


## Proposal

For the purposes of this proposal, each bot should be given a name (or names)
following the Java package naming convention.  For example, the Voyager bot
from t2bot.io could use the name `io.t2bot.voyager`.

A new room state event `m.room.robots` is used to define what bots are allowed
to index the rooms, and what data they are allowed to fetch and store from the
room.  The event is an object whose values are configuration objects, which are
a map from parameter name to parameter value.  Bots should use the
configurations based on their name: when a bot wants to get a parameter from
the configuration:

- it checks if the `m.room.robots` state has a key that matches its name, and
  if the associated configuration object has a key for the parameter that it is
  looking for.  If it exists, then it uses that value.
- If the state does not have a key that matches its name, or the configuration
  object does not contain the parameter in question, then the bot strips off a
  component from its name, and looks for a configuration object using that
  name.
- This is continued until the bot finds a parameter, or until it has stripped
  off all the components from its name.  If no parameter value has been found,
  then the bot will check if the state has a key of `*` that has the parameter
  configured, and if so, will use that value.
- Otherwise, it will use the default value for that parameter.

A bot may have multiple names that could be applicable to it.  For example, if
uhoreg.ca ran an instance of the Voyager bot, then the configuration for both
`io.t2bot.voyager` and `ca.uhoreg.voyager` could be applicable.  In this case,
the bot should order the two names in some way, check the configuration using
one name, and if no value is found, to check the configuration using the next
name.  This can also be done with multiple names.  In general, the names should
be ordered from more specifig to more general, so in this case,
`ca.uhoreg.voyager` would be checked first, then `io.t2bot.voyager`, and
finally `*`.

Parameters defined in this proposal are:

- `allow`: (boolean) whether the bot is allowed to crawl the room.  If `false`,
  then the bot may not display any information about the room to users who are
  searching its directory, and may not store any information about the room
  other than its existence and its crawling preferences.  The bot should also
  avoid joining the room, or leave the room if it has already joined.  If `true`, the bot
  may index the room, and may store and display the room's ID, name, avatar,
  aliases, canonical alias, topic, encryption status, join rules, and history
  visibility.  Some other aspects of the room are controlled by specific
  parameters.  Other aspects that are not listed above, nor controlled by a
  different parameter, are left to the discretion of the bot owner, but in
  general should err on the side of privacy.  Default: `true` if the
  `m.room.join_rules` is `public`, and `false` otherwise.
- `members`: (boolean) whether the bot is allowed to index the room's members.
  This includes members' Matrix IDs, display names, and avatars.  Default:
  `true` if `m.room.join_rules` is `public` and `false` otherwise.
- `messages`: (boolean) whether the bot is allowed to index the room's
  messages.  Default: `true` if `m.room.history_visibility` is
  `world_readable`, and `false` otherwise.
- `log`: (boolean) whether the bot is allowed to display logs of the room to
  users.  This will be `false` if `messages` is `false`.  Default: `true` if
  `m.room.history_visibility` is `world_readable`, and `false` otherwise.
- `follow`: (boolean) whether the bot is allowed to follow links to other
  rooms.  This will be `false` if `messages` is `false`.  Default: `true` if
  `m.room.history_visibility` is `world_readable`, and `false` otherwise.

Bots may use other parameter names, but the names that are not listed in the
Matrix spec must be namespaced following the Java package naming convention.

Example:

Suppose a room with `m.room.join_rules` set to `public`, and
`m.room.history_visibility` set to `world_readable` has the following
`m.room.robots`:

```json
{
  "*": {
    "members": false
  },
  "io.t2bot": {
    "allow": false
  },
  "io.t2bot.voyager": {
    "allow": true,
    "io.t2bot.foo": "bar"
  }
}
```

In this case, the Voyager bot would be allowed to index the room, no other bots
from t2bot.io would be allowed to, but any other non-t2bot.io bots would be
allowed to.  No bots would be allowed to index the members, since that is
specified in the configuration for `*`.  All bots would be allowed to index
messages and show logs to users, due to the history visibility settings (except
for non-Voyager t2bot.io bots, since they are not allowed to index anything).
Voyager additionally has a custom parameter of `io.t2bot.foo` defined.


## Tradeoffs / potential issues / notes

There are many aspects of a room whose crawling could potentially be controlled
by individual parameters.  This proposal attempts to strike a reasonable
balance between allowing administrators control over crawling, and avoiding too
many configuration options.  Thus the thus parameters mainly target the parts
of the room that are the most privacy-sensitive.

As mentioned above, not all parts of the room are covered by configuration
parameters.  In this proposal, we trust bot owners to use their judgement in
determining what is acceptable or not.  Given that the preferences expressed in
the room state are purely advisory, and the bot could just ignore the
preferences, this is not seen as a security issue.  However, bot owners are
advised that if there is doubt whether some information should be indexed, that
they should err on the side of privacy.  Bots can also use the existing
parameters to inform their decision on whether to index certain information.
For example, a bot that tracks which web pages are linked to from various
Matrix rooms might use the `log` and/or `follow` parameters to determine
whether to process links in a certain room, depending on what it does with that
information.  Bots are also able to define their own paramaters to control
certain parts of their indexing, if the existing parameters are not sufficient.

If allowed, bots may peek into the room to examine the `m.room.robots` state to
determine whether they are allowed to index the room; a bot that is not allowed
to index the room may not want to join the room.  However, bots may not be able
to peek in rooms that its server is not already a part of until
[MSC1777](https://github.com/matrix-org/matrix-doc/pull/1777) is fixed.

Clients can display the `m.room.robots` state to users to notify them of the
crawling and indexing preferences of the room.  This proposal does not attempt
to define how this information is displayed to the user.

Individual users may have preferences on whether bots index their messages or
their membership in a room.  This proposal does not address that issue, but it
might be able to be addressed by using a similar method in combination with
[MSC1769](https://github.com/matrix-org/matrix-doc/pull/1769).


## Security considerations

The configuration information is purely advisory, and should not be relied on
for security since bots can simply ignore the configuration.


## Unstable prefix

Until this lands in the spec, the state event type
`org.matrix.msc2291.room.robots` should be used in place of `m.room.robots`.
