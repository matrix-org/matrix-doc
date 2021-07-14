# \[WIP]MSC3262: aPAKE authentication

Like most password authentication, matrix's 
[login](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-login) 
requires sending the password in plain text (though usually encrypted in transit with https). 
This requirement has as (obvious) downside that a man in the middle attack would allow reading the password,
but also requires that the server has temporary access to the plaintext password 
(which will subsequently be hashed before storage).

A Password Authenticated Key Exchange (PAKE) can prevent the need for sending the password in plaintext for login,
and an aPAKE (asymmetric or augmented) allows for safe authentication without the server ever needing
access to the plaintext password. OPAQUE is a modern implementation of an aPAKE that is
[currently an ietf draft](https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-opaque-05), 
but as it's still pending and doesn't have many open source implementations using it would 
require implementing it ourselves. As such choosing to use SRP 
([rfc2945](https://datatracker.ietf.org/doc/html/rfc2945)) makes more sense. 
SRP has as downside that the salt is transmitted to the client before authentication, 
allowing a precomputation attack which would speed up a followup attack after a server compromise.
However, should a server be compromised, 
it is probably simpler to generate an access token and impersonate the target that way.

## Proposal

Add support for the SRP 6a login flow, as `"type": "m.login.srp6a"`.

### Registration flow

To allow clients to discover the supported groups (and whether srp6a is supported)
the client sends a GET request.

`GET /_matrix/client/r0/register`

```
{
	"auth_types": ["password", "srp6a"]
	"srp_groups": [supported groups]
}
```  
Here the server sends it's supported authentication types (in this case only password and srp6a)
and if applicable it sends the supported SRP groups, as specified by the 
[SRP specification](https://datatracker.ietf.org/doc/html/rfc5054#page-16) or 
[rfc3526](https://datatracker.ietf.org/doc/html/rfc3526).

The client then chooses an srp group and generates a random salt `s`.
The client then calculates the verifier `v` as:

	x = H(s, p)  
	v = g^x

Here H() is a secure hash function, and p is the user specified password, 
and `g` is the generator of the selected srp group.  
Note that all values are calculated modulo N (of the selected srp group).

This is then sent to the server, otherwise mimicking the password registration, through:

`POST /_matrix/client/r0/register?kind=user`

```
{
  "auth": {
    "type": "example.type.foo",
    "session": "xxxxx",
    "example_credential": "verypoorsharedsecret"
  },
  "auth_type": "srp6a",
  "username": "cheeky_monkey",
  "verifier": v,
  "group": [g,N],
  "salt": s,
  "device_id": "GHTYAJCE",
  "initial_device_display_name": "Jungle Phone",
  "inhibit_login": false
}
```

The server stores the verifier, salt, and group next to the username.  

### Convert from password to SRP

Mimicking the flow of register above, first a GET request is sent to check if SRP is 
supported and find the supported groups, here we'll reuse the register endpoint 
`GET /_matrix/client/r0/register`. *Or we could add a GET endpoint for /_matrix/client/r0/account/password*

To convert to SRP we'll use the [change password endpoint](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-account-password) with the 
`"auth_type": "srp6a"` added, and the required `verifier`, `group`, and `salt`.

`POST /_matrix/client/r0/account/password HTTP/1.1`

```
{
  "auth_type": "srp6a",
  "verifier": v,
  "group": [g,N],
  "salt": s,
  "logout_devices": false,
  "auth": {
    "type": "example.type.foo",
    "session": "xxxxx",
    "example_credential": "verypoorsharedsecret"
  }
}
```

The server then removes the old password (or old verifier, group, and salt) and stores the new values.

### Login flow

To start the login flow the client sends a GET request to `/_matrix/client/r0/login`, the server responds with:

```
{
  "flows": [
    {
      "type": "m.login.srp6a"
    }
  ]
}
```
(and any other supported login flows)

Next the client sends it's username to obtain the salt and SRP group as:

`POST /_matrix/client/r0/login`

```
{
  "type": "m.login.srp6a.init",
  "username": "cheeky_monkey"
}
```

If the user hasn't registered with SRP the server responds with:

`Status code: 403`

```
{
  "errcode": "M_UNAUTHORIZED",
  "error": "User has not registered with SRP."
}
```

The server responds with the salt and SRP group (looked up from the database), and public value `B`:

```
{
  "prime": N,
  "generator": g,
  "salt": s,
  "server_value": B,
  "auth_id": "12345"
}
```
Here N is the prime and g is the generator of the SRP group. s is the stored salt for the user
as supplied in the `POST`, B is the public server value, and auth_id is the id of this authentication flow,
can by any unique random string, used for the server to keep track of the authentication flow.

the server calculates B as:

	B = kv + g^b 

where b is a private randomly generated value for this session (server side) and k is given as:

	k = H(N, g) 

The client then calculates:

	A = g^a 
where a is a private randomly generated value for this session (client side).

Both then calculate:

	u = H(A, B) 

Next the client calculates:

	x = H(s, p)  
	S = (B - kg^x) ^ (a + ux)  
	K = H(S)

The server calculates:

	S = (Av^u) ^ b  
	K = H(S)

Resulting in the shared session key K.

To complete the authentication we need to prove to the server that the session key K is the same.
*note that this proof is directly lifted from the [SRP spec](http://srp.stanford.edu/design.html),
another proof can be possible as well.*

The client calculates:

	M1 = H(H(N) xor H(g), H(I), s, A, B, K)

The client will then respond with:

`POST /_matrix/client/r0/login`

```
{
  "type": "m.login.srp6a.verify",
  "evidence_message": M1,
  "client_value": A,
  "auth_id": "12345"
}
```
Here `M1` is the client evidence message, and A is the public client value.
Upon successful authentication (ie M1 matches) the server will respond with the regular login success status code 200:

To prove the identity of the server to the client we can send back M2 as:

	M2 = H(A, M, K)

```
{
  "user_id": "@cheeky_monkey:matrix.org",
  "access_token": "abc123",
  "device_id": "GHTYAJCE",
  "evidence_message": M2
  "well_known": {
    "m.homeserver": {
      "base_url": "https://example.org"
    },
    "m.identity_server": {
      "base_url": "https://id.example.org"
    }
  }
}
```

The client verifies that M2 matches, and is subsequently logged in.


## Potential issues

Adding this authentication method requires client developers to implement this in all matrix clients.

As long as the plain password login remains available it is not trivial to allow clients to
assume the server never learns the password, since an evil server can say to a new client that it
doesn't support SRP and learn the password that way. And with the client not being authenticated
before login there's no easy way for the client to know whether the user expects SRP to be used.
The long-term solution to this is to declare the old password authentication as deprecated and
have all matrix clients refuse to login with `m.password`. This may take a long time; "the best
moment to plant a tree is 10 years ago, the second best is today."
The short term solution requires a good UX in clients to notify the user that they expect to
login with SRP but the server doesn't support this.
*My initial thought was to look at whether SSSS is set for the user, or even try to decrypt it*
*with the given password and give a warning if this works, but the server can just lie to the*
*client about that, leaving the user none the wiser.*

SRP is vulnerable to precomputation attacks and it is incompatible with elliptic-curve cryptography.
Matthew Green judges it as 
["It’s not ideal, but it’s real." and "not obviously broken"](https://blog.cryptographyengineering.com/2018/10/19/lets-talk-about-pake/)
and it's a fairly old protocol.

## Alternatives

OPAQUE is the more modern protocol, which has the added benefit of not sending the salt in plain text to the client,
but rather uses an 'Oblivious Pseudo-Random Function' and can use elliptic curves.

*Bitwardens scheme can be mentioned here as well, since it does allow auth without the server
learning the plaintext password, but it isn't a PAKE, but rather something along the lines of a hash
of the password before sending the hash to the server for auth, practically making the hash
the new password, and as such it doesn't protect against a mitm.*

The UIA-flow can map pretty well on the proposed login flow and would remove the need for `m.login.srp6a.init`.
This is deemed out of scope for this MSC, but would not be hard to change later.


## Security considerations

SRP uses the discrete logarithm problem, deemed unsolved, though Shor's algorithm can become an
issue when quantum computers get scaled up. Work seems to have been done to create a quantum-safe
SRP version, see [here](https://eprint.iacr.org/2017/1196.pdf), though I lack the credentials to
determine whether or not this holds water.


This whole scheme only works if the user can trust the client, which may be an issue
in the case of a 'random' javascript hosted matrix client, though this is out of scope for this MSC.

## Outlook
This MSC allows for authentication without the server learning the password, and authenticating
both the server and the client to each other. This may prevent a few security issues, such as
a CDN learning the users password. The main reason for this MSC is that later this may allow 
the reuse of the same password for both authentication and SSSS encryption while remaining secure.

## Unstable prefix
The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`m.login.srp6a.*` | login type | `com.vgorcum.msc3262.login.srp6a.*`
