# MSC2821: Test Pusher

It is often useful for both client developers and end-users to be able to test
their push notification configuration. In order to facilitate this a new API
is proposed which instructs the homeserver to notify the push gateway to send a
test push to the client device.


## Proposal

A new endpoint is to be added which will allow testing push notifications. It
requires the `pushkey` and `app_id` parameters, which should match a previously
added pusher.

```
POST /_matrix/client/r0/pushers/push HTTP/1.1
Content-Type: application/json

{
  "app_id": "com.example.app.ios",
  "pushkey": "APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvPVGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7hH5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMCg2ZXKqpc8FXKmhX94kIxQ"
}
```

A 200 response is returned if the push was successful. A 400 response is returned
if one or more fields were invalid. A 429 response is returned if the request was
rate-limited.

## Additional thoughts

It might potentially make sense to accept a parameter which would act as a
"test event" to run push rules over. This would potentially allow a deeper check
than just kicking off a push.

## Security considerations

This could potentially be used to spam a user with notifications via a homeserver,
but the endpoint is authenticated so that seems like a limited risk. Regardless,
this endpoint should be rate limited.

## Unstable prefix

TODO
