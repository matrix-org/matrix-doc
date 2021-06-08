# MSC2398: Proposal to allow mxc:// in the `a` tag within messages

Currently message events (m.room.message) can contain formatted data
in its formatted_body field, if the format of the message is
org.matrix.custom.html. In this subset of HTML `img` tags are permitted
if they refer to media repository contents with the mxc schema and
clients are able to resolve these URIs to (ie.) HTTPs to retrieve the
actual contents.

However, the spec currently forbids `a` tags from receiving the same
treatment. These links could be useful for example for systems that
upload PDF files to the media storage and then produce messages
linking to such files.

## Proposal

The spec for `a` tags says:

-`a`:
  `name`, `target`, `href` (provided the value is not relative and has a scheme
  matching one of: `https`, `http`, `ftp`, `mailto`, `magnet`)

Clients would be able to handle the mxc schema here in the exact same
way they handle `img` tags. Thus the proposal is to modify that fragment
to say:

-`a`:
  `name`, `target`, `href` (provided the value is not relative and has a scheme
  matching one of: `https`, `http`, `ftp`, `mailto`, `magnet`, or `mxc`
  for `Matrix Content (MXC) URI`)

## Potential issues ##

As far as I see, this is quite a benign change.

The only problem I see (in addition to possible problems already
present in `img` tags) is that current clients may not be able to handle
mxc tags in this position; thus such clients would not be able to
retrieve resources linked this way. Some clients may already
accidentally support this, though, due to consistent handling of URIs.

## Security considerations ##

There is some potential for security issues in hosting HTML in general
in the matrix media repository, but using MXC schema does not affect
much the scope of such attacks as such URIs can already be constructed
with current support - unless protections for such attacks are
fundamentally based on the URI format.

## Alternatives

The alternative to using `mxc://` would be to construct direct
relative links via `/download` (though relative links are also
prohibited by the current spec). Using the `mxc://` scheme seems
cleaner, though.
