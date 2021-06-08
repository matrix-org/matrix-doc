# Proposal for more granular profile error codes

Clients and other applications in the wider Matrix ecosystem may wish to do a "proof of life"
check on users to see if they exist. For clients, this may be done ahead of inviting a user to
a room to assist the user in picking the right target. Other use cases may include a bridge which
is attempting to map from the 3rd party protocol to Matrix instead of the other way around.

Currently the best way to perform this check is to ask for the target user's profile, however
this option is not great. Under the current specification, servers can return 404 for a wide
range of reasons which are not all that helpful.


## Proposal

We make `GET /_matrix/client/$version/profile/$userId` return more granular responses to aid
the specific use cases outlined above:

* 200 OK - The profile was found and supplied by the server (no change from the current spec).
* 404 / `M_USER_NOT_FOUND` - The server acknowledges that the user was not found/does not exist.
* 404 / `M_PROFILE_NOT_FOUND` - The server acknowledges that the user does exist, but has an
  otherwise empty profile.
* 404 / `M_PROFILE_UNDISCLOSED` - The server is refusing to disclose details about this user. Clients
  cannot assume that the user does or does not exist.

The rationale for keeping all 3 error codes as `404 Not Found` is to maintain backwards compatibility
with clients which may already be calling these endpoints.

Currently, `M_NOT_FOUND` is returned for when a profile is empty or when the requested user was not
found. This proposal is splitting that out into `M_USER_NOT_FOUND` and `M_PROFILE_NOT_FOUND` for added
clarity to clients.

To reiterate, `M_PROFILE_UNDISCLOSED` is not to be assumed as an admission that the requested user does
or does not exist. The server could be refusing to disclose the user/profile for a variety of reasons
including prevention of user ID harvesting or to maintain a highly private environment.

In all cases, the server would be expected to proxy the error code returned by remote servers if the
profile request ends up being for a remote user.

Clients which do check for existence are encouraged to provide the user with a "continue anyways"
option where possible. For example, if the client checks that users exist before inviting them, it
may wish to warn the user that one or more targets might not be actual users in the system but should
still let the user invite them anyways.


## Alternative Solutions

#### Add a new proof of life endpoint

Adding another endpoint further complicates the spec for such a small feature. Additionally, clients
may actually end up wanting the profile returned from the endpoint and shouldn't have to call two
different endpoints to get highly related information.


## Potential issues

If accepted, it is possible that a private federation of servers results in only ever `M_PROFILE_UNDISCLOSED`
errors, regardless of who is requesting the information. In these cases, clients may wish to consider
supporting a configuration option for not checking whether a user exists or not to avoid bombarding the
user with warnings constantly.
