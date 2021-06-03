# MSC2782: HTTP Pushers with the full event content

Sometimes you might want to receive the full event in push notifications, not just the room id and
the event id. For that, for pushers of kind `http` there is a `format` specified, however the only
[speced format](https://matrix.org/docs/spec/client_server/latest#post-matrix-client-r0-pushers-set)
currently is `event_id_only`.

In some scenarios this might be insufficient, e.g. if you are in a closed ecosystem (as in, you know
that the push message is not proxied via any third party) and the receiving end does of the push
notification does not have an access token, e.i. is not a matrix client. If the full event was pushed
no information was leaked but the notification could be displayed significantly more nicely.

Please note that [synapse already supports this](https://github.com/matrix-org/synapse/blob/develop/synapse/push/httppusher.py#L313),
and [the old riot-android used to use it](https://github.com/matrix-org/matrix-android-sdk/blob/develop/matrix-sdk/src/main/java/org/matrix/androidsdk/rest/client/PushersRestClient.java#L135-L137),
so working implementations already exist.

## Proposal

For pushers of kind `http` a new `format`, `full_event`, is introduced. If this format is specified
it is expected that the homeserver tries to fill out the following fields as specified in the [push gateway api](https://matrix.org/docs/spec/push_gateway/r0.1.1#post-matrix-push-v1-notify):
 - `event_id`
 - `room_id`
 - `type`
 - `sender`
 - `prio`
 - `counts`
 - `membership` (for `m.room.member`)
 - `user_is_target` (for `m.room.member`)
 - `content`
 - `sender_display_name`
 - `room_name`

## Potential issues

None

## Alternatives

The usecase in the introduction was that the receiving end of the push notification does not have an
access token. Thus, it is impossible for it to fetch the event content based on only the room id and
event id. So the only alternative was to require such services to be configured with an access token,
which seems rather sub-ideal, depending on situation.

## Security considerations

If an unknowing client configures to receive the full event via push, it is possible that the event
contents are routed via googles are apples servers, in case of android and iOS apps. Thus, the spec
should appropriately inform client developers about this, and if a client chooses to make it optional
to receive the full event over push, the client should properly inform the user about the privacy
implications. The old riot-android already had a good example of that.

## Differences to the old riot-android implementation

The old riot-android implementation just left out the `format` if it wanted to receive the whole event
over push. While the format isn't required for kind `http` (spec bug?) it seems like a good idea to
introduce it to be required, or to make the default the more privacy-respecting `event_id_only`. Having
to explicitly state when you want to receive the `full_event` seems more appropriate to address the
mentioned security considerations.
