# MSC 2666: Get rooms in common with another user

It is useful to be able to fetch rooms you have in common with another user. Popular messaging services
such as Telegram offer users the ability to show "groups in common", which allows users to determine
what they have in common before participating in converstion.

There are a variety of applications for this information. Some users may want to block invites from
users they do not share a room with at the client level, and need a way to poll the homeserver for
this information. Another use case would be trying to determine how a user came across your mxid, as
invites on their own do not present much context. With this endpoint, a client could tell you what
rooms you have in common before you accept an invite.

While this information can be determined if the user has full access to member state for all rooms,
modern clients often implement "lazy-loading", so they often only have a subset of state for the rooms
the user is in. Therefore, the homeserver should have a means to provide this information.

This proposal aims to implement a simple mechanism to fetch rooms you have in common with another user.


## Proposal

Homeservers should implement a new endpoint `/user/shared_rooms/{user_id}` which will take
the MxID of the user who is being searched for.

The response format will be an array containing all rooms where both the authenticated user and `user_id` have
a membership of type `join`. If the `user_id` does not exist, or does not share any rooms with the authenticated user,
an empty array should be returned.

```
GET /_matrix/client/r0/user/shared_rooms/%40bob%3Aexample.com
```

```json
{
  "joined": [
    "!OGEhHVWSdvArJzumhm:matrix.org",
    "!HYlSnuBHTxUPgyZPKC:half-shot.uk",
    "!DueayyFpVTeVOQiYjR:example.com"
  ]
}
```

The response error for trying to get shared rooms with yourself will be an HTTP code 400, with `M_FORBIDDEN` as the `errcode`.

## Potential issues

Homeserver performance and storage may be impacted by this endpoint. While a homeserver already stores
membership information for each of its users, the information may not be stored in a way that is readily
accessible. Homeservers that have implemented [POST /user-directory/search](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-user-directory-search)
may have started some of this work, if they are limiting users to searching for users for which they
share rooms. While this is not a given by any means, it may mean that implementations of this API
and /search may be complimentary.


## Alternatives

A client which holds full and current state can already see all membership for all rooms, and thus
determine which of those rooms contains a "join" membership for the given user_id. Clients which "lazy-load"
however do not have this information, as they will have only synced a subset of the full membership for
all rooms. While a client *could* pull all membership for all rooms at the point of needing this information,
it's computationally expensive for both the homeserver and the client, as well as a bandwidth waste for contrained
clients.


## Security considerations

The information provided in this endpoint is already accessible to the client if it has a copy of all
state that the user can see. This endpoint only makes it possible to get this information without having
to request all state ahead of time.


## Unstable prefix

The implementation MUST use `/_matrix/client/unstable/uk.half-shot.msc2666/user/shared_rooms/{user_id}`.  
The /versions endpoint MUST include a new key in `unstable_features` with the name `uk.half-shot.msc2666`.
If the value is false or the key is not present, clients MUST assume the feature is not available.
Once the MSC has been merged, clients should use `/_matrix/client/r0/user/shared_rooms/{user_id}`
and will no longer need to check for the `unstable_features` flag.
