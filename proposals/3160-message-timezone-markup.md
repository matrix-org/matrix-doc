# MSC3160: Attach timezone metadata to time information in messages

When communicating across timezones, you sometimes want to agree on a time with
others, for example when to have a meeting. If somebody says "let's meet at 8pm"
, everybody else in the room has to think in what timezone the other person is,
and work out the math in their head how that relates to their timezone,
if different.

Luckily, computers are great at math, and so to facilitate this, clients could 
allow to represent a point in time with special markup in a message,
adding the timezone of the sender. The clients of the other users in the room
can then depending on their local timezone work out the math and render
the point in time in the timezone of the user.

## Proposal

For events of type `m.room.message` with `msgtype` of `m.text` and `format` of 
`org.matrix.custom.html` in the `content` field, the `formatted_body` field 
supports containing the
[`<time>` element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/time)
to annotate text describing a point in time with the timezone of the sender.
Here is an example:

```json
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "format": "org.matrix.custom.html",
        "formatted_body": "Shall we have a quick call at <time datetime=\"2021-04-30T09:00-0200\">9am tomorrow</time>?"
    }
}
```

The `datetime` attribute should always contain a timezone, which is not required
 by HTML. We should probably also only allow one specific format,
 as opposed to HTML.
 
No other attributes are allowed on the `<time>` element.

### Possible user interface

Clients could either detect when the user writes something that looks like
a timestamp and either automatically wrap it in a `<time>` element, or propose
to do so. Alternatively, clients could have a time button in the composer
formatting options that allows to add a time with a dialog, requiring less
sophisticated time pattern detection while typing.

When rendering an `<time>` element, clients could render it in a special way,
and allow to interact with it to show the time in the timezone of the sender,
or any other timezone.

## Potential issues

For web clients, Firefox always
[reports the local timezone to be UTC](https://bugzilla.mozilla.org/show_bug.cgi?id=1330890)
when "resist fingerprinting" is on. Web clients would therefore need to at
least confirm the detected timezone with the user to ensure it does not get
sent with a different timezone than the user is actually in and create
a whole new level of confusion.

The `datetime` attribute in HTML does not allow to just specify a time of day
without specifying the day, which could be nice to have. In that case, clients
could just use the current day. It might create confusion though if the sender
didn't mean to explicitly communicate a day.

## Alternatives

Have a custom attribute (`mx-timezone-offset`) and parse the text in the `time`
element to convert it. Having a machine readable version of the timestamp has
the advantage that clients don't need to agree how to read the freeform time
text in the body.

## Security considerations

None I can think of.

## Unstable prefix

Not needed given the time element is already part of html?
