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

## Proposal

The following information would be available (for anyone without any 
pre-arranged state):

* whether the HS supports (open) registrations
* number of registered users / active users in the last *week/month*
* server uptime
* server admin contact (this is covered by pull#1929)
* server description / blurb
* country of the server (if applicable)

Apart from the *first one* all endpoints can be "legally" disabled and 
result a *NOT_DISCLOSED* error, so the admin can decide not to publish 
the data for whatever reason. 

It could be useful to provide a - heavily rate limited - *connectivity 
endpoint*, which would make it possible to "ping" other servers, in a 
very limited fashion (eg. only already known servers and skip anything 
which is backed off already, etc.), since it could provide info on 
connectivity (like when a server is available on IPv6 but cannot reach 
IPv4 servers).

## Tradeoffs

This would provide a standardised **possibility** for admins to publish 
the data helping to pick their servers, it is not compulsory, thus does 
not guarantee that such data is available.

*Active users counter* may need some logic (and thus cpu cycles) to 
calculate.

## Security considerations

Since servers are reachable through public methods these don't really 
open up attack surfaces; most replies are static data. Dynamic results 
shall be protected from DoS (rate limiting, possibly simply globally).

## Conclusion

Implementing these endpoints would make it possible to generate 
automated server lists with data suited to make educated guesses about 
server suitability for new users.

