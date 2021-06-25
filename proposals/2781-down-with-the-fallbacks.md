# MSC2781: Deprecate fallbacks in the specification

Currently replies require clients to send and parse a fallback representation of
the replied to message. Something similar is planned for edits. While at least
in theory fallbacks should make it simpler to start supporting replies in a new
client, they actually introduce a lot of complexity and implementation issues
and block a few valuable features. This MSC proposes to deprecate and eventually
remove those fallbacks. It is an alternative to
[MSC2589](https://github.com/matrix-org/matrix-doc/pull/2589), which intends to
double down on fallbacks.

### Issues with the current fallbacks

#### Stripping the fallback

To reply to a reply, a client needs to strip the existing fallback of the first
reply. Otherwise replies will just infinitely nest replies. [While the spec doesn't necessarily require that](https://github.com/matrix-org/matrix-doc/issues/1541),
not doing so risks running into the event size limit, but more importantly, it
just leads to a bad experience for clients actually relying on the fallback.

Stripping the fallback sadly is not trivial. Most clients did that wrong at some
point. At the point of writing this, FluffyChat seems to fail stripping the
fallback, while Riot/Element did fail to do so in the past, when `<mx-reply>`
tags were not evenly matched. Since clients can send arbitrary byte sequences,
every client needs to basically parse untrusted input and sanitize it. A normal
html parser will fail stripping a `</mx-reply><mx-reply></mx-reply>` sequence in
some cases. If you use a regex to strip the fallback, you may be able to be
attacked using regex DOS attacks (although that is somewhat mitigated by the
maximum event size). In the end there are quite a few edge cases, that are not
covered in the existing specification, since it doesn't specify the exact rules
to strip a fallback at all.

Stripping the fallback from body is even more complicated, since there is no way
to distinguish a quote from a reply reliably.

#### Creating a new fallback

To create a new fallback, a client needs to add untrusted html to its own
events. This is an easy attack vector to inject your own content into someone
elses reply. While this can be prevented with enough care, since Riot basically
had to fix this issue twice, it can be expected that other clients can also be
affected by this.

#### Requirement of html for replies

The spec requires rich replies to have a fallback using html:

> Rich replies MUST have a format of org.matrix.custom.html and therefore a formatted_body alongside the body and appropriate msgtype.

This means you can't reply using only a `body` and you can't reply with an
image, since those don't have a `formatted_body` property currently. This means
a text only client, that doesn't want to display html, still needs to support
html anyway and that new features are blocked, because of fallbacks.

This is also an issue with edits, where the combination of edit fallback and
reply fallback is somewhat interesting: You need to send a fallback, since the
event is still a reply, but you can't send a reply relation, since this is an
edit. So for clients relying on the edit fallback, you send a broken reply
fallback, that doesn't get stripped, even when the client supports rich replies.

#### Format is somewhat badly specified

Further complicating the stripping and creation portion of fallbacks is, that
they are somewhat badly specified. While the fallback and html use are required,
the spec only says how a fallback "should" look, not how it "must" look. In
practice there are various variations of the fallback floating around, where the
tame ones are just localized, but others are just straight up missing suggested
links or tags.

Basically a client can't rely on the fallback being present currently or it
folllowing any kind of shape or form.

#### Replies leak history

A reply includes the `body` of another event. This means a reply to an event can
leak data to users, that joined this room at a later point, but shouldn't be
able to see the event because of visibility rules or encryption. While this
isn't a big issue, there is still an issue about it: https://github.com/matrix-org/matrix-doc/issues/1654

Replies are also sometimes localized. In those cases they leak the users
language selection for their client, which may be personal information.

#### Low value of fallbacks

The above issues would be somewhat acceptable, if reply fallbacks would provide
some value to clients. Generally they don't though. The Qt html renderer breaks
on `<mx-reply>` tags, so you need to strip them anyway to render replies.
Bridges usually try to bridge to native replies, so they need to strip the reply
part (https://github.com/matrix-org/matrix-doc/issues/1541). Even the IRC bridge
seems to send a custom fallback, because the default fallback is not that
welcome to the IRC crowd.

Clients that actually use the fallback (original Riot/Android for example) tend
to do so for quite some while, because the fallbacks are "good enough", but in
the end that provides a worse experience for everyone involved. For example you
couldn't see what image was replied to for the longest time. Just "X replied to
an image with: I like this one" is not valuable, when 3 images were sent.

Only replies to actual text messages have a somewhat reasonable fallback. The
other ones do not provide any more value than a plain "this is a reply" tag,
unless the client also already supports event links.

#### Fallback discussion blocks new features

On any proposal that wants to enable replies to other events or replies with
other events, the discussion around "how to handle the fallback" happens. Any
such MSC needs to specify, how the fallback should look like and the events need
to support the `formatted_body` field. This blocks a lot of improvements, that
could be done to replies as a whole. Often commentors even ask for the issues
with fallbacks to be fixed on that MSC.

#### Localization

Since the fallback is added as normal text into the message, it needs to be
localized for the receiving party to understand it. This however proves to be a
challenge, since users may switch languages freely in a room and it is not easy
to guess, which language was used in a short message. One could also use the
client's language, but that leaks the user's localization settings, which can be a
privacy concern and the other party may not speak that language. Alternatively a
client can just send english fallbacks, but that significantly worsens the
experience for casual users in non-english speaking countries.

## Proposal

Deprecate the rich reply fallback. Clients should stop sending them and should
consider treating `<mx-reply>` parts as either something to be unconditionally
stripped or as something to be escaped as invalid html. In the future the
fallback should be removed from the spec completely with only a note left, that
it may exist in old events. Clients may send replies without a formatted_body
now.

Furthermore, no fallback should be used for edits, since just adding an asterisk
before the same message does not provide much value to users and it complicates
the implementation of edits for no tangible benefit.

The fallback for more niche features, like in room verification can stay, since
that feature is actually somewhat hard to implement and some clients may never
support encryption.

As a result of this, you would be able to reply with an image or edit a video.
New clients would also be able to implement edits and replies more easily, as
they can sidestep a lot of pitfalls.

## Potential issues

Obviously you can't remove the fallback from old events. As such clients would
still need to do something with them in the near future. I'd say just not
handling them in a special way should be okay after some unspecified period of
time.

Clients not implementing rich replies or edits may show some slightly more
confusing messages to users as well. I'd argue though that in most cases, the
reply is close enough to the replied to message, that you would be able to guess
the correct context. Replies would also be somewhat easier to implement and
worst case, a client could very easily implement a little "this is a reply"
marker to at least mark replies visually.

Same applies to edits. If 2 very similar messages appear after one another,
someone new to online messaging would assume, this is a correction to the
previous message. That may even be more obvious to them than if the message was
prefixed with a `*`, since that has been confusing to users in the past. Since
edits would now look exactly like a normal message, they would also be
considerably easier to implement, since you just need to replace the former
message now, similar to a redaction, and not merge `content` and `new_content`.

## Alternatives

[MSC2589](https://github.com/matrix-org/matrix-doc/pull/2589): This adds the
reply text as an addional key. While this solves the parsing issues, it
doesn't address the other issues with fallbacks.

One could also just stick with the current fallbacks and make all clients pay
the cost for a small number of clients actually benefitting from them.

Lastly one could introduce an alternative relation type for replies without
fallback and deprecate the current relation type (since it does not fit the new
format for relations anyway). We could specify, that the server is supposed to
send the replied_to event in unsigned to the client, so that clients just need
to stitch those two events together, but don't need to fetch the replied_to
event from the server. It would make replies slightly harder to implement for
clients, but it would be simpler than what this MSC proposes.

## Security considerations

Removing the fallback from the spec may lead to issues, when clients experience
the fallback in old events. This should not add any security issues the
client didn't already have from interpreting untrusted html, though. In all
other cases this should **reduce** security issues.

## Appendix A: Clients not supporting rich replies

Of the 18 clients listed in the [matrix client matrix](https://matrix.org/client-matrix)
10 are listed as not supporting replies:

- weechat-matrix: Actually has an [implementation](https://github.com/poljar/weechat-matrix/issues/86) to send replies although it may be [broken](https://github.com/poljar/weechat-matrix/issues/233). Doesn't render rich replies. Hard to implement because of the single socket implementation, but may be easier in the Rust version.
- Quaternion: [Blocked because of fallbacks](https://github.com/quotient-im/libQuotient/issues/245).
- matrixcli: [Doesn't support formatted messages](https://github.com/ahmedsaadxyzz/matrixcli/issues/10).
- Ditto Chat: [Doesn't support replying?](https://gitlab.com/ditto-chat/ditto-mobile/-/issues/83), but [does some special stuff for rendering?](https://gitlab.com/ditto-chat/ditto-mobile/-/issues/8)
- Mirage: Supports rich replies, but has [doesn't strip the fallback correctly](https://github.com/mirukana/mirage/issues/89) and uses the fallback to render them.
- Fractal: [Unsupported](https://gitlab.gnome.org/GNOME/fractal/-/issues/194). Has some reports, that the fallback doesn't look nice though.
- Nio: [Unsupported](https://github.com/niochat/nio/issues/85).
- Pattle: Client is not being developed anymore.
- Seaglass: Doesn't support rich replies, but is [unhappy with how the fallback looks](https://github.com/neilalexander/seaglass/issues/51)?
- Miitrix: Somewhat unlikely to support it, I guess?
- matrix-commander: No idea.

So in summary, half of the listed clients don't support replies. At least one
client doesn't support it because of the fallback (Quaternion). 3 of the command
line clients probably won't support replies, since they don't support formatted
messages and replies require html support for at least sending. Fractal and Nio
don't seem to use html for rendering either. It would be interesting to hear the
opionion of the developers of those clients, if dropping the fallback would
negatively impact them or if they would be fine with implementing proper
replies.

## Unstable prefix

Clients should use the prefix `im.nheko.msc2781.` for all their event types, if
they implement this MSC in a publicly available release or events may otherwise
bleed into public rooms.
