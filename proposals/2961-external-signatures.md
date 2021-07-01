# MSC2961: External Signatures

It isn't always possible to meet up in a safe environment to verify the person you are communicating
with. Instead, you might want to trust a PGP signature of someone's master key, some official company
signature, a national ID signature or many more.

It would be also thinkable that, in combination with [MSC2882](https://github.com/matrix-org/matrix-doc/pull/2882)
some company could make a signature for a "Trust Management" team of a company, and thus, if you can
verify those signatures, you can know if people in said company are trusted.

In short, there are many reasons for having custom signatures attached to ones (master)key, but currently
only matrix-internal signatures are allowed. This proposal aims at adding a general format to allow
any kind of signature in the future, be it a custom namespaced one for a specific application, or a
future MSC introducing PGP signatures or the like.

## Proposal

Custom signatures are added in the `signatures` block of anything that is signable (key objects, with
[MSC2757](https://github.com/matrix-org/matrix-doc/pull/2757) events, etc.). To differentiate them
from matrix-internal signatures their key IDs are prefixed with `custom:`, followed by their algorithm
identifier. The algorithm identifier is a reverse-URI as per [MSC2758](https://github.com/matrix-org/matrix-doc/pull/2758).
Optionally, some additional key id, separated with a colon, is used. This key maps to a string or a
json object, which describes the signature. As such, these all are possible examples of a signatures
block:

```json
"signatures": {
  "@alice:example.org": {
    "custom:org.openpgp.signature:pubkey+of+pgp+key": "signature+of+pgp+key"
  }
}
```

```json
"signatures": {
  "@alice:example.org": {
    "custom:org.example.custom": {
      "signature": "some+custom+signature",
      "expiracy": "2021-10-15"
    }
  }
}
```
Note that in this example there is no key ID, and the signature part is an object. An expiracy here
could be done safely, as this MSC does not describe how algorithms create their signature. As such,
it is thinkable that, instead of just using the canonical json of the object to sign, the expiracy is
appended.

### Uploading and visibility of device signatures
Due to the nature of custom signatures, it is impossible for the server to actually validate the
signatures. Thus, the server is expected to just store them, without doing any extra validation.

To actually upload the signature of a device, post it, such as with other cross-signing signatures,
to `POST /_matrix/client/r0/keys/signatures/upload`. The custom signatures are expected to be visible
to everyone who queries your key.

If [MSC2822](https://github.com/matrix-org/matrix-doc/pull/2882) lands before this MSC, then signature
visibility is controlled by presence in the `public` / `private` objects and the signatures are uploaded
via the method specified in that MSC.

### Size constraints
(is this paragraph reasonable?)
As one could easily clog up the server by just adding overly huge signatures, a size constraint of
2048 (is this reasonable?) is introduced. The size is calculated by taking the key id and concatenating
the signature / canonical json of the signature, and then the string length is used.

## Potential issues

Too many signatures could severely bloat the size of key objects. That is why the size constraint is
introduced, to keep things reasonable.

## Alternatives

Instead of allowing the signature to be either a string or an object, this MSC could allow it to be
only a string. That, however, is bound to be abused eventually by just putting json in there, which
is kinda hacky.

## Security considerations

It might be desirable to unpublish a custom signature you made, as you might not want to be associated
with e.g. a certain service anymore. A future MSC can introduce unpublishing signatures.
