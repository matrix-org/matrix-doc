# MSC2644: `matrix.to` URI syntax v2

`matrix.to` URIs are used frequently to link to Matrix things (events, rooms,
users, groups) in the ecosystem today. By adjusting and extending them a bit
further, both clients and the interstitial screens hosted at `matrix.to` can
give the user more context and a better experience.

While `matrix.to` is the initial use case for much of this proposal, it is also
an opportunity to revise, clean up, and extend client handling of these links as
well, as the revise format below can carry additional details in shared links,
which should be broadly useful across the ecosystem.

## Proposal

In an attempt to make it easier for the reader to review, this proposal first
summarises the current syntax, then describes the revised syntax, and finally
summaries the changes proposed.

### Current syntax

This summarises the [currently specified matrix.to URI
format](https://matrix.org/docs/spec/appendices#matrix-to-navigation) as an aid
to the reader.

A matrix.to URI has the following format, based upon the specification defined
in RFC 3986:

```
https://matrix.to/#/<identifier>/<extra parameter>?<additional arguments>
```

The `identifier` (required) may be a:

| type | value |
| ---- | ----- |
| room ID | `!somewhere:example.org` |
| room alias | `#somewhere:example.org` |
| user ID | `@alice:example.org` |
| group ID | `+example:example.org` |

The `extra parameter` (optional) is only used in the case of permalinks where an
event ID is referenced:

| type | value |
| ---- | ----- |
| event ID (v1) | `$event:example.org` |
| event ID (v3) | `$Woq2vwLy8mNukf7e8oz61GxT5gpMmr/asNojhb56+wU` |
| event ID (v4) | `$Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU` |

The ``<additional arguments>`` and the preceding question mark are optional and
only apply in certain circumstances:

* `via=<server>`
  * One or more servers [should be
    specified](https://matrix.org/docs/spec/appendices#routing) in the format
    `example.org` when linking to a room (including a permalink to an event in a
    room) since room IDs and event IDs are not currently routable

If multiple ``<additional arguments>`` are present, they should be treated as
query params following RFC 3986 (even though they are in the fragment):
`https://matrix.to/#/!somewhere:example.org?via=example.org&via=alt.example.org`

While the spec says the components of the matrix.to URI (``<identifier>`` and
``<extra parameter>``) are to be percent-encoded as per RFC 3986, clients often
do not encode, and it is more human-friendly to leave them unencoded, so we
ignore the encoded version here.

### Revised syntax

A matrix.to URI has the following format, based upon the specification defined
in RFC 3986:

```
https://matrix.to/#/<identifier>/<extra parameter>?<additional arguments>
```

The `identifier` (required) may be a:

| type | value |
| ---- | ----- |
| event ID (v3) | `$Woq2vwLy8mNukf7e8oz61GxT5gpMmr/asNojhb56+wU` |
| event ID (v4) | `$Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU` |
| room ID | `!somewhere:example.org` |
| room alias | `#somewhere:example.org` |
| user ID | `@alice:example.org` |
| group ID | `+example:example.org` |

Matrix.to URIs using a event ID alone (without a room ID) should never be
generated when the global uniqueness of the event ID cannot be guaranteed, such
as in the case of v1 and v2 rooms.

The `extra parameter` (optional) now only exists for compatibility with existing
v1 links. It can be used when `identifier` is a room ID or room alias as a part
of a permalink that references a specific event, as shown in the table below.
Going forward, this should be considered deprecated, and clients should place
only the event ID in the `identifier` position for new links.

| type | value |
| ---- | ----- |
| event ID (v1) | `$event:example.org` |
| event ID (v3) | `$Woq2vwLy8mNukf7e8oz61GxT5gpMmr/asNojhb56+wU` |
| event ID (v4) | `$Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU` |

Since clients currently cannot find a room from the event ID alone, a revived
client-server API (`GET /_matrix/client/r0/events/{eventId}`) is proposed by
[MSC2695](https://github.com/matrix-org/matrix-doc/pull/2695) to support the new
URI format when used with an event ID without a room ID.

The ``<additional arguments>`` and the preceding question mark are optional and
only apply in certain circumstances:

* `via=<server>`
  * One or more servers [should be
    specified](https://matrix.org/docs/spec/appendices#routing) in the format
    `example.org` when linking to a room or an event since room IDs and event
    IDs are not currently routable on their own
* `client=<client URL>`
  * This parameter allows clients to indicate which client shared the URI
  * Clients should identify themselves via a schemeless `https` URL pointing
      to a download / install page, such as:
    * `foo.com`
    * `apps.apple.com/app/foo/id1234`
    * `play.google.com/store/apps/details?id=com.foo.client`
  * Since this is a URL embedded inside the `matrix.to` URI, the characters from
    the RFC 3986 `gen-delims` set as well as `&` and `=` should be
    percent-encoded: `:/?#[]@&=`.
* `federated=false`
  * This parameter allows indicating whether a room exists on a federating
    server (assumed to be the default), or if the client must connect via the
    server identified by the room ID or event ID (when set to `false`)
* `sharer=<MXID>`
  * This parameter allows indicating the MXID of the account which created the
    link, so that clients and interstitial UIs can display more context to the
    user
  * As an example, clients and interstitial UIs could use this to query profile
    data for the sharer's account and display the sharer's avatar and display
    name

If multiple ``<additional arguments>`` are present, they should be treated as
query params following RFC 3986 (even though they are in the fragment):
`https://matrix.to/#/!somewhere:example.org?via=example.org&via=alt.example.org`

This revised syntax does not attempt to suggest percent-encoding all of the URI
components, as it's generally more human-friendly to leave them unencoded.
Certain arguments may still need to be encoded (such as the `client` URL), and
those are marked as such where they are defined.

Examples of matrix.to URIs using the revised syntax are:

* Room alias: ``https://matrix.to/#/#somewhere:example.org``
* Room alias with client and sharer:
  ``https://matrix.to/#/#somewhere:example.org?client=example.org%2Freleases%3Fdownload=latest&sharer=@alice:example.org``
* Room: ``https://matrix.to/#/!somewhere:example.org?via=example.org&via=alt.example.org``
* Event permalink: ``https://matrix.to/#/$Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU?via=example.org&via=alt.example.org``
* User: ``https://matrix.to/#/@alice:example.org``
* Group: ``https://matrix.to/#/+example:example.org``

### Summary of changes

* When permalinking to a specific event, the room ID is no longer required and
  event IDs are now permitted in the identifier position, so URIs like
  `https://matrix.to/#/$Woq2vwLy8mNukf7e8oz61GxT5gpMmr_asNojhb56-wU` are now
  acceptable (though would need to include `via` params since event IDs are not
  routable alone)
* Clients should prefer creating URIs with room aliases instead of room IDs
  where possible, as it's more human-friendly and `via` params are not needed
* A new, optional `client` parameter allows clients to indicate
  which client shared the URI
* A new, optional `federated` parameter allows indicating whether a room exists
  on a federating server (assumed to be the default), or if it's only
  reachable through/at a certain server
* A new, optional `sharer` parameter allows indicating the MXID of the account
  which created the link, in case that is meaningful to include

## Potential issues

This proposal seeks to extend the existing `matrix.to` syntax, but there is also
an open proposal for a [Matrix URI
scheme](https://github.com/matrix-org/matrix-doc/pull/2312). If this proposal
moves forward, the Matrix URI scheme would likely need to be reworked to
accommodate the additions here.

The new `client` parameter implies there are potentially many identifiers that
might be passed that point to a given client. If there are use cases which rely
on a static mapping of client identifier to client name, logo, etc. for some
reason, then that could become a burden to maintain over time. The flexibility
of accepting any URL as an identifier (and thus avoiding the need to register a
client in a centralised place) seems preferable and hopefully outweighs this
concern.

## Alternatives

Instead of extending `matrix.to`, these embellishments could wait for and
extend the future [Matrix URI
scheme](https://github.com/matrix-org/matrix-doc/pull/2312). This proposal
attempts to be pragmatic and tries to extend what is already in use today,
rather than blocking on a new scheme.

## Security considerations

The new `sharer` parameter is not authenticated, so you could make it appear as
if someone had shared something they did not. It is currently assumed that this
is a minor concern.

## Unstable prefix

There's no concept of stability for the matrix.to URI syntax, so no prefix is
used here. Since everything proposed here is purely additive, there should not
be a compatibility issues. At worst, the new pieces are ignored.
