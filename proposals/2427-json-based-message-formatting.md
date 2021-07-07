
# JSON-based message formatting
## Problem
Matrix formatting is currently based on a subset of HTML. While HTML is easy to
render in a browser, other platforms have to either make a completely custom
renderer, or use an existing renderer where the supported subset may not match
the subset used in Matrix. Additionally, custom attributes like `data-mx-color`
mean that even clients that can use existing renderers will need to preprocess
the HTML or modify the renderer.

## Proposal
The proposed solution is a object-based message formatting system. While the current 
JSON transport is not the most efficient byte count wise, it would be trivial to switch 
to a binary object representation when using this system.

While a custom formatting system means new renderers will need to be made in
all environments, it is easier to make a custom renderer for text formatted
using a well-defined object based system, than it is to parse HTML and try to handle
all the quirks.
A formatted message consists of one or more chunks. Each chunk is a JSON
object, containing one primary field or one secondary field and zero or more tertiary fields. The
chunks are located in an array under the `m.formatted` key of the `content`
object. All fields are namespaced.

##### Primary field
The primary field is the main content of the chunk. Each chunk must have
exactly one primary field or exactly one secondary field.

* `m.text` (string) - A normal text chunk.
* `m.image` (string) - An inline image. The value must be a `mxc://` URI to an
  image.

##### Secondary 'flattenable' fields
These fields specify a context for their children, they consist of an object array.

If a chunk does not contain a primary field, or a known secondary field or m.list, implementations should attempt to find an object array and flatten that.

This will allow future minor versions to specify new secondary fields without breaking compatibility.
To avoid ambiguity multiple object arrays in one chunk are illegal.

example of flattening:
```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    { "unknown.thing": [
        {"m.text": "I like cheese "},
        {"m.italic": true, "m.text": "Thiiiiiis" },
        {"m.text": " much"}
      ]
    }
  ]
}
```
turns into this:
```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.text": "I like cheese "},
    {"m.italic": true, "m.text": "Thiiiiiis" },
    {"m.text": " much"}
  ]
}
```

Flattening has deliberately not been defined for array[arrayN[chunk]] Since implementations then for the fallback path would need to check each array to a deep level to decide if one chunk is legal or not.
Uses for this likely require heavily modified renderers, and thus should be addressed in a major version, or a custom context specific version.
* `m.spoiler` (array[chunk]) marks a range as a spoiler
* `m.quote` (array[chunk]}) marks a range as a quote

###### Special field
Implementations should have atleast basic support for lists.
(e.g to add a newline after each second level array member)
* `m.list` (array[array[chunk]]) renders as a list.

##### Tertiary fields (attributes)
Tertiary fields are attributes that change the way the chunk is rendered. The
number of tertiary fields is not restricted, but some fields have other
conditions. Unknown tertiary field types should be ignored.

`simple` attributes are booleans that must either be `true` or not be set at
all.

Valid for `m.text` and `m.image`:
* `m.reference` (string) - A Matrix identifier (as per [Identifier Grammar](https://matrix.org/docs/spec/appendices#identifier-grammar))
  or a URI (as per [RFC 3986](https://tools.ietf.org/html/rfc3986)).
  * `m.preview` (bool) - Whether or not clients should show a preview the resource that `m.reference` points to.
  * `m.mention` (bool) - Whether or not to mention (ping) the referenced Matrix user. Only valid if `m.reference` contains a Matrix user ID.
* `m.mime` (string) - The mime type of an object, clients can use this for example for syntax highlighting.
* `m.color.bg` (string) - Background color as RGB hex

Only valid for `m.text`:
* `m.color.fg` (string) - <font color="#FF00FF">Foreground color</font> as RGB hex
* `m.bold` (simple) - **Bold**
* `m.italic` (simple) - *Italic*
* `m.strikethrough` (simple) - ~~Strikethrough~~
* `m.underline` (simple) - <u>Underline</u>
* `m.superscript` (simple) - <sup>Super</sup>script
* `m.subscript` (simple) - <sub>Sub</sub>script
* `m.monospace` (string) - `Monospace` text.
  
Only valid for `m.image`:
* `m.width` (int) - Width for image.
* `m.height` (int) - Height for image.
* `m.alt` (string) - The alt text and hover title for the image.

Only valid for `m.spoiler`:
* `m.reason` (string) - The reason the section is in a spoiler.

Only valid for `m.list`:
* `m.list.style` (string) - The type of list, `bullet` or `numeric ascending` or `numeric descending`. Defaults to `bullet`.
* `m.list.bullet` (string) - The character to display as the bullet, only valid for bullet lists. Default is up to the renderer.
* `m.list.start` (int) - The first index, only valid for numeric lists. Defaults to 1.

##### Versioning
Events that use the `m.formatted` key MUST also contain the `m.formatted.version`
key, which specifies the version of the formatting schema. The value of the
version field should be two numeric identifiers, the major and minor version
number, separated by a dot. The initial version is `0.1`.

Minor version changes may only add or deprecate secondary or flattenable fields. Major version
changes may also change primary fields or parsing logic in general. When a client encounters a major version
that it does not recognize, it should fall back to rendering the plaintext body.

For example, a future minor version could include support for replies to a part of a message, i.e. rich quotes.

A future major version may add support for tables.

### Disadvantages compared to current Matrix HTML
* The current version does not support tables due to their implementation complexity
* More bytes. However, switching Matrix to a more efficient binary format would
  make it have less bytes. Especially a partially structured binary format
  could be significantly more efficient.

### Examples
```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.reference": "@user:example.org", "m.text": "Pretty user"},
    {"m.text": ": Good day, user!\nDid you see this image?\n"},
    {"m.width": 128, "m.height": 64, "m.alt": "Fancy image", "m.image": "mxc://example.org/ABCDEF"}
  ]
}
``` 
```html
<a href="https://matrix.to/#/@user:example.org">Pretty user</a>: Good day, user!<br/>
Did you see this image?<br/>
<img src="mxc://example.org/ABCDEF" width="128" height="64" alt="Fancy image" title="Fancy image" />
```

---

```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.text": "I like cheese "},
    {"m.italic": true, "m.text": "Thiiiiiis" },
    {"m.text": " much"}
  ]
}
```
```html
I like cheese <em>Thiiiiiis</em> much
```

---

```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.color.fg": "#ff0000", "m.text":"R"},
    {"m.color.fg": "#ffdb00", "m.text":"A"},
    {"m.color.fg": "#49ff00", "m.text":"I"},
    {"m.color.fg": "#00ff92", "m.text":"N"},
    {"m.color.fg": "#0092ff", "m.text":"B"},
    {"m.color.fg": "#4900ff", "m.text":"O"},
    {"m.color.fg": "#ff00db", "m.text":"W"}
  ]
}
```
```html
<font data-mx-color="#ff0000">R</font>
<font data-mx-color="#ffdb00">A</font>
<font data-mx-color="#49ff00">I</font>
<font data-mx-color="#00ff92">N</font>
<font data-mx-color="#0092ff">B</font>
<font data-mx-color="#4900ff">O</font>
<font data-mx-color="#ff00db">W</font>
```

```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.text":"Consider these points:"},
    {
    "m.list.style": "numeric ascending",
    "m.list": [
        [{"m.text": "convincing point"}],
        [{"m.text": "extremely convincing point"}],
        [{"m.text": "irrelevant point"}]
      ]
    }
  ]
}
```
```html
Consider these points:
<ol>
  <li>convincing point</li>
  <li>extremely convincing point</li>
  <li>irrelevant point</li>
</ol>
```

## Alternatives
### Indexed formatting entities
Instead of having the text within the formatting entities, the formatting
entities could use indexes to refer to a separate plain text string. However,
this would require specifying the exact encoding used for indexing, and was
therefore rejected.
