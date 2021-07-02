# Login and SSSS with a Single Password

The current approach for secure server-side storage (SSSS) requires that users
create and remember two different passwords for each account.  Unfortunately,
humans are not very good at creating and remembering even one strong password
per account.  Requiring the use of two passwords increases the risk that users
will choose at least one weak password, or that they will re-use the same
password for both purposes.

The case where a user uses a single password for both login and SSSS is
particularly dangerous.  Even though the homeserver should not store the 
password in long-term storage, it does learn the password whenever a user
logs in or authenticates through the user-interactive authentication API.
At that point, a malicious or compromised homeserver could easily decrypt
all of the lazy user's server-side storage.

This proposal describes a new scheme that clients can use to better protect
their users' secrets.  It does not require any changes on the server side.

The general idea is to use hash functions with the user's human-memorable
("raw") password to generate two different secrets.  We use the first secret
as the new login password, and we use the second secret as the symmetric
encryption/decryption key for SSSS.

## Security Requirements

The scheme should satisfy the following requirements:

1. Given the login password, it should be computationally infeasible to
recover the user's original "raw" password.

2. Given the login password, it should be computationally infeasible to
recover the user's SSSS key.

3. Given no special information about the user's "raw" password, it should
be computationally impractical for an adversary to recover either the login
password or the SSSS key.  This requirement applies even to adversaries
who can build or buy specialized hardware, including GPUs, FPGAs, and
ASICs in order to accelerate a brute-force search for the password.

## High-Level Description of the Scheme

The proposed construction is very simple.  It relies on two cryptographic hash
functions.  

1. `H()` - a standard cryptographic hash function, such as SHA256.

2. `PHF()` - a password hashing function, such as bcrypt, scrypt, argon2, or
(if necessary) PBKDF2.

First we pass the user's "raw" password through the password hashing function
to generate a "root" secret known only to the client.  We use a salt derived
from the user's ID to thwart precomputation attacks using rainbow tables or
other time-memory tradeoffs.

```
  salt = H(user_part)
  root_secret = PHF(raw_password, salt)
```

This protects against adversaries that want to recover the raw password.
The PHF parameters should be chosen such that brute force password guessing
attacks are not practical.  For example, the beta version of Circles uses
Bcrypt with work factor 14.  With this setting, computing a single hash is
very fast -- probably under 500ms on mid-range Apple hardware like the
iPhone X, iPhone XR, and the 2018 iPad.  However, a brute-force search for
a non-trivial password would be extremely expensive.

Second, we hash the root secret with the hash function, using two different
prefixes to produce two hash digests, very similar to the way a chain key is
hashed in the double ratchet to produce a message key and a new chain key.
This gives us the two seemingly independent secrets that we require.

We use the first derived secret to create the user's new login password, by
encoding it as an ASCII/UTF8 hex string and taking the first 32 characters.

We take the second derived secret as the symmetric key for SSSS.

```
  login_password = H('LoginPassword'|root_secret)[:16].utf8()
  ssss_key = H('S4Key'|root_secret)
```

## Security Analysis

An adversary who can temporarily take over the homeserver can observe the
login password submitted in requests for password login or user-interactive
authentication.  Our security requirements above state that this adversary
must not be able to learn the SSSS key or the user's human-memorable "raw"
password.

### Protecting the SSSS key
If the attacker can recover the root secret, then it can easily compute the
SSSS key.  The proposed construction protects against this line of attack.
If the hash function is preimage resistant, then the login password gives
the attacker no real information about the root secret.

### Protecting the user's "raw" password
As noted above, the preimage resistance property of the hash function
prevents the attacker working backwards to obtain the root secret.
Furthermore, even if the attacker did know the root secret, the password
hashing function should also offer preimage resistance.  Therefore the
attacker cannot invert the password hash to recover the password.

The attacker's best strategy then is to attempt a brute-force search for
the password, using the latest password dictionaries and guessing rules,
plus possibly specialized hardware to accelerate the computation of the
hash.

If the user uses a reasonable password (ie, not in the password dictionaries,
and not a simple derivation from a word that is), and the password hashing
function resists acceleration, then the brute force guessing attack is also
not practically feasible.

Regardless of the user's choice of password, the proposed scheme is no
weaker than the current approach, where the user has separate passwords
for login and for SSSS.  Under the current approach, the adversary who
temporarily compromises the homeserver learns the login password immediately,
and must brute-force search for the SSSS password.  A clever adversary would
prioritize use of the login password in its brute-force search for the SSSS
password, since many users might re-use their login password, or a closely
related password, for SSSS.




