# MSC3124: Handling spoilers in plain-text message fallback

Spoilers are described in
[MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010) and
[MSC2557](https://github.com/matrix-org/matrix-doc/pull/2557), but
these proposals provide unclear and partially unusable guidance on how
clients should represent spoilers in the plain-text fallback version
of a message.  As a result, most clients simply include the spoilered
content verbatim in the fallback.  However, most clients, even
HTML-aware ones, also display snippets of the fallback verbatim in
contexts such as notifications and channel previews.  This leads to
users frequently viewing spoilered content that they did not choose to
see, hindering the usability of spoilers as a feature to protect
users' mental health and emotional well-being.  The goal of this
proposal is to provide better guidance for client developers on
handling spoilers when sending and receiving messages, to ensure that
spoilers are a safe, effective, and usable feature for all Matrix
users.

## Proposal

(The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC
2119](https://tools.ietf.org/html/rfc2119).)

Spoilers are a vital accessibility feature for users with mental
health issues.  The ability for communities to set guidelines on what
kinds of content should be spoiled, and for community members to
participate in discussions with confidence that they won't see that
content without their active consent, is important for communities to
be able to protect users' well-being. Thus, it is important that
clients strive as much as possible to never display spoilered content
without users' active consent.

[MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010) and
[MSC2557](https://github.com/matrix-org/matrix-doc/pull/2557) do not
set out any specific requirements on how or whether spoilered content
should be represented in the plaintext fallback versions of messages.
Thus, clients should always assume that fallback contains the
spoilered content verbatim and is not safe to display to users.
Therefore, HTML-aware clients SHOULD NOT make any use of the `body`
key for `org.matrix.custom.html` messages containing spoilers.
Instead, if a plain-text representation of a message containing
spoilers is needed, HTML-aware clients SHOULD convert the HTML
formatted body into a plain-text representation of their choosing.
This representation SHOULD NOT contain spoilered content; clients MAY
substitute a placeholder string, or a sequence of Unicode "full block"
characters (█), among other options.

As an additional note,
[MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010)
encourages preserving the semantics of spoilers in plain-text fallback
by uploading spoilered content as a text file, and inserting the MXC
URI into the fallback. However, this method is incompatible with
encrypted rooms; the file would need to be encrypted, and then the
encryption key material would need to be included alongside the MXC
URI, but there's no specification for how to include that data inline
within a message.  Thus, this method SHOULD NOT be used in
encrypted rooms.

## Potential issues

HTML-aware clients may still need to use plain-text representations of
messages in various contexts.  Therefore, to follow this
recommendation, those clients will need to convert HTML messages into
plain-text representations.  It is important that clients perform this
conversion in a way that preserves the semantics of the message.
Potential pitfalls include simply stripping out HTML tags, with no
other modifications; as well as failing to hide spoilers, this
approach would also remove formatting elements that significantly
affect the tone or meaning of messages, such as `<del>` tags.
Depending on where and how the plain-text representation is being
displayed, the latter problem may or may not be important, but
properly redacting spoilers is crucial regardless.

## Alternatives

Instead of placing the onus on receiving clients to handle spoilers
safely, an alternative would be to require that sending clients always
somehow obfuscate spoilers in the plaintext fallback.  However, there
is no way to enforce or check whether clients are following this
requirement, so in general it is not safe for receiving clients to
assume that all incoming messages satisfy such a requirement.  Thus,
receiving clients would still need to follow this proposal's
recommendation in case they are interacting with spec-non-compliant
sending clients.
