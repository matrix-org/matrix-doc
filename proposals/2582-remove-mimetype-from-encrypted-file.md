# Remove `mimetype` from `EncryptedFile` object


## Proposal
The example in the spec currently lists `mimetype` in the examples for `EncryptedFile` but not in
the object definition. As that is duplicate information of the `info` block of file events, the
mimetype should just be removed alltogether.


## Potential issues
Some clients might depend on this?
