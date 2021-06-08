# Proposal for an /info endpoint on the CS API

## Problem

We have many different APIs for querying server capabilities and configuration:

 * `/_matrix/client/versions` tells you what CS API versions your server supports (unauthed)
 * `/_matrix/media/r0/config` tells you the capabilities of your media repository (unauthed)
 * `/_matrix/client/r0/capabilities` tells you whether your server supports various optional capabilities (but is authed)
 * `/_matrix/federation/v1/capabilities` (MSC2127) is a proposal to tell you when you can upgrade rooms or not (authed as server)
 * MSC2233 as a rejected un-authed capabilities endpoint
 * System Alerts (as a way of sharing server updates with users)
 * GDPR flows (as a way of sharing server legalese with users)

 None of these solve
 [SYN-1](https://github.com/matrix-org/synapse/issues/1199) - the very first
 ever Matrix bug, which wanted a standard way for Servers to publish
 structured data to unauthenticated clients for use in branding and to help
 users know that they're trying to log into the right server, and see useful
 information 'from the outside' about that server.

## Proposal

Rather than creating yet another unauthenticated capabilities/config endpoint,
we rename `/versions` into `/info` and support adding additional namespaced
fields into the returned object to broadcast some of this useful data.

Proposed fields (alongside the existing `versions` and `unstable_features` fields) are:

```json
{
	"m.brand.server_name": "Matthew's Server",
	"m.brand.server_info": "Where all the cool kids hang out",
	"m.motd": "This server will be upgraded on Oct 1st",
	"m.server_admin": "@admin:example.com",
	"m.brand.theme": {
		"im.vector.brand.client_name": "Matthew's Riot",
		"m.proportional_fontface": "Nunito Sans",
		"m.proportional_fontfile": "mxc://example.com/qhasdjjvkd",
		"m.fixed_fontface": "Inconsolata",
		"m.fixed_fontfile": "mxc://example.com/zhivjkwdhs",
	},
	"m.brand.theme.dark": {
		"m.brand.logo": "mxc://example.com/1234eruwfgsvhgd",
		"m.primary_color": "#aa0000",
		"m.secondary_color": "#880000",
		"m.accent_color": "#ff0000",
		"m.primary_bgcolor": "#000000",
		"m.secondary_bgcolor": "#444444",
	},
	"m.brand.theme.light": {
		"m.brand.logo": "mxc://example.com/csldvhuwedqwc",
		"m.primary_color": "#aa0000",
		"m.secondary_color": "#880000",
		"m.accent_color": "#ff0000",
		"m.primary_bgcolor": "#ffffff",
		"m.secondary_bgcolor": "#cccccc",
	}
}
```

## Alternatives

We could put this data into a peekable room instead (particularly so we then get sync updates for free).
This could then instead be:

`m.server_info_room: "!sdviuhkjwehiouacs:example.com"`

...and we can then go wild with state events for branding and other info.
We could then also inherit i18n support for events from the extensible events spec.

However, this is slightly harder for the client to achieve; first it has to call `/info` to get
the room ID, and then `/room/$room_id/state` to actually peek in and grab the server branding info.

This is probably a more elegant solution tbh; thoughts welcome?
