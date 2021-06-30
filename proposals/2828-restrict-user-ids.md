# Proposal to restrict allowed user IDs over federation
Currently the spec has [an appendix specifying allowed user ID grammar](https://matrix.org/docs/spec/appendices#user-identifiers).
The spec makes it seem like user IDs can only consist of printable ASCII
characters, excluding space and `:`. However, the user ID grammar is not
actually a part of the event authorization rules, meaning most server
implementations will accept user IDs with arbitrary unicode characters.

Synapse and Dendrite will accept arbitrary unicode, while Construct and Conduit
believed the spec appendix.

## Proposal
The proposed solution is applying the historical user ID grammar in step 5 of
the room v1 event authorization rules. A new step is added between 5.a. and 5.b.:

> If the localpart of the user ID in the `state_key` contains characters not
  allowed by the `extended_user_id_char` grammar, reject.

  ```bnf
  extended_user_id_char = %x21-39 / %x3B-7E  ; all ascii printing chars except : and space
  ```

The changes are applied on top of room v6.

## Note about the user ID grammar spec
The user ID grammar spec appendix needs to be updated to mention that room
versions prior to this new version can contain arbitrary unicode user IDs,
so clients and servers must be able to handle such users.

## Alternatives
### Don't restrict user IDs
We could simply add the note about arbitrary unicode being allowed, and not
create a new room version that restricts user IDs in event auth. Something like
[MSC1228](https://github.com/matrix-org/matrix-doc/pull/1228) will eventually
overhaul the entire user ID system anyway.

## Potential issues
Existing users with user IDs outside the historical user ID grammar would be
unable to join rooms after this new room version. However, there shouldn't be
any actual users with such user IDs, as normal registrations have always
required usernames to follow the historical grammar.

## Unstable prefix
Implementations can use `net.maunium.msc2828` as the room version until this
proposal is added to an official room version.
