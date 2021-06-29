# MSC3008: Scoped access for widgets

Widgets are getting a lot of functionality proposed to them through other MSCs such as
[MSC2876](https://github.com/matrix-org/matrix-doc/pull/2876) and [MSC2762](https://github.com/matrix-org/matrix-doc/pull/2762)
(relating to sending/receiving events). Though this functionality is useful, it is questionable to
further let widgets develop on the postmessage API given it is difficult (or impossible) to interact
with the widget in this way for some clients.

This proposal explores an option where trivial information relating to the room state (and other
similar resources) is provided to the widget rather than the widget querying for access over postmessage.

## Proposal

Using [MSC2967 - API scopes](https://github.com/matrix-org/matrix-doc/pull/2967),
[MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964), and
[issue 2889](https://github.com/matrix-org/matrix-doc/issues/2889) as guiding lights, we'd append scope
information to the standardized widget definition for a widget to stamp an access token for. The client
should prompt the user to confirm the scopes requested prior to rendering the widget. The widget should
be capable of receiving less permissions than expected (due to partially-granted scopes, etc).

The added `scopes` array would look something like this on a widget:

```json5
{
  "type": "m.custom",
  "url": "http://localhost:8082#?widgetId=$matrix_widget_id&accessToken=$matrix_access_token",
  "name": "Widget Debugger",
  "avatar_url": "mxc://t2bot.io/c977fc5396241194e426e6eb9da64f025f813f1b",
  "data": {
    "title": "Widget testing"
  },
  "creatorUserId": "@travis:localhost",
  "id": "debugger_test",

  // This is the only added field. We put it under "auth" to denote possible future extensions to
  // authentication/authorization for widgets.
  "auth": {
    "scopes": [
      // Exact scopes TBD
      "urn:matrix:api:*:read",
    ]
  }
}
```

The `$matrix_access_token` template variable introduced by this proposal would be a stringified JSON object,
encoded as appropriate for placement in the URL. For reference, this is the expected format for an "access
token":

```json
{
  "access_token": "2YotnFZFEjr1zCsicMWpAA",
  "token_type": "Bearer",
  "expires_in": 299,
  "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
  "scope": "openid urn:matrix:api:*:read",
  "id_token": "..."
}
```

The widget would receive a client-server URL via a `$matrix_hs_url` template parameter using the same encoding
technique.

The widget would be responsible for renewing the access token, and the client should never re-use access tokens
even if the scope is the same - the client should always mint a new token for each render.

This MSC is not intended to list the available scopes (that is a decision for the client/user), nor does this
MSC define what scopes would look like for the functionality covered by MSCs like the send/receive events MSCs.

This would effectively obsolete the following MSCs:

* [MSC2876 - Read events](https://github.com/matrix-org/matrix-doc/pull/2876)
* [MSC2762 - Send/receive events](https://github.com/matrix-org/matrix-doc/pull/2762)
* [MSC1960 - OIDC Exchange](https://github.com/matrix-org/matrix-doc/pull/1960)

## Potential issues

The transfer and encoding of the access token via the query string is questionable, though it does allow
for quick transport of the information to the widget without relying on postmessage. It further simplifies
the widget's operation as it can always know which user is using the widget without needing an explicit
prompt. Alternatives for encoding, transport, etc are possible.

## Security considerations

As mentioned, putting the token information into the URL is a bit questionable. This could potentially end
up in browser history, clipboards, etc and be disclosed through those methods. However, seeing as they are
temporary (short-lived) tokens it may not be as realistic as an attack front. This would be dependent on
server support.

## Unstable prefix

The `auth` object gets declared as `org.matrix.msc3008.auth` while this MSC is not considered stable. When
that auth object is present, the client can replace `$org.matrix.msc3008.access_token` and `$org.matrix.msc3008.hs_url`
(in place of `$matrix_access_token` and `$matrix_hs_url`) in the widget's template URL.

The remainder of the unstable prefixes are covered by the other relevant MSCs.
