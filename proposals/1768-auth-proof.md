# Proposal to authenticate with public keys

With the advances in blockchain technologies, so-called user-owned or "distributed
identifiers" (DID) have been established that are created, owned and controlled by the
person herself. These identifiers come with a cryptographic private/public key pair that
can be used to authenticate the user without using the user's password. The user might have
control over other private/public key pairs (like local TLS certificates) that can be used
in the same way as keys from DIDs. Therefore, this proposal is about a general
authentication flow using any private/public key pairs.

In order to authenticate with a matrix home server, the user should proof that she is in
control of a public key that was associated with the user's account as administrative
contact. A new endpoint should be added that provides a reference to these private/public
key pairs.

A second new endpoint should be added that provides a challenge to the user. The user
should sign and return the challenge in the authentication request.

## Proposal

User should be able to login with the private/public keys that they control. The following
authentication flow should be defined assuming that the user has already associated her
public key with her matrix account using ``/account/3pid/``

A new class of login types should be defined starting with ``m.login.proof.`` followed by
the identifier for the relevant cryptographic methods. These identifiers are publishd in
the registry of the [W3C Credentials Communicy Group](https://w3c-ccg.github.io) for
[linked data cryptographic suites](https://w3c-ccg.github.io/ld-cryptosuite-registry).
Examples are ``EdDasSASignatureSecp256k1`` or ``RsaSignature2018``.

To use this authentication type in login calls, clients should submit the following:

````
  {
    "type": "m.login.proof.<crypto_suite_id>",
    "identifier": {
      ...
    },
    "challenge": "<challenge>",
    "proof": "<proof>"
  }
````

where the ``proof`` contains the matrix id and a signature containing a challenge that the
user has received before from the challenge endpoint of the home server. The (json) type of
``proof`` is defined in 
[the specification for Linked Data Proofs](https://w3c-dvcg.github.io/ld-proofs) and
contains ``type`` (of proof; equals to crypto_suite_id), ``creator`` (reference to the
user's public key), ``created`` (when the proof/signature was created), ``domain`` (the
matrix user name), ``nonce`` (provided by the client), ``proofValue`` (the signature).

Example:
````
  {
    "type": "m.login.proof.RSASignature2018",
    "identifier": {
      "type": "m.id.thirdparty",
      "medium": "did",
      "address": "did:stacks:SM24...d4A"
    },
    "challenge": "achallengefromtheserver",
    "proof": {
        "type": "RSASignature2018",
        "creator": "https://matrix.org/account/friedger/keys/1",
        "created": "2019-01-02T23:21:12Z",
        "domain": "@friedger:matrix.org",
        "nonce": "anoncefromtheuser",
        "proofValue":"eyJ.....fFWFOEjxk"
    },
  }
````

The home server responds with the access token as usual if the proof could be verified
using the algorithm specified in the Linked Data Proof document.

If the signature could not be verified the error ``M_UNAUTHORIZED`` should be returned.

The reference endpoint for public keys should be defined as
``/account/<username>/keys/<number>``. It returns a json containing a description of the
public key of ``username`` with id ``number`` in the format

````
  {
    "owner": "@friedger:matrix.org",
    "publicKeyBase58": "H3C....PV",
  }
````

The challenge endpoint should be defined as ``/account/proof/requestChallenge`` and return
a random text that is unique for each call (within a time window that is sufficient to
complete the login flow).

## Tradeoffs

Instead of adding a new login type, the type ``m.login.password`` could be used. The
password could contain the signature of the challenge and during password verification the
home server could verify the signature. However, it is not the password of matrix user and
therefore, the password login type should not be used.

The creation of the challenge for the login call could be handled by the
identity server. The user would then just submit the 3PID verification
credentials of the identity server session for login calls similar to
``m.login.email.identity``. THowever, the identity server has no means to
announce which crypto methods it supports.

Instead of providing a cryptographic proof/signature the user could publish the challenge
at a storage location that is only accessible by the user if she is in control of the
public key. The home server could then verify the challenge by accessing this (user-owned)
storage location. This simplifies the verification process for home server a lot but
restricts the user to private/public keys that are associated to decentralized identifiers
with user-owned storage hubs (see for example blockstack's gaia and DID documents
specification).

The new login type is similar to the token login type. However, the verification of the
signature requires an understanding of the proof/signature algorithm for both the server
and client. In view of the interactive authentication flow, the server can announce the
supported login type (supported crypto methods) and the client can choose the login type
(crypto method) of the user's public key.

## Potential issues

* There is no way specified to associate a public key as an administrative account. In
MSC1762 a 3PID is defined that describes decentralized identifiers (DIDs) which come with a
public keys. These could be used in ``account/3pid`` calls. Then the did could be resolved
and the keys could be used for the reference endpoint of public keys as well.

* This login flow is verbose as it uses vocabulary and object types from the W3C CCG, e.g.
the user identifier is specified in property ``identifier`` as well as in the proof as
property ``domain`` as it is specified by the Linked Data Proof document.

* The reference endpoint of public keys does not return a URL/linked document to the owner
of the public key as suggested by the W3C CCG (it returns just the matrix id). Currently,
the matrix protocol has no endpoint to reference the user (i.e. the owner). A reference to
an identity server could be returned for public keys that are associated with decentralized
identifiers (DIDs). The link would be something like 

````
http://localhost:8090/_matrix/identity/api/v1/lookup?medium=did&address=did:stacks:SM34..4A
````
The returned matrix id should be the same as the domain in the proof.

## Security considerations

* The challenge returned from the challenge endpoint should be used only once per user
(within a time window that is sufficient for the login to complete) to repevent so-called
replay attacks.

* The cryptographic proof methods could be weak and bad actors could gain access to the
user's account using vulnerabilities in these methods.

## Conclusion

Adding authentication using public keys is inline with the vision of matrix.org to build an
open, decentralized communication network. The proposed authentication types helps users to
authenticate without using a password or a trusted third-party.