# MSC 2379: Add /versions endpoint to Appservice API. 

Bridges do not have a way to specify what version of the spec they support. This means that if the path
of any of the appservice endpoints were to change in the spec, homeservers would not be able to
intelligently discover the paths that a bridge supports.

## Proposal

A new endpoint is required, which is `/_matrix/app/versions`. This is nearly identical to the
[C-S API](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-versions) endpoint
but lacks a `unstable_features` key, and is hosted by the appservice rather than the homeserver.

All bridges MUST implement this endpoint and specify which version(s) of the `AS` API they support. 
The homeserver MUST send requests to the endpoints specified by that version of the AS spec.

## Potential issues

None

## Alternatives

This proposal previously used the `registration` file as a way to specify the supported version, but
this was dropped as it was hard for the bridge to be authoritive over what version it supports. Typically
the registration format is generated once by the bridge and then handled by the homeserver. If a bridge were
to update and require a new version of the AS API, the registration data would need to be updated/regenerated.

## Security considerations

None
