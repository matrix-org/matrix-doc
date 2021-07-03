# MSC2957: Cryptographically Concealed Credentials

When logging in to Matrix using the `POST /login` endpoint, the client
transmits the password to the server, so the server is able to see the user's
password.  It is generally expected that the server would handle the password
securely, for example, only storing the password in a salted and hashed
format.  However a malicious server could store the user's password.  If a user
re-uses their password on other services, the server administrator could then
use the stored password to log in to the user's other accounts.  Also, this
means that the user's login password should not be the same as the password
that they use for [Secret
Storage](https://matrix.org/docs/spec/client_server/unstable#storage).

This proposal defines a way for users to authenticate without sending their
password to the server.  Additional goals of this proposal include:

- relatively simple to implement
- the data stored on the server cannot be used (apart from attacking the
  underlying cryptographic operations) to authenticate with the server
- the user can verify that the server that they are authenticating against is
  the same as the server where they originally created their account
- a man-in-the-middle cannot use information from observing a registration or
  login to log in as the user
- a malicious user who unsuccessfully tries to authenticate against the server
  does not gain any information about the user's password.  For example, an
  attacker cannot take any of the server's responses to perform any offline
  computations or guesses to try to obtain the user's password.

Another benefit of the method proposed here, compared to the current practice
of sending the password to the server, is that the costly operation of key
stretching is moved to the client rather than the server.  This means that an
attacker cannot easily DoS the server by sending a large number of login
attempts.

## Proposal

### Protocol overview

The protocol operates by generating a Curve25519 key pair based on the user's
password using PBKDF2.  When a user registers their account, the server is
provided with the public part of the key pair and the PBKDF2 parameters.  Thus
the server is not given the user's password directly.

When logging in, the client retrieves the PBKDF2 parameters from the server and
generates the Curve25519 key from the password.  It then uses this key, along
with other ephemeral Curve25519 keys, to generate a MAC key, and calculates the
MAC for a shared message with the server.  The server is able to generate the
same MAC key and verify the MAC calculated by the client to confirm that the
client is in possession of the private key.

Other keys and cryptographic operations are used to provide additional security
properties.

#### Notation

- A Curve25519 key pair is denoted <K<sub>priv</sub>,K<sub>pub</sub>>, where
  K<sub>priv</sub> is the private key and K<sub>pub</sub> is the public key.
- ECDH(A<sub>priv</sub>,B<sub>pub</sub>): the elliptic curve Diffie-Hellman of
  the private key A<sub>priv</sub> and the public key B<sub>pub</sub>.
- HKDF(K, S, I, L): HKDF-SHA-256 where K is the initial key material, S is the
  salt, I is the info, and L is the number of bits to generate.
- PBKDF2(P, S, I, L): PBKDF2 using HMAC-SHA-256 as the hash function, where P is
  the password, S is the salt, I is the iteration count, and L is the length.
- `text in monospace` denotes a literal byte string; "" denotes the empty byte
  string
- "+" denotes concatenation of byte strings

#### Registration

When registering, the client generates an ephemeral Curve25519 key pair
<C<sub>priv</sub>,C<sub>pub</sub>>, and sends to the server:

- the user's desired Matrix ID
- C<sub>pub</sub>

The server generates its own ephemeral Curve25519 key pair
<S<sub>priv</sub>,S<sub>pub</sub>>, and sends the S<sub>pub</sub> to the user.

The ephemeral keys will be used to encrypt the PBKDF2 parameters and the
authentication key when sending them to the server.  The server's ephemeral key
is also used, in conjunction with the authentication key, to generate the
"confirmation key", which is used to ensure that the server that the user
registers with is the same as the server that the user later logs into.  Since
the PBKDF2 parameters and authentication key are encrypted using the server's
ephemeral key, a man-in-the-middle that tries to obtain the PBKDF2 parameters
and authentication key would need to replace the server's ephemeral key with
their own, which means that the server would not calculate the same
confirmation key as the client.  Thus the next time the user logs in, they
would be alerted to the fact that the entity that they were communicating with
is different, unless the same man-in-the-middle is present at the next login
attempt.

The client calculates:

- parameters used for future authentication:
  - Salt = HKDF(R, "", `salt|` + MatrixID), where R is a random byte string
  - K<sub>base</sub> = PBKDF2(Password, Salt, I, 256), where I is an iteration
    count chosen by the client (K<sub>base</sub> can be used as the Secret
    Storage key)
  - the Curve25519 private key A<sub>priv</sub> = HKDF(K<sub>base</sub>, "",
    `authentication key|` + MatrixID, 256) (which is called the "authentication
    key") and the corresponding public key A<sub>pub</sub>
- parameters used for encrypting the above information (the server performs the
  corresponding calculations to decrypt):
  - K<sub>1</sub> = ECDH(C<sub>priv</sub>,S<sub>pub</sub>)
  - K<sub>AES</sub> = HKDF(K<sub>1</sub>, "", `encryption key|`+ MatrixID+ `|` +
    C<sub>pub</sub> + `|` + S<sub>pub</sub>, 256)
  - K<sub>IV</sub> = HKDF(K<sub>1</sub>, "", `encryption iv|` + MatrixID + `|` +
    C<sub>pub</sub> + `|` + S<sub>pub</sub>, 256)
  - K<sub>MAC</sub> = HKDF(K<sub>1</sub>, "", `mac key|` + MatrixID + `|` +
    C<sub>pub</sub> + `|` + S<sub>pub</sub>, 256)

The client sends to the server (encrypted with AES-256-CBC using the key
K<sub>AES</sub> and the initialization vector K<sub>IV</sub>, and MACed with
HMAC-SHA-256 using K<sub>MAC</sub> as the key):

- A<sub>pub</sub>
- R, and I, which can be used to reconstruct the PBKDF2 parameters

The server then generates K<sub>1</sub> =
ECDH(S<sub>priv</sub>,C<sub>pub</sub>) and the derived keys K<sub>AES</sub>,
K<sub>IV</sub>, and K<sub>MAC</sub>, decrypts the information and stores:

- A<sub>pub</sub>
- R and I
- the "confirmation key", calculated as K<sub>conf</sub> = HKDF(ECDH(S<sub>priv</sub>,
  C<sub>pub</sub>) + ECDH(S<sub>priv</sub>, A<sub>pub</sub>), "", `confirmation
  key|` + MatrixID + `|` + A<sub>pub</sub> + `|` + C<sub>pub</sub> + `|` +
  S<sub>pub</sub>, 16)

The client calculates

- the confirmation key K<sub>conf</sub> = HKDF(ECDH(C<sub>priv</sub>,
  S<sub>pub</sub>) + ECDH(A<sub>priv</sub>, S<sub>pub</sub>), "", `confirmation
  key|` + MatrixID + `|` + A<sub>pub</sub> + `|` + C<sub>pub</sub> + `|` +
  S<sub>pub</sub>, 16),
- a security check number HKDF(A<sub>priv</sub> + K<sub>conf</sub>, "",
  `security check|` + MatrixID, 3), giving a number between 0 and 7

The client then displays the emoji (or the text equivalent) from the SAS
verification emoji list corresponding to that number.  The user
remembers/records the emoji for later verification.  Since this emoji is
constructed based on the user's password (by way of A<sub>priv</sub>) and the
confirmation key, it can be used to by the user on later login attempts as a
hint indicating (with some probability):

- whether they have entered the right password, and
- whether they are logging into the same server.

Changing/resetting a user's password would happen similarly, with the addition
that the data in Secret Storage would need to be re-encrypted if the user is
using the same password for that, or re-created if the user does not remember
their previous password.

#### Logging in

The client generates an ephemeral Curve25519 key pair
<C'<sub>priv</sub>,C'<sub>pub</sub>> and sends their Matrix ID and
C'<sub>pub</sub> to the server.

The server then generates its own ephemeral Curve25519 key pair
<S'<sub>priv</sub>,S'<sub>pub</sub>>, calculates

- K<sub>2</sub> = ECDH(S'<sub>priv</sub>, A<sub>pub</sub>) +
  ECDH(S'<sub>priv</sub>, C'<sub>pub</sub>)
- K'<sub>AES</sub> = HKDF(K<sub>2</sub>, "", `encryption key|` + MatrixID +
  `|` + A<sub>pub</sub> + `|` + C'<sub>pub</sub> + `|` + S'<sub>pub</sub>, 256)
- K'<sub>IV</sub> = HKDF(K<sub>2</sub>, "", `encryption iv|` + MatrixID +
  `|` + A<sub>pub</sub> + `|` + C'<sub>pub</sub> + `|` + S'<sub>pub</sub>, 256)

and sends to the client:

- the parameters R and I that it received from the client when registering
- S'<sub>pub</sub>
- a random 32-byte nonce
- K<sub>conf</sub>, encrypted with AES-256-CBC using the key K'<sub>AES</sub>
  and the initialization vector K'<sub>IV</sub>.  Note that this data is not
  MACed; if it is MACed, an attacker could perform an offline attack by testing
  passwords to see which one results in a key that gives the correct MAC.

The client calculates:

- the authentication key, as follows:
  - Salt = HKDF(R, "", `salt|` + MatrixID)
  - K<sub>base</sub> = PBKDF2(Password, Salt, I, 256)
  - the authentication key: A<sub>priv</sub> = HKDF(K<sub>base</sub>, "",
    `authentication key|` + MatrixID, 256) and the corresponding public key
    A<sub>pub</sub>
- the confirmation key, as follows:
  - K<sub>2</sub> = ECDH(A<sub>priv</sub>, S'<sub>pub</sub>) +
    ECDH(C'<sub>priv</sub>, S'<sub>pub</sub>)
  - K'<sub>AES</sub> = HKDF(K<sub>2</sub>, "", `encryption key|` + MatrixID +
    `|` + A<sub>pub</sub> + `|` + C'<sub>pub</sub> + `|` + S'<sub>pub</sub>,
    256)
  - K'<sub>IV</sub> = HKDF(K<sub>2</sub>, "", `encryption iv|` + MatrixID +
    `|` + A<sub>pub</sub> + `|` + C'<sub>pub</sub> + `|` + S'<sub>pub</sub>,
    256)
  - K<sub>conf</sub> by decrypting the ciphertext sent by the server using
    K'<sub>AES</sub> and K'<sub>IV</sub>
- the security check number HKDF(A<sub>priv</sub> + K<sub>conf</sub>, "",
  `security check|` + MatrixID, 3)

The client displays the emoji (or text equivalent) from the SAS verification
emoji list corresponding to the number given by the last calculation, and
allows the user to check that the emoji matches the one displayed when the user
registered their account.  This allows the user to verify (to a degree of
confidence) that they entered their password correctly, and that they are
communicating with the same entity that they were communicating with when they
registered.

To authenticate with the server, the client generates a message that the server
is also able to construct and calculates the MAC for that message using a key
that the server is also able to generate.  The server can prove to the client
that it is the same entity that the user originally registered with in a
similar manner.

The client calculates

- K'<sub>MAC</sub> = HKDF(K<sub>2</sub>, "", `client MAC|` + MatrixID + `|` +
  A<sub>pub</sub> + `|` + C'<sub>pub</sub> + `|` + S'<sub>pub</sub> + `|` +
  K<sub>conf</sub>, 256)

and sends an HMAC of the nonce using the key K'<sub>MAC</sub> to the server.

The server calculates

- K'<sub>MAC</sub> = HKDF(K<sub>2</sub>, "", `client MAC|` + MatrixID + `|` +
  A<sub>pub</sub> + `|` + C'<sub>pub</sub> + `|` + S'<sub>pub</sub> + `|` +
  K<sub>conf</sub>, 256)
- K''<sub>MAC</sub> = HKDF(K<sub>2</sub>, "", `server MAC|` + MatrixID + `|` +
  A<sub>pub</sub> + `|` + C'<sub>pub</sub> + `|` + S'<sub>pub</sub> + `|` +
  K<sub>conf</sub>, 256)

and verifies the HMAC sent by the client, which proves to the server that the
client is in possession of the secret key A<sub>priv</sub>.  The server then
responds with an HMAC of the nonce using the key K''<sub>MAC</sub>, which the
client can check to show that the server is in possession of the public key
A<sub>pub</sub>.

### Protocol details

TODO:

## Security characteristics

### Different ciphersuites

Although the proposal specifically mentions certain cryptographic algorithms
(such as Curve25519 and SHA-256), these can be swapped out for different
algorithms should one algorithm be found to be insecure.

TODO: the protocol details should say how the algorithms are negotiated

### Replay attacks

If an attacker tries to replay the client's messages to the server to
authenticate with it, the authentication will fail since authentication depends
on the randomly chosen ephemeral key and nonce which will be different for the
attacker's session.

### Data breach

If the server's database is leaked, this could reveal A<sub>pub</sub> and
K<sub>conf</sub>.

An attacker could try to brute-force the user's password by trying various
passwords and performing the PBKDF2 and HKDF operations to see if it yields a
Curve25519 private key that matches A<sub>pub</sub>.  However, PBKDF2 will slow
down the attacker's attempts.  This is no worse than the current practice of
storing a hashed version of the user's password.  This can also be made more
secure by encrypting A<sub>pub</sub> using a key that is stored separately from
the database, similarly to how Synapse allows specifying a "pepper" value that
is used when hashing the user's password.  In this way, an attacker who only
has the database, and not the additional encryption key, cannot retrieve
information about the user's password.

If the attacker obtains A<sub>pub</sub> and K<sub>conf</sub>, they can
impersonate the server to the user.  Again, this can be partially mitigated by
encrypting K<sub>conf</sub> in addition to A<sub>pub</sub> using a key that is
stored separately from the database.

Since the server does not know the private key A<sub>priv</sub>, the attacker
cannot use the data stored on the server to authenticate as the given user
short of attacking Curve25519 to obtain A<sub>priv</sub> from A<sub>pub</sub>.

### Deniability

Even though the protocol allows the server to authenticate the user, it cannot
prove to a third party that the user authenticated with it, even if it produces
a full transcript of the authentication process.  All information contained in
the client's requests is either known to the server or could be created by the
server, so the server cannot prove that the requests were created by the user
and not fabricated by the server.

### Offline computation

If an attacker initiates a login attempt, the server does not reveal any
information that would help the attacker determine the user's password.  The
server only reveals: the PBKDF2 parameters to use (which should be viewed as
public information, and do not give any information about the password),
S'<sub>pub</sub> and a random 32-byte nonce (which are single-use and are not
related to the user's password), and an encrypted version of K<sub>conf</sub>.

If the attacker knows K<sub>conf</sub>, they could try to brute-force the
user's password until they can decrypt the encrypted version of
K<sub>conf</sub> to obtain the known value of K<sub>conf</sub>.  However,
K<sub>conf</sub> is only 16 bits long, so there may be multiple passwords that
can result in its correct decryption.  Also, if the attacker knows
K<sub>conf</sub>, they would most likely also know A<sub>pub</sub>, which would
already allow them to try to brute-force the user's password, so in this case,
the attacker does not gain any information by attempting to log in.  Note that
in this case, it is important that the encryption of K<sub>conf</sub> is done
in an unauthenticated manner to ensure that an attacker is not given any
information about whether or not they have guessed the right decryption key.

It should be noted that an attacker who shoulder-surfs when the user registers
or logs in will be able to see the emoji security check displayed to the user.
The attacker may then use this to reduce the search space when trying
passwords.  Since there are eight possible emoji, this reduces the search space
by a factor of 8, which can be compensated for by the user adding an extra
character to their password.  As well, the attacker still needs to test each
password by submitting requests to the server, and so can be rate-limited by
the server.  Since the emoji security check provides some feedback to the user
on whether they mistyped their password (a mistyped password would have a 7/8
chance of displaying the wrong emoji), servers can more aggressively rate-limit
login attempts when using this method.  Clients could also make the emoji
security check optional so that users can disable it when they are in a
situation where shoulder-surfing is likely.

### Man-in-the-middle attacks

An attacker who is able to eavesdrop on the protocol messages could gain
information (for example, A<sub>pub</sub>, if they eavesdrop during the user's
registration) that would allow them to brute-force the user's password.  Since
the sensitive data is encrypted using a key produced by an ECDH, it is not
enough for the attacker to be a passive eavesdropper; they would need to be an
active man-in-the-middle who uses their own set of ephemeral Curve25519 keys.

If there is a man-in-the-middle during the registration phase, then the
K<sub>conf</sub> values calculated by the client and server will be different.
If the user later connects to the server without the man-in-the-middle, the
value of K<sub>conf</sub> encrypted and sent by the server will be different
from the value calculated by the client during registration, yielding a 7/8
chance that the emoji security check will not match.

Conversely, if there is no man-in-the-middle during the registration phase, but
there is one during the login phase, the man-in-the-middle will receive the
value of K<sub>conf</sub> encrypted using a key based on their ephemeral
Curve25519 key.  However, they cannot decrypt it and re-encrypt it to send to
the user since the key is also based on the authentication key, which they do
not have.  Thus the best they can do is pass the ciphertext along, or replace
it with a random value, which has a 7/8 chance of being detected with the emoji
security check.

There is no protection against a man-in-the-middle who is present during the
registration phase and all login phases.

While a 1/8 chance of success is significant, a 7/8 chance of failure may be
enough to dissuade some attackers if the consequences of tipping of the user to
the attacker is viewed as sufficiently significant.

### Malicious PBKDF2 parameters

A malicious server could present incorrect PBKDF2 parameters to a client in
order to perform an attack.

A malicious server could present a very large iteration count in order to DoS a
client by making it perform many calculations.  To guard against this, clients
may define a maximum number of iterations that they are willing to perform, and
fail the login if the requested number of iterations exceeds this number.

On the other hand, a malicious server could present a very small iteration
count.  The server can then try to brute-force the user's password by trying
various passwords using this reduced iteration count until it can reproduce the
MAC sent by the client.  To guard against this, clients may define a minimum
number of iterations that they are willing to perform.

If the server were allowed to send the PBKDF2 salt, it could send a salt for
which it has pre-computed a rainbow table giving possible K<sub>base</sub>
values.  Then, when it receives the MAC from the client, it could try the
various K<sub>base</sub> values until it finds one that matches (if present),
giving it the user's password.  To mitigate against this, the PBKDF2 salt is
first passed through HKDF, which means that the server can no longer control
the PBKDF2 salt.

### Phishing

It may be possible that a user is tricked into trying to log into a malicious
homeserver, thinking that it is their homeserver.  In such a case, there is a
7/8 chance that the emoji security check will not match.  Still, an attacker
might still be happy to trick 1/8 of the people who try to log in.  In the case
where the emoji security check fails to alert the user (either because it
matched or because they ignored it), the attacker would need to brute-force the
user's password based on their response.  This is essentially the same as the
situation given above under "Malicious PBKDF2 parameters".

### ...

## Potential issues

This proposal cannot be used by users who log in using SSO, or whose passwords
are managed by an external system.  In such cases, users will have to use the
current system where they have a separate SSSS password.

## Alternatives

### PAKE

A Password-authenticated Key Exchange (PAKE) is a method by which a password is
used to generate a key that is shared between two parties.  Some PAKEs, those
which define a client and server role where the server does not store
password-equivalent data, are suitable for client-server authentication.

TODO: compare with various PAKEs (e.g. SRP, OPAQUE)

### SCRAM

[SCRAM](https://tools.ietf.org/html/rfc5802) is another protocol that allows a
user to authenticate without the server receiving the user's password.  It also
has the feature that the user is also able to authenticate the server since the
client proves that it has access to the `StoredKey`.  One of its goals is that
the information stored on the server is not sufficient to impersonate a user.
However, if an attacker has access to the server's storage AND is able to
eavesdrop on an authentication (or impersonate the server), they can compute
the `ClientKey`, which is sufficient for the attacker to authenticate with the
server.  This is noted in the "Security Considerations" section of RFC-5802:

> If an attacker obtains the authentication information from the authentication
> repository and either eavesdrops on one authentication exchange or
> impersonates a server, the attacker gains the ability to impersonate that
> user to all servers providing SCRAM access using the same hash function,
> password, iteration count, and salt.  For this reason, it is important to use
> randomly generated salt values.

### Socialist Millionaire

The [socialist millionaire
protocol](https://www.win.tue.nl/~berry/papers/dam.pdf) could be used to
construct an authentication protocol.  Such an authentication protocol might
look something like this: the user's password is used to generate a Curve25519
key part, and the public part is given to the server, as is done in this
proposal.  On login, the Curve25519 key is used to generate a shared secret,
possibly in a way similar to what is done in this proposal.  The client and
server can then use the socialist millionaire protocol to determine if they
have the shared secret.  In this way, if either party is not who they claim to
be, they will not gain any information about the user's credentials.

This would address some of the vulnerabilities in the protocol from this
proposal.  However, the current socialist millionaire protocol is tied to the
discrete logarithm problem.  It would also be harder for Matrix clients to
implement since it uses cryptography that is not currently used by Matrix
clients.

### Argon2

Argon2 would likely be a better option than PBKDF2 for generating a key from
a password.  However, this proposal uses PBKDF2 for compatibility with Secret
Storage, which used PBKDF2 due to the availability of implementations of both
algorithms.  (For example, WebCrypto includes a PBKDF2 implementation, but not
an Argon2 implementation.)  In the future, we may switch to Argon2 for both
authentication and Secret Storage.

## Security considerations

### Old clients

If a user tries to log into their account using a server that does not follow
this proposal may send the user's password to the server by trying to log in
using the current `POST /login` endpoint.  This can be partially mitigated in
two ways.

1. Deployments in which the choice of clients is not well controlled should not
   enable this feature until most of the commonly-used clients are updated to
   support this feature.  It is up to individual server administrators to
   determine when to do this.

2. Users should be educated to expect to see and verify the emoji security
   check before submitting the password.  Old clients will not display the
   emoji, providing a hint to users that the client does not support this
   authentication method.

### User enumeration

Since users log in by first submitting their user ID to the server before
supplying their credentials, an attacker could determine which user IDs are
active if the server responds differently for user IDs that are not in use.  If
a server does not want attackers to be able to learn this information, it
should respond to such requests with a response consistent with how it would
respond to an existing user.  When it does so, the PBKDF2 parameters should be
the same when a specific user ID is requested multiple times.  Otherwise, an
attacker could make two login requests in quick succession and compare the
PBKDF2 parameters to see if they are different.  One way to do this is to set
the iteration count to a value that is used in a common client, and set the
salt to a hash of the requested user ID, salted by a secret value.

## Possible future work

TODO: combine 2FA?

## Unstable prefix

TODO:
