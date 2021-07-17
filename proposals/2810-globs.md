# MSC2810: Consistent globs specification

A [glob](https://en.wikipedia.org/wiki/Glob_(programming)) is a simplified matching system which is
compatible with several platforms and ideas. Unlike regular expressions, globs are human readable
for the most part and have an easier set of rules to process.

Matrix already uses globs in server ACLs, push rules, and policy events. This proposal aims to
formalize the glob specification between these three areas (which is already consistent) and for
future uses of globs within Matrix.

## Proposal

Matrix is to only support two characters for globs, removing a lot of the parsing complexity
described by the article linked above. The characters are:

* `*` - an asterisk to denote zero or more character matches.
* `?` - a question mark to denote one or more character matches.
* `\` - a backslash escapes the character that follows to be treated as a literal. If the character
  that follows has no specific meaning, the escape character is treated as a literal itself.

Glob characters can appear anywhere in a sequence, or may not be present at all.

These definitions are the same definitions used today by ACLs, push rules, and policy events
as well as the article linked above.

Further rules, such as square bracket matching, are excluded for the time being. A future MSC
can introduce them as needed when an appropriate use case arises.

MSCs making use of globs should use this standard once supported by specification.

Examples:

* `alice` - no globs present, matches text "alice" exactly.
* `alice*` - suffixed with an asterisk, matches "alice" as well as "alicebob".
* `alice?` - suffixed with a question mark, matches "alicebob" but not "alice".
* `alice\?` - escaped character, matches exactly "alice?" like in the first example.
* `\alice` - unrepresented escape sequence, matches exactly "\alice".

## Potential issues

Not supporting square brackets from day one might cause issues for future extensions to the spec,
potentially requiring room versions to ensure things like server ACLs are accurately applied by
all parties. This is seen as a necessary limitation by this proposal due to existing glob usage
in Matrix already being limited to the above rules.

## Alternatives

Each new usage of a glob could define its own specification, leading to confusion among implementations
and excessive specification needing to be written. By using a common baseline, we are more easily able
to point to a single section within the specification and implementations can rely upon a single library
for parsing Matrix globs. Defining a common approach already has prior art through signatures in Matrix.

## Security considerations

Implementations should be careful to handle escape sequences to avoid mishandling globs. Because globs
are used for security purposes (ACLs, policy events, etc) it is important that the implementation be
well tested prior to usage.

Implementations may wish to optimize lookups to avoid excessive resource usage. For example, `?*` can
be shortened to just `?`. Optimized token searching can also be employed to avoid having to read a
majority of the test string.

Implementations which convert globs to regular expressions should be wary of user input potentially
causing dangerous, unsafe, or badly performing regular expressions.

## Unstable prefix

None relevant - this MSC formalizes an existing functionality within the spec.
