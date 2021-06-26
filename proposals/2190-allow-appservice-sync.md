# Allow appservice bots to use /sync

In the past, application services could use `/sync` as the appservice bot as an
alternative to having a HTTP server listening for events from the homeserver.
At some point, that feature was deprecated and broke entirely, so appservice
bot `/sync`ing was blocked in synapse entirely (in [matrix-org/synapse#2948]).
Later the limitation was added to the spec in [matrix-org/matrix-doc#1144] and
[matrix-org/matrix-doc#1535].

Currently, the application service spec states

> Application services wishing to use `/sync` or `/events` from the Client-Server
  API MUST do so with a virtual user (provide a `user_id` via the query string).
  It is expected that the application service use the transactions pushed to
  it to handle events rather than syncing with the user implied by
  `sender_localpart`.

## Proposal

The limitation is unnecessary, so this proposal suggests removing the special
casing. This would mean calling `/sync` with the appservice token and no
identity assertion parameter would work the same way as any other user calling
`/sync`, i.e. it only returns events for the appservice bot. Note that this
behavior would be different from the original synapse behavior, where `/sync`
returned events for all users in the appservice's namespace.

## Tradeoffs

None.

## Potential issues

Old appservices that use `/sync` could run into silent issues rather than the
very clear internal server error currently thrown by synapse.

## Security considerations

None.

[matrix-org/matrix-doc#1144]: https://github.com/matrix-org/matrix-doc/issues/1144
[matrix-org/matrix-doc#1535]: https://github.com/matrix-org/matrix-doc/pull/1535
[matrix-org/synapse#2948]: https://github.com/matrix-org/synapse/pull/2948
