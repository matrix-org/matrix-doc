# MSC2882: Tempered Transitive Trust

There are many situations in which two people are unable to verify each other
directly, but they both trust a third party to mediate the verification.  For
example, it may be impractical for all employees in a company to verify each
other, but the company may be able to provide a trusted agent who can verify
all employees.

In order to do this, we need to a mechanism for users to share their
verifications with other users.  However, this sharing needs to be done in a
controlled, or tempered, fashion so that we maintain the privacy of a user's
contacts: if Alice has verified Bob, Alice should be able to choose whether she
makes that fact public or not.

In addition, Bob should be able to select which of Alice's public verifications
he wants to trust.  For example, he may wish to trust Alice to verify her
co-workers, but not any other people.

To do this, we introduce one new per-user key for making public attestations on
other users' identities.  We define a new account-data event for storing (via
SSSS) which users to trust for verifying other users.  We also replace the
`POST /keys/signatures/upload` endpoint defined in
[MSC1756](https://github.com/matrix-org/matrix-doc/pull/1756) with an endpoint
that provides more flexibility, and create a new endpoint to delete signatures.

## Proposal

Each user has a new Ed25519 key, a public user signing key, which is used for
making public signatures on other users' master or public user keys.  The
public part of this key can be uploaded to `POST /keys/device_signing/upload`
by using the name `public_user_signing_key`.  When uploaded, it must be signed
with the user's master key, and must have `public-user` in the `usage`
property.  The private part of this key can be stored in the
`m.cross_signig.public_user_signing` account-data using
[SSSS](https://github.com/matrix-org/matrix-doc/pull/1946), using the same
format as the other cross-signing keys.

### Publishing signatures

When Alice wants to publish the fact that she has verified Bob, she will upload
a signature of Bob's master key signed with her public user signing key.
Similarly, she can also publish the fact that she trusts Bob to verify other
people by upload a signature of Bob's public user signing key signed with her
own public user signing key. \[FIXME: Should we have some way for Alice to
indicate who she trusts Bob to verify?\] Signing public user signing keys
allows for multi-hop transitive trust: by publishing the fact that Alice trusts
Bob to verify users and to sign them with a given public user signing key,
Carol can verify with Alice and (if she believes that Alice is a good judge of
character) can then trust the users that Bob has publicly signed.

We introduce a new endpoint, `POST /...FIXME: what name should we use?` for
uploading signatures for devices and cross-signing keys.  The request body has
two parameters, both optional: `public` and `private`.  Both of these
parameters are an mapping of user ID to key ID to signed key.  The signatures
given in the `public` parameter will be made public and may be visible to any
Matrix user, while the signatures given in the `private` parameter will only be
seen by the user who uploaded it.

This endpoint may be used as a replacement for the `POST
/keys/signatures/upload` endpoint defined in
[MSC1756](https://github.com/matrix-org/matrix-doc/pull/1756) by putting
signatures made by the user's self-signing key in `public`, and signatures made
by the user's user-signing key in `private`.  `POST /keys/signatures/upload` is
also now deprecated.

Example:

The example of `POST /keys/signatures/upload` given in MSC1756, with errors
corrected and with a public signature of another user, can be written
instead as:

```json
POST /...?

{
  "public": {
    "@alice:example.com": {
      "HIJKLMN": {
        "user_id": "@alice:example.com",
        "device_id": "HIJKLMN",
        "algorithms": [
          "m.olm.curve25519-aes-sha256",
          "m.megolm.v1.aes-sha"
        ],
        "keys": {
          "curve25519:HIJKLMN": "base64+curve25519+key",
          "ed25519:HIJKLMN": "base64+ed25519+key"
        },
        "signatures": {
          "@alice:example.com": {
            "ed25519:base64+self+signing+public+key": "base64+signature+of+HIJKLMN"
          }
        }
      },
      "base64+master+public+key": {
        "user_id": "@alice:example.com",
        "usage": ["master"],
        "keys": {
          "ed25519:base64+master+public+key": "base64+master+public+key"
        },
        "signatures": {
          "@alice:example.com": {
            "ed25519:HIJKLMN": "base64+signature+of+master+key"
          }
        }
      }
    },
    "@carol:example.com": {
      "carols+base64+master+public+key": {
        "user_id": "@carol:example.com",
        "keys": {
          "ed25519:carols+base64+master+public+key": "carols+base64+master+public+key"
        },
        "usage": ["master"],
        "signatures": {
          "@alice:example.com": {
            "ed25519:alices+base64+public+user+signing+key": "base64+signature"
          }
        }
      }
    }
  },
  "private": {
    "@bob:example.com": {
      "bobs+base64+master+public+key": {
        "user_id": "@bob:example.com",
        "keys": {
          "ed25519:bobs+base64+master+public+key": "bobs+base64+master+public+key"
        },
        "usage": ["master"],
        "signatures": {
          "@alice:example.com": {
            "ed25519:base64+user+signing+public+key": "base64+signature+of+bobs+master+key"
          }
        }
      }
    }
  }
}
```

To avoid abuse by flooding a user's devices/keys with signatures, each user may
only make one public signature on another user's device/key; if they make
another signature, on a device/key, the old signature will be removed.  \[We
should also add a size limit on signatures. ~1KB should be sufficient per
signature.\]

When Alice makes a public signature is made on Bob's device/key, Alice's
homeserver will inform Bob's homeserver of the new signature using an EDU of
type `m.device.signature`. \[FIXME: define the properties.\]

\[FIXME: should we also replace `POST /keys/device_signing/upload` with something
that's more flexible with the key types?  We need to have *some* checking,
since we check that the USK/SSK/PUSK are signed by the master key, so it can't
just be divided into public and private.  But maybe we can have master, public
and private under the assumption that anything that isn't master must be signed
by the master key?\]

### Trusting trust

If Bob wants to trust Alice's signatures for some users, he will store
information in the `m.trust.transitive` event type in account-data.  This
information will be encrypted using SSSS; encryption performs two functions: it
prevents others from seeing who Bob trusts, and it ensures that others cannot
change who Bob trusts since the encryption used by SSSS also authenticates the
data.

\[FIXME: define how `m.trust.transitive` is formatted.  Initial ideas are
something along the lines of having a mapping of trusted users to users that
they are trusted for (e.g. I trust Alice to verify `@carol:matrix.org` and
`*:example.org`), plus a list of exceptions (e.g. even though I said I trust
Alice to verify `*:example.org`, I don't want to trust her for
`@dave:example.org` (e.g. because I have coffee with him regularly and can
easily verify him myself).)  Perhaps we could also do something like "I trust
Alice to verify all the users who are in a given room", which could be helpful
if, e.g. all of a company's employees are in a common company chat room, but
could allow a server admin to lie about someone being in the room so that you
will trust a signature on that user.  Specifying multi-hop trust may be
complicated.\]

## Potential issues

When a user makes their signatures public, this is visible to all Matrix users.
This could be used, for example, to find all the employees of a company by
checking which users have signatures made by the company's agent.

## Alternatives

Rather than classifying signatures as "public" and "private", we could also
have some signatures with a limited distribution, where they will only be seen
by certain people.  This would prevent the issue listed in the "Security
considerations" section, but would increase the complexity.

Rather than replacing `POST /keys/signatures/upload` with a new endpoint, we
could just use the current `POST /keys/signatures/upload` endpoint and have the
server infer the distribution based on the key type.  However, this does not
allow for easy additions of new key types, and increases the complexity of the
server implementation.

## Security considerations

When a user makes their signatures public, this is visible to all Matrix users.
This could be used, for example, to find all the employees of a company by
checking which users have signatures made by the company's agent.

## Unstable prefix

The new endpoints will be prefixed with `/unstable/msc2882` until they land in
a released version of the spec, and event types should be prefixed with
`org.matrix.msc2882.` instead of `m.`.

Clients can discover if a server supports this feature by checking for the
`org.matrix.msc2882` unstable feature flag in `GET /versions`.
