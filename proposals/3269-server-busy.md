# MSC3269: An error code for busy servers

Sometimes, the server cannot respond because it's too busy.

This proposal introduces `M_SERVER_BUSY` for this use case.

## Proposal

A server may decide to throttle an individual user who places too many requests. This is currently returned as
`M_RESOURCE_LIMIT_EXCEEDED`. However, this does not cover the case in which the server is busy for other reasons.

This proposal introduces `M_SERVER_BUSY`, to be used when the server is too busy to respond right now, typically
because a large number of pending requests, and the client should retry later. It is typically designed to be returned
with a `retry_after_ms`, which hints how long the client should wait before retrying.

Clients are expected to display a message along the lines of "The server is currently experiencing a high load, this
operation may take longer than usual."

## Potential issues

None that I can see.

## Alternatives

We could rather decide that `M_RESOURCE_LIMIT_EXCEEDED` can also be used to mean that the user should wait before
retrying, even if they're not the ones using too many resources. I suspect that this would be confusing, though.

## Security considerations

I can't think of any security issues that this could cause.

## Unstable prefix

I believe that this doesn't need an unstable prefix.
