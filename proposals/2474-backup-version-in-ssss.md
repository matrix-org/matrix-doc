# Add key backup version to SSSS account data

[MSC1219](https://github.com/matrix-org/matrix-doc/issues/1219) introduces a
method to store megolm keys on the server.  The decryption keys are encrypted
so that server administrators cannot read them.  The recovery key, to decrypt
the megolm keys, can be stored using
[MSC1946](https://github.com/matrix-org/matrix-doc/issues/1946).  However, this
currently does not include the backup version.  Since the Secure Secret Storage
data is managed separately from the backup data, the two get out of sync.  For
example, a client could create a new backup without storing a new backup key.

We propose to add an unencrypted `version` field to the Secret Storage data, so
that clients will know if the stored key matches the backup version.


## Proposal

When the recovery key for a key backup is saved using MSC1946, clients may
include an unencrypted `version` field in the `m.megolm_backup.v1`
account-data.  For example, if the recovery key for backup version `1` is
encrypted using a key with ID `key_id`, the `m.megolm_backup.v1` account-data
could look like:

```json
{
  "version": "1",
  "encrypted": {
    "key_id": {
      "iv": "foo",
      "ciphertext": "bar",
      "mac": "baz"
    }
  }
}
```

When clients see this field, they can use it to determine which backup version
it is for.
