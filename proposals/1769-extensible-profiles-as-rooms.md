# Proposal for extensible profiles as rooms

## Problem

Profiles are currently limited to display names and avatars.  We'd like users to
be able to publish arbitrary data about themselves instead (in a relatively
vcard-compatible fashion).

## Solution

Rather than creating a whole new set of APIs for defining and synchronising
profiles, the proposal is to simply put the data as state events in a room and
leverage all the existing infrastructure we have for sending and receiving state
events.

Clients should construct the default alias of the profile room is constructed as
`#@userid:<server>` (assuming aliases allow @; if not, `#_profile_userid:<server>`.
The server in the alias is that of the user whose profile is being considered.

This may be overridden per-room by setting a `profile` field in the
`m.room.member` for the user.  (Once we remove MXIDs from rooms in
[MSC1228](https://github.com/matrix-org/matrix-doc/issues/1228) then this
becomes irrelevant, as each user will get its own profile room alias for each
room it is in. That user would typically choose to point all those aliases at
the same underlying profile room).

This does not replace the current `displayname` and `avatar_url` field behaviour
on `m.room.membership` events which we have today.

This proposal is an alternative to [MSC489](https://github.com/matrix-org/matrix-doc/issues/489).

## Client behaviour

When a client loads a membership info page for a given user, it peeks into that
user's profile room in order to inspect their current profile state events.

N.B. This requires the peeking API to be improved from the legacy stopgap of using
/events.  One solution could be to pass /sync a list of additional rooms to attempt
to sync data for (somewhat as per the paginated /sync API did in
https://github.com/matrix-org/synapse/pull/893).  Defining this is left as a
separate MSC ([MSC1776](https://github.com/matrix-org/matrix-doc/issues/1776))

N.B. This also requires peeking to work over federation.  One simple solution to
this could be to require servers to join remote rooms they need to peek into
usinga null user - e.g. @:server or @null:server.  This would avoid having to
create a new membership event type for servers and complicate state auth/res
rules. Again, defining this is left as a separate MSC.
([MSC1777](https://github.com/matrix-org/matrix-doc/issues/1777))

The same peeking could also be used to display message events in the user's
profile room - the equivalent of their social network profile wall.

## Events

### m.profile

This would store a vCard-style profile of the user.

In the absence of a jsCalendar style format for expressing vCards as idiomatic
JSON (rather than as a parse tree of the vCard data, as jCard does (RFC7095)),
it could be something like this:

```json
{
    "type": "m.profile",
    "content": {
        "m.profile": {
            "name": {
                "family": "Gump",
                "given": "Forrest",
                "additional": "",
                "prefixes": "Mr.",
                "suffixes": ""
            },
            "fn": "Forrest Gump",
            "org": "Bubba Gump Shrimp Co.",
            "title": "Shrimp Man",
            "tel": [
                {
                    "type": [
                        "work", "voice"
                    ],
                    "uri": "tel:+1-111-555-1212"
                },
                {
                    "type": [
                        "home", "voice"
                    ],
                    "uri": "tel:+1-404-555-1212"
                }
            ],
            "address": [
                {
                    "type": [
                        "work"
                    ],
                    "pref": 1,
                    "label": "100 Waters Edge\nBaytown, LA 30314\nUnited States of America",
                    "pobox": "",
                    "extended": "",
                    "street": "100 Waters Edge",
                    "locality": "Baytown",
                    "region": "LA",
                    "postcode": "30314",
                    "country": "United States of America"
                },
                {
                    "type": [
                        "home"
                    ],
                    "label": "42 Plantation St.\nBaytown, LA 30314\nUnited States of America",
                    "pobox": "",
                    "extended": "",
                    "street": "42 Plantation St.",
                    "locality": "Baytown",
                    "region": "LA",
                    "postcode": "30314",
                    "country": "United States of America"
                }
            ],
            "email": "forrestgump@example.com",
            "rev": "20080424T195243Z"
        }
    }
}
```

Representing:

```vcard
N:Gump;Forrest;;Mr.;
FN:Forrest Gump
ORG:Bubba Gump Shrimp Co.
TITLE:Shrimp Man
PHOTO;MEDIATYPE=image/gif:http://www.example.com/dir_photos/my_photo.gif
TEL;TYPE=work,voice;VALUE=uri:tel:+1-111-555-1212
TEL;TYPE=home,voice;VALUE=uri:tel:+1-404-555-1212
ADR;TYPE=WORK;PREF=1;LABEL="100 Waters Edge\nBaytown\, LA 30314\nUnited States of America":;;100 Waters Edge;Baytown;LA;30314;United States of America
ADR;TYPE=HOME;LABEL="42 Plantation St.\nBaytown\, LA 30314\nUnited States of America":;;42 Plantation St.;Baytown;LA;30314;United States of America
EMAIL:forrestgump@example.com
REV:20080424T195243Z
```

The avatar would be split out into a normal Matrix avatar (or perhaps an `m.avatar`
room profile event).

Internationalisation could be done using "lang" keys, as per MSC1767.

### Other events

Other events could be custom data, using the normal fallback representations from
MSC1767 to determine fallbacks (m.text, m.html, m.message, m.thumbnail etc).
