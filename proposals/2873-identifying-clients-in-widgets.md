# MSC2873: Identifying clients and user settings in widgets

Some widgets may wish to enable functionality depending on the client they are being presented
within, or match the client's theme as best as possible, or even localize the widget itself to
match the user's preference. None of this is currently possible for a widget to achieve in a
stable way.

## Proposal

Some new template variables are added to the available options for a widget URL:

* `matrix_client_id` - A [MSC2758](https://github.com/matrix-org/matrix-doc/pull/2758) identifier
  for the client which is rendering the widget.
* `matrix_client_theme` - The stringified name for the user's current theme as decided upon by
  the client.
* `matrix_client_language` - The ISO 639-1 alpha-2 code for the user's current language.

For example, in Element Web the `matrix_client_id` might be `io.element.web` and the
`matrix_client_theme` could be `light`. In the case of another example client, the client ID might
be `org.example.ios` with a theme of `org.example.dark` - the theme name can be any string so long
as it is relevant to the client ID (such as `light` in the case of Element). No standardized naming
is proposed here for themes.

To help with theme changes and supporting custom themes in some clients, a new `to_widget` action
is proposed:

```json5
{
  "api": "toWidget",
  "requestId": "AAABBB",
  "widgetId": "CCCDDD",
  "action": "theme_change",
  "data": {
    // client-specific theme information
  }
}
```

The `theme_change` request should be acknowledged with an empty response body by the widget. The
widget can then use the information to update its own theme, if desired. The `data` of the request
is entirely dependent on the client's theme information as it doesn't make sense at this time to
standardize a theme format for all clients.

For Element Web, this may look like:

```json
{
  "api": "toWidget",
  "requestId": "AAABBB",
  "widgetId": "CCCDDD",
  "action": "theme_change",
  "data": {
    "name": "Selenized dark theme",
    "src": "https://raw.githubusercontent.com/aaronraimist/element-themes/master/Selenized/Selenized%20Dark/Selenized%20Dark.json",
    "author": "@dylhack:dhdf.dev",
    "is_dark": true,
    "colors": {
        "accent-color": "#41c7b9",
        "primary-color": "#4695f7",
        "warning-color": "#fa5750",
        "sidebar-color": "#103c48",
        "roomlist-background-color": "#184956",
        "roomlist-text-color": "#dbb32d",
        "roomlist-text-secondary-color": "#FFFFFF",
        "roomlist-highlights-color": "#2d5b69",
        "roomlist-separator-color": "#2d5b69",
        "timeline-background-color": "#2d5b69",
        "timeline-text-color": "#FFFFFF",
        "timeline-text-secondary-color": "#72898f",
        "timeline-highlights-color": "#184956",
        "reaction-row-button-selected-bg-color": "#4695f7"
    }
  }
}
```

Whenever a client changes its theme with a widget open, it should send this `theme_change` request.
Because the client's first availbility to send this request would be after the capabilities
exchange, which may take a while, the client may wish to consider setting slightly more coarse theme
names in the URL variable so the widget can render the appropriate theme as soon as possible (eg:
in Element Web, if a custom dark theme is used it might still say "dark" instead of "Selenized dark
theme"). The URL variable exists purely for the purposes of letting the widget load the right theme
while waiting for a `theme_change` request (which might happen immediately after the capabilities
exchange to help the widget change into the right colour scheme).

To further assist with the changes of language, the following action is defined. Like with the theme
information, the URL variable is useful for while the widget is loading and followed by an update
later on if the language were to change.

```json
{
  "api": "toWidget",
  "requestId": "AAABBB",
  "widgetId": "CCCDDD",
  "action": "language_change",
  "data": {
    "lang": "fr"
  }
}
```

The `lang` variable is an ISO 639-1 alpha-2 code. The request is acknowledged with an empty response
by the widget.

## Potential issues

The lack of standardization could lead to widgets having massive libraries to support an infinite
combination of potential formats for a theme, though in practice this is unlikely. Widgets are more
likely to support a general structure for most clients with some more enhanced themeing for others.

For example, a widget designed for FluffyChat (if it supported widgets) might care a lot more about
FluffyChat's current theme than, also for example, Element Web's. A widget designed for both would
likely listen for both client's themes more closely.

## Alternatives

We could standardize the theme format, however custom themes are too new to the ecosystem to create
a formal, consistent, standard at the time of writing this MSC. A future MSC may wish to standardize
a format for what a (custom) theme looks like.

## Security considerations

By identifying the client explicitly, widgets could potentially be made aware of when a vulnerable
client is being used and attempt to exploit the client. This would likely happen regardless of a
direct indication of what the client is, though the check does become easier for the widget if it
is told exactly which client is rendering it.

In a similar vein, clients could lie about their client ID or provide changing/false details for
the theme. This is considered a self-inflicted problem for the client to deal with and not
recommended by this proposal. Widgets should be validating all data anyways, and therefore should
be anticipating that the client ID and theme information might mismatch what that client's spec
says.

## Unstable prefix

Until in the spec, implementations can use `org.matrix.msc2873.client_id` and
`org.matrix.msc2873.client_theme` in place of the proposed variables. Implementations should also
only use the `theme_change` action if the widget supports `org.matrix.msc2873` in its versions.
