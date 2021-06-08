# MSC2872: Move the widget `title` to the root

Currently widgets can support a "title" (subtext alongside the name) per the
[draft specification](https://github.com/matrix-org/matrix-doc/pull/2764) for widgets. However, due
to legacy reasons this field is in the `data` object rather than at the top level alongside `name`.

## Proposal

For cleanliness of the API surface, it is proposed to move `title` to the top level of the widget
definition alongside the existing `name` field. For backwards compatibility, it is suggested that
clients use the legacy `data.title` if a top level field is not present. The `data.title` field
is deprecated/removed under this MSC.

## Potential issues

No relevant issues - this is API consistency.

## Alternatives

We could just leave it, or move things to the `data` in general. This isn't really needed given
widgets can't touch their client-side aesthetics (name, title, avatar), and the information isn't
typically needed for the widget to function (ie: widgets don't use a `$title` template variable).

## Security considerations

None relevant.

## Unstable prefix

Implementations can use `org.matrix.msc2872.title` at the top level instead for now.
