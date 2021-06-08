* **author**: Peter Gervai
* **Created**: 2019-05-32

## Introduction 

Matrix network have a general problem of an overloaded _matrix.org_ 
server and many underused, hard to find servers just waiting for users. 
There are -- and probably will be more -- services which help users to 
find servers matching their needs. These lists are only as useful as 
the data they offer.

The most important data is available: network reachability. Apart from 
that, however, there are very few API endpoints available to provide 
generic statistical and administrative data about the servers for 
future users. This proposal offers ideas of such endpoints, and 
welcomes input from seasoned spec authors to actually dream it into 
syntax.

Right now the following is available:
* server version (`_matrix/federation/v1/version`)
* supported client specs (`_matrix/client/versions`)
* supported login methods (`_matrix/client/r0/login`)

Technically `_matrix/key/v2/query` can be used as a crude 
connectivity-check tool.

The proposed endpoint(s) would provide a standardised **possibility** 
for admins to publish the data helping to pick their servers, it is 
not compulsory, thus does not guarantee that such data is available.

## Proposal

The following information would be available (for anyone without any 
pre-arranged state):

* whether the HS supports (open) registrations
* number of registered users / active users in the last *week/month*
* server uptime

Apart from the *first one* all endpoints can be "legally" disabled and 
result a `M_FORBIDDEN` error, so the admin can decide not to publish 
the data for whatever reason. 

### GET /_matrix/federation/v1/server_data

* Rate-limited: Yes
* Requires auth: No

Requires no parameters.

Response:

```json
{
  "server_data": {
    "m.open_registrations": true,
    "m.uptime": 63072000,
    "m.registered_users": 4,
  }
}
```
* `open_registrations`: `true` if the server accepts new account registrations
  (open server); this response field is **required**.
* `uptime` in *seconds* (possible to see whether there was a recent restart,
  upgrade)
  
### Data acquired by other means

The following data will be (or ought to be) provided by pull#1929 
(MSC 1929) through static `.well-known` method:

* server human readable name
* server description / blurb
* country of the server (if applicable)
* server admin contact

There ought to be a way to gather *server connectivity data*, to check
working federation, but it shall be covered by a specific proposal later.

## Security considerations

Since servers are reachable through public methods these don't really 
open up attack surfaces; replies are quasi-static data. 

## Conclusion

Implementing these endpoints would make it possible to generate 
*automated server lists* with data suited to make educated guesses about 
server suitability for new users.

