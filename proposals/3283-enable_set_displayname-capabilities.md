# MSC3283: Expose enable_set_displayname in capabilities response 


Some home servers like Synapse can be configured to enable_set_displayname: false. To enable clients to handle that gracefully in the UI this setting should be exposed.

## Proposal

The `/_matrix/client/r0/capabilities` endpoint should be decorated to provide more information on capabilities.
```javascript
{
  "capabilities": {
    "m.set_displayname": { "enabled": false },
    "m.room_versions": {...},
  }
}
```
As part of this MSC, a capability will be added that exposes the server setting:
`m.enable_set_displayname`

## Client recommendations
When presenting profile settings, clients should use capabilities in order to display the correct UI.
If capability is not present the default is true.

## Unstable prefix
Implementations won't actually be able to use m.enable_set_displayname until the MSC has finished the Final Comment Period. While the MSC is in review, implementations can use an unstable prefix (im.vector.enable_set_displayname) instead.
