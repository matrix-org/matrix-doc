# Markup for mathematical messages

Some people write using an odd language that has strange symbols.  No, I'm not
talking about computer programmers; I'm talking about mathematicians.  In order
to aid these people in communicating, Matrix should define a standard way of
including mathematical notation in messages.

This proposal presents a format using LaTeX, in contrast with a [previous
proposal](https://github.com/matrix-org/matrix-doc/pull/1722/) that used
MathML.

See also:

- https://github.com/vector-im/riot-web/issues/1945


## Proposal

A new attribute `data-mx-maths` will be added for use in `<span>` or `<div>`
elements.  Its value will be mathematical notation in LaTeX format.  `<span>`
is used for inline math, and `<div>` for display math.  The contents of the
`<span>` or `<div>` will be a fallback representation or the desired notation
for clients that do no support mathematical display, or that are unable to
render the entire `data-mx-maths` attribute.  The fallback representation is
left up to the sending client and could be, for example, an image, or an HTML
approximation, or the raw LaTeX source.  When using an image as a fallback, the
sending client should be aware of issues that may arise from the receiving
client using a different background colours.

Example (with line breaks and indentation added to `formatted_body` for clarity):

```json
{
  "content": {
    "body": "This is an equation: sin(x)=a/b",
    "format": "org.matrix.custom.html",
    "formatted_body": "This is an equation:
      <span data-mx-maths=\"\\sin(x)=\\frac{a}{b}\">
        sin(<i>x</i>)=<sup><i>a</i></sup>/<sub><i>b</i></sub>
      </span>",
    "msgtype": "m.text"
  },
  "event_id": "$eventid:example.com",
  "origin_server_ts": 1234567890,
  "sender": "@alice:example.com",
  "type": "m.room.message",
  "room_id": "!soomeroom:example.com"
}
```


## Other solutions

[MSC1722](https://github.com/matrix-org/matrix-doc/pull/1722/) proposes using
MathML as the format of transporting mathematical notation.  It also summarizes
some other solutions in its "Other Solutions" section.

In comparison with MathML, LaTeX has several advantages and disadvantages.

The first advantage, which is quite obvious, is that LaTeX is much less verbose
and more readable than MathML.  In many cases, the LaTeX code is a suitable
fallback for the rendered notation.

LaTeX is a suitable input method for many people, and so converting from a
user's input to the message format would be a no-op.

However, balanced against these advantages, LaTeX has several disadvantages as
a message format.  Some of these are covered in the "Potential issues" and
"Security considerations".


## Potential issues

### "LaTeX" as a format is poorly defined

There are several extensions to LaTeX that are commonly used, such as
AMS-LaTeX.  It is unclear which extensions should be supported, and which
should not be supported.  Different LaTeX-rendering libraries support different
sets of commands.

This proposal suggests that the receiving client should render the LaTeX
version if possible, but if it contains unsupported commands, then it should
display the fallback.  Thus, it is up to the receiving client to decide what
commands it will support, rather than dictating what commands must be
supported.  This comes at a cost of possible inconsistency between clients, but
is somewhat mitigated by the use of a fallback.

### Lack of libraries for displaying mathematics

see the corresponding section in [MSC1722](https://github.com/matrix-org/matrix-doc/pull/1722/)


## Security considerations

LaTeX is a [Turing complete programming
language](https://web.archive.org/web/20160110102145/http://en.literateprograms.org/Turing_machine_simulator_%28LaTeX%29);
it is possible to write a LaTeX document that contains an infinite loop, or
that will require large amounts of memory.  While it may be fun to write a
[LaTeX file that can control a Mars
Rover](https://wiki.haskell.org/wikiupload/8/85/TMR-Issue13.pdf#chapter.2), it
is not desireable for a mathematical formula embedded in a Matrix message to
control a Mars Rover.  Clients should take precautions when rendering LaTeX.
Clients that use a rendering library should only use one that can process the
LaTeX safely.

Clients should not render mathematics by calling the `latex` executable without
proper sandboxing, as `latex` was not written to handle untrusted input.  (see,
for example, https://hovav.net/ucsd/dist/texhack.pdf,
https://0day.work/hacking-with-latex/, and
https://hovav.net/ucsd/dist/tex-login.pdf .)

Certain commands such as `\newcommand` are potentially dangerous; clients
should either decline to process those commands, or should take care to ensure
that they are handled in safe ways.  In general, LaTeX commands should be
filtered using a whitelist rather than blacklist.

In general, LaTeX places a heavy burden on client authors to ensure that it is
processed safely.


## Conclusion

Math(s) is hard, but LaTeX makes it easier to write mathematical notation.
However, using LaTeX as a format for including mathematics in Matrix messages
has some serious downsides.  Nevertheless, if clients handle the LaTeX
carefully, or rely on the fallback representation, the concerns can be
addressed.
