---
title: "Appendices"
weight: 70
type: docs
---

## Unpadded Base64

*Unpadded* Base64 refers to 'standard' Base64 encoding as defined in
[RFC 4648](https://tools.ietf.org/html/rfc4648), without "=" padding.
Specifically, where RFC 4648 requires that encoded data be padded to a
multiple of four characters using `=` characters, unpadded Base64 omits
this padding.

For reference, RFC 4648 uses the following alphabet for Base 64:

    Value Encoding  Value Encoding  Value Encoding  Value Encoding
        0 A            17 R            34 i            51 z
        1 B            18 S            35 j            52 0
        2 C            19 T            36 k            53 1
        3 D            20 U            37 l            54 2
        4 E            21 V            38 m            55 3
        5 F            22 W            39 n            56 4
        6 G            23 X            40 o            57 5
        7 H            24 Y            41 p            58 6
        8 I            25 Z            42 q            59 7
        9 J            26 a            43 r            60 8
       10 K            27 b            44 s            61 9
       11 L            28 c            45 t            62 +
       12 M            29 d            46 u            63 /
       13 N            30 e            47 v
       14 O            31 f            48 w
       15 P            32 g            49 x
       16 Q            33 h            50 y

Examples of strings encoded using unpadded Base64:

    UNPADDED_BASE64("") = ""
    UNPADDED_BASE64("f") = "Zg"
    UNPADDED_BASE64("fo") = "Zm8"
    UNPADDED_BASE64("foo") = "Zm9v"
    UNPADDED_BASE64("foob") = "Zm9vYg"
    UNPADDED_BASE64("fooba") = "Zm9vYmE"
    UNPADDED_BASE64("foobar") = "Zm9vYmFy"

When decoding Base64, implementations SHOULD accept input with or
without padding characters wherever possible, to ensure maximum
interoperability.

## Signing JSON

Various points in the Matrix specification require JSON objects to be
cryptographically signed. This requires us to encode the JSON as a
binary string. Unfortunately the same JSON can be encoded in different
ways by changing how much white space is used or by changing the order
of keys within objects.

Signing an object therefore requires it to be encoded as a sequence of
bytes using [Canonical JSON](#canonical-json), computing the signature
for that sequence and then adding the signature to the original JSON
object.

### Canonical JSON

We define the canonical JSON encoding for a value to be the shortest
UTF-8 JSON encoding with dictionary keys lexicographically sorted by
Unicode codepoint. Numbers in the JSON must be integers in the range
`[-(2**53)+1, (2**53)-1]`.

We pick UTF-8 as the encoding as it should be available to all platforms
and JSON received from the network is likely to be already encoded using
UTF-8. We sort the keys to give a consistent ordering. We force integers
to be in the range where they can be accurately represented using IEEE
double precision floating point numbers since a number of JSON libraries
represent all numbers using this representation.

{{% boxes/warning %}}
Events in room versions 1, 2, 3, 4, and 5 might not be fully compliant
with these restrictions. Servers SHOULD be capable of handling JSON
which is considered invalid by these restrictions where possible.

The most notable consideration is that integers might not be in the
range specified above.
{{% /boxes/warning %}}

{{% boxes/note %}}
Float values are not permitted by this encoding.
{{% /boxes/note %}}

```py
import json

def canonical_json(value):
    return json.dumps(
        value,
        # Encode code-points outside of ASCII as UTF-8 rather than \u escapes
        ensure_ascii=False,
        # Remove unnecessary white space.
        separators=(',',':'),
        # Sort the keys of dictionaries.
        sort_keys=True,
        # Encode the resulting Unicode as UTF-8 bytes.
    ).encode("UTF-8")
```

#### Grammar

Adapted from the grammar in <http://tools.ietf.org/html/rfc7159>
removing insignificant whitespace, fractions, exponents and redundant
character escapes.

    value     = false / null / true / object / array / number / string
    false     = %x66.61.6c.73.65
    null      = %x6e.75.6c.6c
    true      = %x74.72.75.65
    object    = %x7B [ member *( %x2C member ) ] %7D
    member    = string %x3A value
    array     = %x5B [ value *( %x2C value ) ] %5B
    number    = [ %x2D ] int
    int       = %x30 / ( %x31-39 *digit )
    digit     = %x30-39
    string    = %x22 *char %x22
    char      = unescaped / %x5C escaped
    unescaped = %x20-21 / %x23-5B / %x5D-10FFFF
    escaped   = %x22 ; "    quotation mark  U+0022
              / %x5C ; \    reverse solidus U+005C
              / %x62 ; b    backspace       U+0008
              / %x66 ; f    form feed       U+000C
              / %x6E ; n    line feed       U+000A
              / %x72 ; r    carriage return U+000D
              / %x74 ; t    tab             U+0009
              / %x75.30.30.30 (%x30-37 / %x62 / %x65-66) ; u000X
              / %x75.30.30.31 (%x30-39 / %x61-66)        ; u001X

#### Examples

To assist in the development of compatible implementations, the
following test values may be useful for verifying the canonical
transformation code.

Given the following JSON object:

```json
{}
```

The following canonical JSON should be produced:

```json
{}
```

Given the following JSON object:

```json
{
    "one": 1,
    "two": "Two"
}
```

The following canonical JSON should be produced:

```json
{"one":1,"two":"Two"}
```

Given the following JSON object:

```json
{
    "b": "2",
    "a": "1"
}
```

The following canonical JSON should be produced:

```json
{"a":"1","b":"2"}
```

Given the following JSON object:

```json
{"b":"2","a":"1"}
```

The following canonical JSON should be produced:

```json
{"a":"1","b":"2"}
```

Given the following JSON object:

```json
{
    "auth": {
        "success": true,
        "mxid": "@john.doe:example.com",
        "profile": {
            "display_name": "John Doe",
            "three_pids": [
                {
                    "medium": "email",
                    "address": "john.doe@example.org"
                },
                {
                    "medium": "msisdn",
                    "address": "123456789"
                }
            ]
        }
    }
}
```

The following canonical JSON should be produced:

```json
{"auth":{"mxid":"@john.doe:example.com","profile":{"display_name":"John Doe","three_pids":[{"address":"john.doe@example.org","medium":"email"},{"address":"123456789","medium":"msisdn"}]},"success":true}}
```

Given the following JSON object:

```json
{
    "a": "日本語"
}
```

The following canonical JSON should be produced:

```json
{"a":"日本語"}
```

Given the following JSON object:

```json
{
    "本": 2,
    "日": 1
}
```

The following canonical JSON should be produced:

```json
{"日":1,"本":2}
```

Given the following JSON object:

```json
{
    "a": "\u65E5"
}
```

The following canonical JSON should be produced:

```json
{"a":"日"}
```

Given the following JSON object:

```json
{
    "a": null
}
```

The following canonical JSON should be produced:

```json
{"a":null}
```

### Signing Details

JSON is signed by encoding the JSON object without `signatures` or keys
grouped as `unsigned`, using the canonical encoding described above. The
JSON bytes are then signed using the signature algorithm and the
signature is encoded using [unpadded Base64](#unpadded-base64). The resulting base64
signature is added to an object under the *signing key identifier* which
is added to the `signatures` object under the name of the entity signing
it which is added back to the original JSON object along with the
`unsigned` object.

The *signing key identifier* is the concatenation of the *signing
algorithm* and a *key identifier*. The *signing algorithm* identifies
the algorithm used to sign the JSON. The currently supported value for
*signing algorithm* is `ed25519` as implemented by NACL
(<http://nacl.cr.yp.to/>). The *key identifier* is used to distinguish
between different signing keys used by the same entity.

The `unsigned` object and the `signatures` object are not covered by the
signature. Therefore intermediate entities can add unsigned data such as
timestamps and additional signatures.

```json
{
   "name": "example.org",
   "signing_keys": {
     "ed25519:1": "XSl0kuyvrXNj6A+7/tkrB9sxSbRi08Of5uRhxOqZtEQ"
   },
   "unsigned": {
      "age_ts": 922834800000
   },
   "signatures": {
      "example.org": {
         "ed25519:1": "s76RUgajp8w172am0zQb/iPTHsRnb4SkrzGoeCOSFfcBY2V/1c8QfrmdXHpvnc2jK5BD1WiJIxiMW95fMjK7Bw"
      }
   }
}
```

```py
def sign_json(json_object, signing_key, signing_name):
    signatures = json_object.pop("signatures", {})
    unsigned = json_object.pop("unsigned", None)

    signed = signing_key.sign(encode_canonical_json(json_object))
    signature_base64 = encode_base64(signed.signature)

    key_id = "%s:%s" % (signing_key.alg, signing_key.version)
    signatures.setdefault(signing_name, {})[key_id] = signature_base64

    json_object["signatures"] = signatures
    if unsigned is not None:
        json_object["unsigned"] = unsigned

    return json_object
```

### Checking for a Signature

To check if an entity has signed a JSON object an implementation does
the following:

1.  Checks if the `signatures` member of the object contains an entry
    with the name of the entity. If the entry is missing then the check
    fails.
2.  Removes any *signing key identifiers* from the entry with algorithms
    it doesn't understand. If there are no *signing key identifiers*
    left then the check fails.
3.  Looks up *verification keys* for the remaining *signing key
    identifiers* either from a local cache or by consulting a trusted
    key server. If it cannot find a *verification key* then the check
    fails.
4.  Decodes the base64 encoded signature bytes. If base64 decoding fails
    then the check fails.
5.  Removes the `signatures` and `unsigned` members of the object.
6.  Encodes the remainder of the JSON object using the [Canonical
    JSON](#canonical-json) encoding.
7.  Checks the signature bytes against the encoded object using the
    *verification key*. If this fails then the check fails. Otherwise
    the check succeeds.

## Identifier Grammar

Some identifiers are specific to given room versions, please refer to
the [room versions specification](/#room-versions) for more
information.

### Standard Identifier Format

Throughout the specification some identifiers will mention they use the
"Standard Identifier Format", which is a common definition for how
identifiers are to be represented. Identifiers which are not explicitly
listed in this specification or do not use the Standard Identifier Format
have undefined grammar.

The requirements of identifiers using this format are:

 * An identifier may not be less than one character or more than 255 characters
   in length.
 * Identifiers must start with one of the characters `[a-z]`, and be entirely
   composed of the characters `[a-z]`, `[0-9]`, `-`, `_` and `.`.
 * Identifiers starting with the characters `m.` are reserved.
 * Identifiers which are not described in the specification should follow the
   Java Package Naming Convention to namespace their identifier. This is typically
   a reverse DNS format, such as `com.example.identifier`.

This identifier format is intended for solely non-user-visible identifiers.

{{% boxes/note %}}
Identifiers which are accepted into the specification through the proposal process
are assumed to use this Standard Identifier Format unless explicitly mentioned
otherwise in the proposal.
{{% /boxes/note %}}

{{% boxes/note %}}
Identifiers can and do inherit grammar from this specification. For example, "this
identifier uses the Standard Identifier Format, though without the namespacing
requirements" - this means that `m.` is still reserved, but that implementations
do not have to use the reverse DNS scheme to namespace their custom identifier.
{{% /boxes/note %}}

{{% boxes/rationale %}}
ASCII characters do not have issues with homoglyphs or alternative encodings which
might interfere with the identifier's purpose. Additionally, using lowercase
characters prevents concerns about case sensitivity.
{{% /boxes/rationale %}}

### Server Name

A homeserver is uniquely identified by its server name. This value is
used in a number of identifiers, as described below.

The server name represents the address at which the homeserver in
question can be reached by other homeservers. All valid server names are
included by the following grammar:

    server_name = hostname [ ":" port ]

    port        = 1*5DIGIT

    hostname    = IPv4address / "[" IPv6address "]" / dns-name

    IPv4address = 1*3DIGIT "." 1*3DIGIT "." 1*3DIGIT "." 1*3DIGIT

    IPv6address = 2*45IPv6char

    IPv6char    = DIGIT / %x41-46 / %x61-66 / ":" / "."
                      ; 0-9, A-F, a-f, :, .

    dns-name    = 1*255dns-char

    dns-char    = DIGIT / ALPHA / "-" / "."

— in other words, the server name is the hostname, followed by an
optional numeric port specifier. The hostname may be a dotted-quad IPv4
address literal, an IPv6 address literal surrounded with square
brackets, or a DNS name.

IPv4 literals must be a sequence of four decimal numbers in the range 0
to 255, separated by `.`. IPv6 literals must be as specified by
[RFC3513, section 2.2](https://tools.ietf.org/html/rfc3513#section-2.2).

DNS names for use with Matrix should follow the conventional
restrictions for internet hostnames: they should consist of a series of
labels separated by `.`, where each label consists of the alphanumeric
characters or hyphens.

Examples of valid server names are:

-   `matrix.org`
-   `matrix.org:8888`
-   `1.2.3.4` (IPv4 literal)
-   `1.2.3.4:1234` (IPv4 literal with explicit port)
-   `[1234:5678::abcd]` (IPv6 literal)
-   `[1234:5678::abcd]:5678` (IPv6 literal with explicit port)

{{% boxes/note %}}
This grammar is based on the standard for internet host names, as
specified by [RFC1123, section
2.1](https://tools.ietf.org/html/rfc1123#page-13), with an extension for
IPv6 literals.
{{% /boxes/note %}}

Server names must be treated case-sensitively: in other words,
`@user:matrix.org` is a different person from `@user:MATRIX.ORG`.

Some recommendations for a choice of server name follow:

-   The length of the complete server name should not exceed 230
    characters.
-   Server names should not use upper-case characters.

### Common Identifier Format

The Matrix protocol uses a common format to assign unique identifiers to
a number of entities, including users, events and rooms. Each identifier
takes the form:

    &string

where `&` represents a 'sigil' character; `string` is the string which
makes up the identifier.

The sigil characters are as follows:

-   `@`: User ID
-   `!`: Room ID
-   `$`: Event ID
-   `+`: Group ID
-   `#`: Room alias

User IDs, group IDs, room IDs, room aliases, and sometimes event IDs
take the form:

    &localpart:domain

where `domain` is the [server name](#server-name) of the homeserver
which allocated the identifier, and `localpart` is an identifier
allocated by that homeserver.

The precise grammar defining the allowable format of an identifier
depends on the type of identifier. For example, event IDs can sometimes
be represented with a `domain` component under some conditions - see the
[Event IDs](#room-ids-and-event-ids) section below for more information.

#### User Identifiers

Users within Matrix are uniquely identified by their Matrix user ID. The
user ID is namespaced to the homeserver which allocated the account and
has the form:

    @localpart:domain

The `localpart` of a user ID is an opaque identifier for that user. It
MUST NOT be empty, and MUST contain only the characters `a-z`, `0-9`,
`.`, `_`, `=`, `-`, and `/`.

The `domain` of a user ID is the [server name](#server-name) of the
homeserver which allocated the account.

The length of a user ID, including the `@` sigil and the domain, MUST
NOT exceed 255 characters.

The complete grammar for a legal user ID is:

    user_id = "@" user_id_localpart ":" server_name
    user_id_localpart = 1*user_id_char
    user_id_char = DIGIT
                 / %x61-7A                   ; a-z
                 / "-" / "." / "=" / "_" / "/"

{{% boxes/rationale %}}
A number of factors were considered when defining the allowable
characters for a user ID.

Firstly, we chose to exclude characters outside the basic US-ASCII
character set. User IDs are primarily intended for use as an identifier
at the protocol level, and their use as a human-readable handle is of
secondary benefit. Furthermore, they are useful as a last-resort
differentiator between users with similar display names. Allowing the
full Unicode character set would make very difficult for a human to
distinguish two similar user IDs. The limited character set used has the
advantage that even a user unfamiliar with the Latin alphabet should be
able to distinguish similar user IDs manually, if somewhat laboriously.

We chose to disallow upper-case characters because we do not consider it
valid to have two user IDs which differ only in case: indeed it should
be possible to reach `@user:matrix.org` as `@USER:matrix.org`. However,
user IDs are necessarily used in a number of situations which are
inherently case-sensitive (notably in the `state_key` of `m.room.member`
events). Forbidding upper-case characters (and requiring homeservers to
downcase usernames when creating user IDs for new users) is a relatively
simple way to ensure that `@USER:matrix.org` cannot refer to a different
user to `@user:matrix.org`.

Finally, we decided to restrict the allowable punctuation to a very
basic set to reduce the possibility of conflicts with special characters
in various situations. For example, "\*" is used as a wildcard in some
APIs (notably the filter API), so it cannot be a legal user ID
character.

The length restriction is derived from the limit on the length of the
`sender` key on events; since the user ID appears in every event sent by
the user, it is limited to ensure that the user ID does not dominate
over the actual content of the events.
{{% /boxes/rationale %}}

Matrix user IDs are sometimes informally referred to as MXIDs.

##### Historical User IDs

Older versions of this specification were more tolerant of the
characters permitted in user ID localparts. There are currently active
users whose user IDs do not conform to the permitted character set, and
a number of rooms whose history includes events with a `sender` which
does not conform. In order to handle these rooms successfully, clients
and servers MUST accept user IDs with localparts from the expanded
character set:

    extended_user_id_char = %x21-39 / %x3B-7E  ; all ASCII printing chars except :

##### Mapping from other character sets

In certain circumstances it will be desirable to map from a wider
character set onto the limited character set allowed in a user ID
localpart. Examples include a homeserver creating a user ID for a new
user based on the username passed to `/register`, or a bridge mapping
user ids from another protocol.

Implementations are free to do this mapping however they choose. Since
the user ID is opaque except to the implementation which created it, the
only requirement is that the implementation can perform the mapping
consistently. However, we suggest the following algorithm:

1.  Encode character strings as UTF-8.
2.  Convert the bytes `A-Z` to lower-case.
    -   In the case where a bridge must be able to distinguish two
        different users with ids which differ only by case, escape
        upper-case characters by prefixing with `_` before downcasing.
        For example, `A` becomes `_a`. Escape a real `_` with a second
        `_`.
3.  Encode any remaining bytes outside the allowed character set, as
    well as `=`, as their hexadecimal value, prefixed with `=`. For
    example, `#` becomes `=23`; `á` becomes `=c3=a1`.

{{% boxes/rationale %}}
The suggested mapping is an attempt to preserve human-readability of
simple ASCII identifiers (unlike, for example, base-32), whilst still
allowing representation of *any* character (unlike punycode, which
provides no way to encode ASCII punctuation).
{{% /boxes/rationale %}}

#### Room IDs and Event IDs

A room has exactly one room ID. A room ID has the format:

    !opaque_id:domain

An event has exactly one event ID. The format of an event ID depends
upon the [room version specification](/#room-versions).

The `domain` of a room ID is the [server name](#server-name) of the
homeserver which created the room/event. The domain is used only for
namespacing to avoid the risk of clashes of identifiers between
different homeservers. There is no implication that the room or event in
question is still available at the corresponding homeserver.

Event IDs and Room IDs are case-sensitive. They are not meant to be
human-readable. They are intended to be treated as fully opaque strings
by clients.

#### Room Aliases

A room may have zero or more aliases. A room alias has the format:

    #room_alias:domain

The `domain` of a room alias is the [server name](#server-name) of the
homeserver which created the alias. Other servers may contact this
homeserver to look up the alias.

Room aliases MUST NOT exceed 255 bytes (including the `#` sigil and the
domain).

#### matrix.to navigation

{{% boxes/note %}}
This namespacing is in place pending a `matrix://` (or similar) URI
scheme. This is **not** meant to be interpreted as an available web
service - see below for more details.
{{% /boxes/note %}}

Rooms, users, aliases, and groups may be represented as a "matrix.to"
URI. This URI can be used to reference particular objects in a given
context, such as mentioning a user in a message or linking someone to a
particular point in the room's history (a permalink).

A matrix.to URI has the following format, based upon the specification
defined in RFC 3986:

> <https://matrix.to/#/>&lt;identifier&gt;/&lt;extra
> parameter&gt;?&lt;additional arguments&gt;

The identifier may be a room ID, room alias, user ID, or group ID. The
extra parameter is only used in the case of permalinks where an event ID
is referenced. The matrix.to URI, when referenced, must always start
with `https://matrix.to/#/` followed by the identifier.

The `<additional arguments>` and the preceding question mark are
optional and only apply in certain circumstances, documented below.

Clients should not rely on matrix.to URIs falling back to a web server
if accessed and instead should perform some sort of action within the
client. For example, if the user were to click on a matrix.to URI for a
room alias, the client may open a view for the user to participate in
the room.

The components of the matrix.to URI (`<identifier>` and
`<extra parameter>`) are to be percent-encoded as per RFC 3986.

Examples of matrix.to URIs are:

-   Room alias: `https://matrix.to/#/%23somewhere%3Aexample.org`
-   Room: `https://matrix.to/#/!somewhere%3Aexample.org`
-   Permalink by room:
    `https://matrix.to/#/!somewhere%3Aexample.org/%24event%3Aexample.org`
-   Permalink by room alias:
    `https://matrix.to/#/%23somewhere:example.org/%24event%3Aexample.org`
-   User: `https://matrix.to/#/%40alice%3Aexample.org`

{{% boxes/note %}}
Historically, clients have not produced URIs which are fully encoded.
Clients should try to interpret these cases to the best of their
ability. For example, an unencoded room alias should still work within
the client if possible.
{{% /boxes/note %}}

{{% boxes/note %}}
Clients should be aware that decoding a matrix.to URI may result in
extra slashes appearing due to some [room
versions](/#room-versions). These slashes should normally be
encoded when producing matrix.to URIs, however.
{{% /boxes/note %}}

{{% boxes/note %}}
<!-- TODO: @@TravisR: Make "Spaces" a link when that specification exists -->
In prior versions of this specification, a concept of "groups" were mentioned
to organize rooms. This functionality did not properly get introduced into
the specification and is subsequently replaced with "Spaces". Historical
matrix.to URIs pointing to groups might still exist: they take the form
`https://matrix.to/#/%2Bexample%3Aexample.org` (where the `+` sigil may or
may not be encoded).
{{% /boxes/note %}}

##### Routing

Room IDs are not routable on their own as there is no reliable domain to
send requests to. This is partially mitigated with the addition of a
`via` argument on a matrix.to URI, however the problem of routability is
still present. Clients should do their best to route Room IDs to where
they need to go, however they should also be aware of [issue
\#1579](https://github.com/matrix-org/matrix-doc/issues/1579).

A room (or room permalink) which isn't using a room alias should supply
at least one server using `via` in the `<additional arguments>`, like
so:
`https://matrix.to/!somewhere%3Aexample.org?via=example.org&via=alt.example.org`.
The parameter can be supplied multiple times to specify multiple servers
to try.

The values of `via` are intended to be passed along as the `server_name`
parameters on the Client Server `/join` API.

When generating room links and permalinks, the application should pick
servers which have a high probability of being in the room in the
distant future. How these servers are picked is left as an
implementation detail, however the current recommendation is to pick 3
unique servers based on the following criteria:

-   The first server should be the server of the highest power level
    user in the room, provided they are at least power level 50. If no
    user meets this criterion, pick the most popular server in the room
    (most joined users). The rationale for not picking users with power
    levels under 50 is that they are unlikely to be around into the
    distant future while higher ranking users (and therefore servers)
    are less likely to give up their power and move somewhere else. Most
    rooms in the public federation have a power level 100 user and have
    not deviated from the default structure where power level 50 users
    have moderator-style privileges.
-   The second server should be the next highest server by population,
    or the first highest by population if the first server was based on
    a user's power level. The rationale for picking popular servers is
    that the server is unlikely to be removed as the room naturally
    grows in membership due to that server joining users. The server
    could be refused participation in the future due to server ACLs or
    similar, however the chance of that happening to a server which is
    organically joining the room is unlikely.
-   The third server should be the next highest server by population.
-   Servers which are blocked due to server ACLs should never be chosen.
-   Servers which are IP addresses should never be chosen. Servers which
    use a domain name are less likely to be unroutable in the future
    whereas IP addresses cannot be pointed to a different location and
    therefore higher risk options.
-   All 3 servers should be unique from each other. If the room does not
    have enough users to supply 3 servers, the application should only
    specify the servers it can. For example, a room with only 2 users in
    it would result in maximum 2 `via` parameters.

## 3PID Types

Third Party Identifiers (3PIDs) represent identifiers on other
namespaces that might be associated with a particular person. They
comprise a tuple of `medium` which is a string that identifies the
namespace in which the identifier exists, and an `address`: a string
representing the identifier in that namespace. This must be a canonical
form of the identifier, *i.e.* if multiple strings could represent the
same identifier, only one of these strings must be used in a 3PID
address, in a well-defined manner.

For example, for e-mail, the `medium` is 'email' and the `address` would
be the email address, *e.g.* the string `bob@example.com`. Since domain
resolution is case-insensitive, the email address `bob@Example.com` is
also has the 3PID address of `bob@example.com` (without the capital 'e')
rather than `bob@Example.com`.

The namespaces defined by this specification are listed below. More
namespaces may be defined in future versions of this specification.

### E-Mail

Medium: `email`

Represents E-Mail addresses. The `address` is the raw email address in
`user@domain` form with the domain in lowercase. It must not contain
other text such as real name, angle brackets or a mailto: prefix.

In addition to lowercasing the domain component of an email address,
implementations are expected to lowercase the localpart as described
in [the unicode mapping file](https://www.unicode.org/Public/8.0.0/ucd/CaseFolding.txt)
prior to any processing. For example, `Strauß@Example.com` must be
considered to be `strauss@example.com` while processing the email
address.

### PSTN Phone numbers

Medium: `msisdn`

Represents telephone numbers on the public switched telephone network.
The `address` is the telephone number represented as a MSISDN (Mobile
Station International Subscriber Directory Number) as defined by the
E.164 numbering plan. Note that MSISDNs do not include a leading '+'.

## Security Threat Model

### Denial of Service

The attacker could attempt to prevent delivery of messages to or from
the victim in order to:

-   Disrupt service or marketing campaign of a commercial competitor.
-   Censor a discussion or censor a participant in a discussion.
-   Perform general vandalism.

#### Threat: Resource Exhaustion

An attacker could cause the victim's server to exhaust a particular
resource (e.g. open TCP connections, CPU, memory, disk storage)

#### Threat: Unrecoverable Consistency Violations

An attacker could send messages which created an unrecoverable
"split-brain" state in the cluster such that the victim's servers could
no longer derive a consistent view of the chatroom state.

#### Threat: Bad History

An attacker could convince the victim to accept invalid messages which
the victim would then include in their view of the chatroom history.
Other servers in the chatroom would reject the invalid messages and
potentially reject the victims messages as well since they depended on
the invalid messages.

#### Threat: Block Network Traffic

An attacker could try to firewall traffic between the victim's server
and some or all of the other servers in the chatroom.

#### Threat: High Volume of Messages

An attacker could send large volumes of messages to a chatroom with the
victim making the chatroom unusable.

#### Threat: Banning users without necessary authorisation

An attacker could attempt to ban a user from a chatroom without the
necessary authorisation.

### Spoofing

An attacker could try to send a message claiming to be from the victim
without the victim having sent the message in order to:

-   Impersonate the victim while performing illicit activity.
-   Obtain privileges of the victim.

#### Threat: Altering Message Contents

An attacker could try to alter the contents of an existing message from
the victim.

#### Threat: Fake Message "origin" Field

An attacker could try to send a new message purporting to be from the
victim with a phony "origin" field.

### Spamming

The attacker could try to send a high volume of solicited or unsolicited
messages to the victim in order to:

-   Find victims for scams.
-   Market unwanted products.

#### Threat: Unsolicited Messages

An attacker could try to send messages to victims who do not wish to
receive them.

#### Threat: Abusive Messages

An attacker could send abusive or threatening messages to the victim

### Spying

The attacker could try to access message contents or metadata for
messages sent by the victim or to the victim that were not intended to
reach the attacker in order to:

-   Gain sensitive personal or commercial information.
-   Impersonate the victim using credentials contained in the messages.
    (e.g. password reset messages)
-   Discover who the victim was talking to and when.

#### Threat: Disclosure during Transmission

An attacker could try to expose the message contents or metadata during
transmission between the servers.

#### Threat: Disclosure to Servers Outside Chatroom

An attacker could try to convince servers within a chatroom to send
messages to a server it controls that was not authorised to be within
the chatroom.

#### Threat: Disclosure to Servers Within Chatroom

An attacker could take control of a server within a chatroom to expose
message contents or metadata for messages in that room.

## Cryptographic Test Vectors

To assist in the development of compatible implementations, the
following test values may be useful for verifying the cryptographic
event signing code.

### Signing Key

The following test vectors all use the 32-byte value given by the
following Base64-encoded string as the seed for generating the `ed25519`
signing key:

    SIGNING_KEY_SEED = decode_base64(
        "YJDBA9Xnr2sVqXD9Vj7XVUnmFZcZrlw8Md7kMW+3XA1"
    )

In each case, the server name and key ID are as follows:

    SERVER_NAME = "domain"

    KEY_ID = "ed25519:1"

### JSON Signing

Given an empty JSON object:

```json
{}
```

The JSON signing algorithm should emit the following signed data:

```json
{
    "signatures": {
        "domain": {
            "ed25519:1": "K8280/U9SSy9IVtjBuVeLr+HpOB4BQFWbg+UZaADMtTdGYI7Geitb76LTrr5QV/7Xg4ahLwYGYZzuHGZKM5ZAQ"
        }
    }
}
```

Given the following JSON object with data values in it:

```json
{
    "one": 1,
    "two": "Two"
}
```

The JSON signing algorithm should emit the following signed JSON:

```json
{
    "one": 1,
    "signatures": {
        "domain": {
            "ed25519:1": "KqmLSbO39/Bzb0QIYE82zqLwsA+PDzYIpIRA2sRQ4sL53+sN6/fpNSoqE7BP7vBZhG6kYdD13EIMJpvhJI+6Bw"
        }
    },
    "two": "Two"
}
```

### Event Signing

Given the following minimally-sized event:

```json
{
    "room_id": "!x:domain",
    "sender": "@a:domain",
    "origin": "domain",
    "origin_server_ts": 1000000,
    "signatures": {},
    "hashes": {},
    "type": "X",
    "content": {},
    "prev_events": [],
    "auth_events": [],
    "depth": 3,
    "unsigned": {
        "age_ts": 1000000
    }
}
```

The event signing algorithm should emit the following signed event:

```json
{
    "auth_events": [],
    "content": {},
    "depth": 3,
    "hashes": {
        "sha256": "5jM4wQpv6lnBo7CLIghJuHdW+s2CMBJPUOGOC89ncos"
    },
    "origin": "domain",
    "origin_server_ts": 1000000,
    "prev_events": [],
    "room_id": "!x:domain",
    "sender": "@a:domain",
    "signatures": {
        "domain": {
            "ed25519:1": "KxwGjPSDEtvnFgU00fwFz+l6d2pJM6XBIaMEn81SXPTRl16AqLAYqfIReFGZlHi5KLjAWbOoMszkwsQma+lYAg"
        }
    },
    "type": "X",
    "unsigned": {
        "age_ts": 1000000
    }
}
```

Given the following event containing redactable content:

```json
{
    "content": {
        "body": "Here is the message content"
    },
    "event_id": "$0:domain",
    "origin": "domain",
    "origin_server_ts": 1000000,
    "type": "m.room.message",
    "room_id": "!r:domain",
    "sender": "@u:domain",
    "signatures": {},
    "unsigned": {
        "age_ts": 1000000
    }
}
```

The event signing algorithm should emit the following signed event:

```json
{
    "content": {
        "body": "Here is the message content"
    },
    "event_id": "$0:domain",
    "hashes": {
        "sha256": "onLKD1bGljeBWQhWZ1kaP9SorVmRQNdN5aM2JYU2n/g"
    },
    "origin": "domain",
    "origin_server_ts": 1000000,
    "type": "m.room.message",
    "room_id": "!r:domain",
    "sender": "@u:domain",
    "signatures": {
        "domain": {
            "ed25519:1": "Wm+VzmOUOz08Ds+0NTWb1d4CZrVsJSikkeRxh6aCcUwu6pNC78FunoD7KNWzqFn241eYHYMGCA5McEiVPdhzBA"
        }
    },
    "unsigned": {
        "age_ts": 1000000
    }
}
```
