# MSC2391 - Efficient point-queries for Room state over Federation

The principal method for obtaining Matrix Room state over Federation is
specified in Server-to-Server r0.1.3 §10.1 and §10.2. These two
endpoints `/state/` and `/state_ids/` respectively, both conduct bulk transfers
of the entire state of a room. The state of a room in Matrix can be lumbering
for implementations to process entirely at once. Worse, in practice, these
endpoints mostly transfer data which is redundant to copies held by the
requestor, or far too much data than they cared to obtain in the first place.

The federation interface lacks an essential granular alternative to these
methods. Interestingly, the client-to-server interface is capable of conducting
point-queries for room state (see: client-to-server r0.6.0 §9.5.1 and §9.5.2)
so we are compelled to approach the following solutions as a reduction from
the client-to-server interface.

##### GET `/_matrix/federation/v1/state/{roomId}/{eventType}/{stateKey}`

We specify an endpoint capable of querying state at a cellular level over
Federation using `(eventType,stateKey)` arguments. All other parameters,
response format, and error conditions are inherited from server-to-server
§10.1.

##### GET `/_matrix/federation/v1/state/{roomId}/{eventType}`

We specify an endpoint capable of querying state at a class level over
Federation using `(eventType)` arguments. All other parameters,
response format, and error conditions are inherited from server-to-server
§10.1.

#### Analysis

Efficient room state queries over federation provide an essential foundation
to implement MSC1769, MSC2390, and countless others. For example,
`GET /_matrix/federation/v1/state/!@jason:zemos.net/m.user.profile/avatar_url`
