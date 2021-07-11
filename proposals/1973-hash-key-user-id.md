# Hash Key User ID

Trust-less federation of client keys via hash in User ID.

## Proposal

During signature verification, if the User ID matches the following pattern: `[a-z2-7]{16}//`

Then decode it as: `base32(SHA3-PREFIX)//`

Where:
  - SHA3-PREFIX is first 80 bits of the SHA3-256 of the users public key
  - `//` is the 'magic string' identifier to differentiate from normal User IDs

Verify that the SHA3 hash matches for all given signatures.

e.g.
```json
"signatures": {
  "@xmh57jrzrnw6insl//:example.com": {
    "ed25519:JLAFKJWSCS": "dSO80A01XiigH3uBiDVx/EjzaoycHcjq9lfQX0uWsqxl2giMIiSPR8a4d291W1ihKJL/a+myXS367WT6NAIcBA"
  }
}
```

This scheme is inspired by Tor [rend-spec v2](https://github.com/torproject/torspec/blob/master/rend-spec-v2.txt).

This addresses [13.11.2 Device verification](https://matrix.org/docs/spec/client_server/r0.4.0.html#device-verification).

## Tradeoffs

Another solution would be to embed the Ed25519 key in the User ID, a la Tor [rend-spec v3](https://gitweb.torproject.org/torspec.git/tree/rend-spec-v3.txt). However this would not support other key types and is much longer.

## Potential issues

This requires clients to synchronize their keys across devices, which can be dangerous.

There is potential for conflicts with legitimate user names, however the `//` 'magic string' exists to mitigate this to some extent.

The `//` magic string might trip-up client parsing (maybe?), alternatives could be `--`, `==`, `..`, etc.

## Security considerations

80 bits is probably sufficient (see Tor) to prevent impersonation. Keep in mind that a collision must be found while also generating a valid private key.

## Conclusion

This proposal allows the use of untrustworthy federation servers without manually verifying device lists and keys.
