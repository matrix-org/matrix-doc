# MSC1767: Extensible events in Matrix

##  Problem

 1. There is no formal mechanism of extending events with additional structured metadata.
 2. New events tend to reinvent the wheel rather than being able to reuse existing types.
 3. Clients don’t know how to render unknown event types.

This is seriously hindering uptake of new event types in Matrix - whether that’s
richer data types (stickers, location, calendaring, etc) or IOT-style use cases.
It also means we are currently using an underspecified solution for rich
messaging, as there has never been a previous agreed way of a jury rig solution
for rich messaging as we never previously agreed a way of expressing alternate
formats of displaying the same event.

## Solution

We group the keys of an event's contents together into different types. This lets
us address the problem by:

 1. Making it easy to extend events by adding new types into contents alongside existing ones.
 2. Making it easy to reuse existing types by adding new ones alongside existing ones.
 3. Letting clients render unknown event types by falling back to types in the event that they *do* recognise.

Events still have a primary type, which is used when sending them in Matrix.

The names of the keys in contents are now expected to be namespaced, given they
typically refer to types of events.  However, for compatibility, we can keep using
some of the original fields too.

Certain types (e.g. `m.message`, `m.caption`, `m.thumbnail`) which can contain
multiple alternative payloads in different formats express the alternatives as
an ordered list; most preferred first.

We provide short-form types (`m.text` and `m.html`) for the most common scenarios
of an event requiring a plain-text or HTML-formatted representation.

For convenience and compatibility, we keep `body` and `formatted_body` as
shorthand for plain-text and html-formatted fallback for events. We lose `format`
and `msgtype`, however.

The various types in an event's contents MUST refer to the same event.  Multiple
events should be linked using a `m.relates_to` reference rather than multiplexing
into a single event.

Here are proposals for different types of events:

### m.text and m.html

For compactness for this super-common case, we define a short form which is
equivalent to the longer form `m.message` example below:

```json5
{
    "type": "m.message",
    "content": {
        "m.text": "i am a *fish*", // doesn't have to be markdown, but useful as a "fallback" for HTML
        "m.html": "i am a <b>fish</b>"
    }
}
```

### m.message

m.message describes a simple textual instant message.

```json5
{
    "type": "m.message",
    "content": {
        "m.message": [
            {
                "mimetype": "text/html", // optional, default text/plain
                "body": "i am a <b>fish</b>"
            },
            {
                "mimetype": "text/plain",
                "body": "i am a *fish*"
            }
        ],
    }
}
```

### m.file

```json5
{
    "type": "m.file",
    "content": {
        "m.text": "foo.dat (12KB)",
        "m.file": {
            "url": "mxc://matrix.org/asdjkhcsd",
            "name": "foo.dat",
            "mimetype": "application/octet-stream",
            "size": 12345
        }
    }
}
```

### m.image

```json5
{
    "type": "m.image",
    "content": {
        "m.text": "matrix logo (640x480, 12KB)",
        "m.image": {
            "width": 640,
            "height": 480,
        },
        "m.file": {
            "url": "mxc://matrix.org/asdjkhcsd",
            "mimetype": "image/jpeg",
            "name": "logo.jpg",
            "size": 12345
        },
        "m.caption": [
            {
                "mimetype": "text/plain", // still optional
                "body": "matrix logo"
            }
        ],
        "m.thumbnail": [
            {
                "url": "mxc://matrix.org/thumb",
                "mimetype": "image/jpeg",
                "width": 160,
                "height": 120,
                "size": 123
            }
        ],
    }
}
```

The schemas for some of the types above have some overlap, such as `m.image` and `m.thumbnail` repeating
the same information (or `m.file` also duplicating that information). De-duplicating this doesn't appear
to be an easy feat when we consider schema complexity, thus the duplication is tolerable by this MSC.

It's also worth noting that thumbnails do not have dedicated captions as they are implicitly a thumbnail
of the captioned content in the event. Events are meant to have exactly one thing represented within them,
meaning that a second caption is not required.

### m.message containing original source text, to allow future edits:

***TODO: Compare with how edits work in practice, adjust as needed.***

```json5
{
    "type": "m.message",
    "content": {
        "m.message": [
            {
                "mimetype": "text/html",
                "body": "I am a <a href=\"http://www.reddwarf.co.uk\">fish</a>",
            },
            {
                "mimetype": "text/markdown",
                "original": true,
                "body": "I am a [fish](http://www.reddwarf.co.uk)",
            },
            {
                "mimetype": "text/plain",
                "body": "I am a fish < http://www.reddwarf.co.uk/ >",
            },
        ]
    }
}
```

### m.message interationalised

```json5
{
    "type": "m.message",
    "content": {
        "m.message": [
            {
                "body": "Je suis un poisson",
                "lang": "fr",
            },
            {
                "body": "I am a fish",
                "lang": "en_EN",
            }
        ]
    }
}
```

The french text is preferred and comes first, and a non-i18n aware client would
use it.  A smarter i18n-aware client would realise the user can't speak french
and fall through to the next one.

### m.video

```json5
{
    "type": "m.video",
    "content": {
        "m.text": "animated matrix logo (logo.mp4, 1280x720, 1m30s, 23.6MB)",
        "m.video": {
            "width": 1280,
            "height": 720,
            "duration": 90000,
        },
        "m.file": {
            "url": "mxc://matrix.org/v1d30",
            "mimetype": "video/mp4",
            "name": "logo.mp4",
            "size": 23654321
        },
        "m.caption": [
            {
                "body": "animated matrix logo"
            }
        ],
        "m.thumbnail": [
            {
                "url": "mxc://matrix.org/videothumb",
                "mimetype": "video/mp4",
                "animated": true,
                "width": 128,
                "height": 72,
                "size": 12300
            },
            {
                "url": "mxc://matrix.org/thumb",
                "mimetype": "image/jpeg",
                "width": 128,
                "height": 72,
                "size": 123
            }
        ],
    }
}
```

### Hypothetical IOT events (e.g. net.arasphere.temperature)

with text fallback:

```json5
{
    "type": "net.arasphere.temperature",
    "content": {
        "m.text": "The temperature is 37C",
        "m.html": "The temperature is <font color='#f00'>37C</font>",
        "net.arasphere.temperature": {
            "temperature": 37.0
        }
    }
}
```

### Hypothetical m.calendar.request

*Making this not-hypothetical would be a responsibility of another MSC.*

This is a deliberately chunky event designed to show a geotagged calendar request.

(In practice we should probably use the IETF jsCalendar format rather than inventing a
new one here, and to ensure interop with the JMAP folks.
https://tools.ietf.org/html/draft-ietf-calext-jscalendar-11)

```json
{
    "type": "m.calendar.request",
    "content": {
        "m.text": "Invite to Party at Bob's House on Feb 7th, 3pm",
        "m.html": "Invite to Party at <i>Bob's house</i> on Feb 7th, 3pm",
        "m.calendar.request": {
            "version": "2.0",
            "summary": "Party at Bob's house",
            "vEvent": {
                "dtStart": {
                    "date": "20180207T150000",
                    "tzId": "Europe/London"
                },
                "dtEnd": {
                    "date": "20180207T180000",
                    "tzId": "Europe/London"
                }
            }
        },
        "m.file": {
            "uri": "mxc://matrix.org/auiheiuh1eqwd",
            "mimetype": "text/calendar",
            "name": "bobs-party.ics",
            "size": 1246
        },
        "m.location": {
            "uri": "geo:37.786971,-122.399677;u=35",
            "description": "123 Fake Street"
        },
        "m.thumbnail": [
            {
               "uri": "mxc://localhost/JWEIFJgwEIhweiWJE",
               "width": 256,
               "height": 256,
               "mimetype": "image/jpeg",
               "size": 1024000
            }
        ],
    }
}
```

This would be nicer with displayhints support, but still works pretty well.

## Technical schema

***TODO***

This is where we put all the pre-spec prose for what this looks like, such as grammar,
acceptable formats, etc.

## Potential issues

It's a bit ugly to not know whether a given key will take a string, hash or array.

It's a bit arbitrary as to which fields are allowed lists of fallbacks.

It's a bit ugly that you have to look over the keys of contents to see what types
are present, but better than duplicating this into an explicit `types` list (on balance).

We're skipping over defining rules for which fallback combinations to display
(i.e. "display hints") for now; these can be added in a future MSC if needed.
MSC1225 contains a proposal for this.

I think Erik had some concerns about mixing together types at the top level of `content`
but I've forgotten the details.  Hopefully these are mitigated by the revised approach.

## Security considerations

We can't apply ACLs serverside to the types embedded in the event contents.
However, this is inevitable given the existence of E2E, so we have no choice but
for clients to apply ACLs clientside (e.g. refuse to render an m.image contents
on an event if the sender doesn't have enough PL to send an m.image event).

Like today, it's possible to have the different representations of an event not match,
thus introducing a potential for malicious payloads (text-only clients seeing something
different to HTML-friendly ones). Clients could try to do similarity comparisons, though
this is complicated with features like HTML and arbitrary custom markup (markdown, etc)
showing up in the plaintext or in tertiary formats on the events. Historically, room
moderators have been pretty good about removing these malicious senders from their rooms
when other users point out (quite quickly) that the event is appearing funky to them.

## Migration, availability, and unstable prefix

Given the disruption of migrating clients, bridges, servers, etc to the new event shape,
this will require an amount of advertising and warning to land.

While this MSC is not considered stable by the specification, implementations *must* use
`org.matrix.msc1767` as a prefix to denote the unstable functionality. For example, sending
a `m.text` event would mean sending a `org.matrix.msc1767.text` event instead.

Currently visible events are `m.room.message` with a `msgtype` to distinguish
between `m.text`, `m.image`, `m.file`, etc. This MSC outlines how those would be 
translated to the new event shape, but does not cover fallback as obviously.

A suggested migration would be to send/receive `m.room.message` events as formatted today
with the additional fields from this MSC. For example, here's a simple text message:

```json5
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "Hello World",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>Hello</b> World",
        "m.text": "Hello World",
        "m.html": "<b>Hello</b> World"
    }
}
```

This looks very awful, but it at least shows that the parent type is meant to be a `m.text` event.
Similar semantics apply to videos, audio, etc. This has a risk of potentially running up against the
65K limit, though for the vast majority of messages this will be fine.

After a period of time (***TBD***), implementations would stop sending the `m.room.message` hybrid
and switch to solely to the defined types of this MSC, accepting breakage of any clients.

Before all that happens, this MSC would need to be adopted into the spec. As such, implementations
wishing to trial the migration ahead of this MSC's inclusion in the spec would use the unstable
prefix mentioned above. The example `m.room.message` event becomes:

```json5
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "Hello World",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>Hello</b> World",
        "org.matrix.msc1767.text": "Hello World",
        "org.matrix.msc1767.html": "<b>Hello</b> World"
    }
}
```

## Changes from MSC1225

 * converted from googledoc to MD, and to be a single PR rather than split PR/Issue.
 * simplifies it by removing displayhints (for now - deferred to a future MSC).
 * removes all references to mixins, as the term was scaring people and making it feel far too type-theoretic.
 * replaces the clunky m.text.1 idea with lists for types which support fallbacks.
 * removes the concept of optional compact form for m.text by instead having m.text always in compact form.
 * tries to accomodate most of the feedback on GH and Google Docs from MSC1225.
