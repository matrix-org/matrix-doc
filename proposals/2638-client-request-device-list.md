# MSC2638: Ability for clients to request homeservers to resync device lists

With the recent roll out of cross-signing,
[some](https://github.com/matrix-org/synapse/issues/7418)
[bugs](https://github.com/matrix-org/synapse/issues/7504) in Synapse were
reported around the way it was handling failures when processing device list
updates started hitting users, causing local copies of remote device lists to
grow stale.

Remote device lists growing stale can happen as soon as a homeserver
implementation implements processing of device list updates improperly, or
without the proper retry mechanisms. It can also happen if a homeserver was down
for enough time to miss out on device list updates.

The main consequence of this situation is rendering it impossible for impacted
users to use cross-signing/end-to-end encryption for some remote devices, or
even to use it at all.

When fixing this issue, it is currently quite difficult for a homeserver to
figure out which users it should resync the device lists of. However, it is much
easier for clients to see if a device list is likely out of date (e.g. if it has
cross-signing keys but no signatures), and almost trivial for users to do so
(e.g. if someone tells me "I've enabled cross-signing" but I can't see their
cross-signing keys, then I know something has gone wrong).

In the current situation, the best answer we can give to a user seeing stale
device lists is to ask their server admin to get their instance to somehow (the
details on how to do it depend on the implementation) resync the device list(s)
for the impacted user(s), which isn't an acceptable solution.

For clarity, "resync" here means for a homeserver to ask the latest version of a
user's device list to their homeserver, using the [`GET
/_matrix/federation/v1/user/devices/{userId}`](https://matrix.org/docs/spec/server_server/latest#get-matrix-federation-v1-user-devices-userid)
federation endpoint. "device list update" here describes both a
`m.device_list_update` EDU and a `m.signing_key_update` one.

The proposal described here fixes this issue by adding a new endpoint to the
client-server API, allowing clients to request homeservers to resync device
lists. Clients could then either expose a button a user can use when necessary,
or call this endpoint on specific actions, or both.

## Proposal

This proposal adds the following authenticated endpoint to the client-server API:

### `POST /_matrix/client/r0/user/{userId}/devices/refresh`

In this request, `{userId}` is the full Matrix ID of the user to retrieve the
device list for.

The homeserver responds to a request to this endpoint with a 202 Accepted
response code and an empty body (`{}`).

Upon request to this client-side endpoint, the homeserver would send a request
to [`GET
/_matrix/federation/v1/user/devices/{userId}`](https://matrix.org/docs/spec/server_server/latest#get-matrix-federation-v1-user-devices-userid)
on the target user's homeserver to retrieve the device list.

If the request to the aforementioned federation endpoint succeeds (i.e. the
destination responds with a 200 response code and a device list for the target
user), then the homeserver would include the updated device list in sync
responses in order to relay it to clients.

If the request to the aforementioned federation endpoint fails (i.e. the
destination responds with a non-200 response code or times out), then the
homeserver should relay this error to clients, but should also schedule retries
for this request in case the destination starts working again. In case one of
these retries succeeds (i.e. the destination responds with a 200 response code
and a device list for the target user), the homeserver would include the updated
device list in sync responses.

Clients can then make requests to this endpoint, either upon an explicit
request from the user (e.g. clicking a button) or while performing other actions
(e.g. creating an encrypted 1:1 chat, processing an invite in a group chat,
sending a verification request, etc.).

XXX: I'm unsure whether the spec should be mandating when a client uses this
endpoint or whether this is left as an implementation detail.


## Alternatives

An alternative to this proposal is to let homeservers figure out when a good
time to resync a device list is. However, it can be difficult for it to do so,
especially as it can't see some of the actions a resync would be most useful for
(e.g. sending a verification request, which are encrypted in encrypted rooms).
It therefore makes more sense to do this on the client-side, and it also adds
the ability for the user to figure out when a device list needs to be resynced.

Another approach would be to have the homeserver directly relay the response to
the client in the response to a `GET /_matrix/client/r0/user/{userId}/devices`
request. This approach has been dropped in order to stay consistent in how we
relay device list updates to users.


## Security considerations

This could provide a way for users to flood remote homeservers with federated
device list requests. However, this can be easily mitigated with rate-limiting
and a short-lived cache on the homeserver.


## Unstable prefix

Until this MSC is merged and included in a stable release of the spec,
implementations should use the route
`GET /_matrix/unstable/org.matrix.msc2638/user/{userId}/devices`.
