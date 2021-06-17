# MSC2813: Handling invalid Widget API requests

Currently the widget specification (as of writing, https://github.com/matrix-org/matrix-doc/pull/2764
is the best resource for this) does not specify what clients or widgets should do when they see invalid
or inappropriate requests. This proposal fixes that.

## Proposal

Using the existing error response structure, clients and widgets are expected to return errors
to the other end in the following cases:

* Unsupported or unhandled requests (eg: unknown `action`, not applicable to the widget at hand, etc).
* Requests not matching their schemas (fields being arrays when they should be strings, etc).
* Out of sequence requests (sending stickers before capabilities, for example).

In addition, for the purposes of a "valid schema", when a field is optional with respect to widget API
requests, `null`, `undefined`, and not present are acceptable. For example, all of these JSON objects
are valid (assuming the field is flagged as optional):

* `{"field": null}`
* `{"field": undefined}`
* `{}`

When null, undefined, or lack of presence is in play the default behaviour defined by the field applies.
When the type is invalid by falsey in typical languages (empty strings, arrays, etc) the field is
considered provided as-is, which may result in schema violations that are handled per above.

The widgets specification already defines programming faults (unexpected exceptions) as needing error
responses and are thus not mentioned in this proposal in detail.

## Potential issues

Arguablly there are more issues when we don't define strict behaviour for errors.

## Alternatives

The alternatives would be to do nothing or to work through a different behaviour. Doing nothing is subpar,
and working through different behaviour is the goal of an MSC.

## Security considerations

By specifically validating schemas implementations will be less vulnerable to various attacks.

## Unstable prefix

None relevant - errors are already an expected part of the widget API and implementations should be able
to handle them.
