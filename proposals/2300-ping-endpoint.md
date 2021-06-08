# Proposal for a /ping endpoint on the CS API

## Proposal

Currently there is no well-defined way for clients to determine whether their server is still alive and well.
Riot/Web fudges this by calling /versions, but this is an abuse (especially if & when /versions becomes a richer endpoint).

We propose a new endpoint:

`GET /_matrix/client/r0/ping`

which returns

```
200 OK
{}
```

to replace the abuse of /versions for this purpose.
