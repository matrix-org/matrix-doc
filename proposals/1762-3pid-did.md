# Proposal to support user-owned identifiers as 3rd party identifiers (3PID)

Email and phone numbers are well-established third party identifiers (3PID). The
verification that a user owns such an identifiers is usually done by sending an
email or SMS. The finalization of the verification requires interaction from the
user. With the advances in blockchain technologies, so-called user-owned or
"distributed identifiers" (DID) have been established that are created, owned
and controlled by the person herself. Third-parties can verify the ownership of
DIDs by verifying cryptographic signatures using public/private key pairs
associated with these DIDs. 

For the matrix protocol, this means 

* that DIDs can be associated and verified with a user account, and 
* that autentication can be done with the matrix username, 3PID and a signature only,
  without using the user's password similar to [email based authentication via
  identity
  server](https://matrix.org/docs/spec/client_server/r0.4.0.html#email-based-identity-server).
  

Both aspects should be defined in separate MSCs and are mentioned as motivation
why DIDs are a good candidate for a new 3PID type.

While DIDs are not human-friendly identifiers by definition there are some DID
methods that associate a human-friendly id to DIDs. These ids/names should be used
to lookup matrix users through the identity servers as well (in addition to
using DIDs for lookup).

## Proposal

During the last year decentralized identifiers have been standardized by the
[W3C Credentials Community Group](https://w3c-ccg.github.io) (CCG). There exists
several methods to create DIDs. A list of these methods is maintained by the
[CCG Method Registry](https://w3c-ccg.github.io/did-method-registry). The group
also defines standards to describe properties of identifiers, in particular how
to verify ownership of DIDs.

Supporting DIDs as a new 3PID type opens the matrix network to users that are
using DIDs, enables applications with control over DIDs to communicate across
the borders of DID methods, e.g. connect users with a blockstack.org account
(did:stacks:..) to users with sovrin.org accounts (did:sov:..) and to users that
do not have any DID but a matrix account. 

DIDs should be defined as a new 3PID type. The medium should be defined as
``m.did``. The address should contains the DID in normalized form as [defined by
the W3C CCG](https://w3c-ccg.github.io/did-spec/#normalization).

Example (for address
[15gxXgJyT5tM5A4Cbx99nwccynHYsBouzr](https://core.blockstack.org/v1/dids/did:stack:v0:15gxXgJyT5tM5A4Cbx99nwccynHYsBouzr-0)):

```
{ 
    medium: "m.did",
    address: "did:stack:v0:15gxXgJyT5tM5A4Cbx99nwccynHYsBouzr-0"
}
```
Furthermore, extensions of the 3PID type ``m.did`` should be defined for DID
methods that support human-friendly names. The type should consist of ``m.did.``
followed by the DID methods as defined in the [DID name
registry](https://w3c-ccg.github.io/did-method-registry/). In particular the
following two should be added (more could be added in separate MSCs):
* ``m.did.stack`` for names associated with a DID that starts with
  ``did:stack:``
* ``m.did.erc725`` for names associated with a DID that starts with
  ``did:erc725:``


The address of these types are the names in the corresponding DID namespace. The
names can be resolved to DIDs using a resolver method defined by the DID method.

Example (resolves to the [same public
key](https://core.blockstack.org/v1/users/judecnelson.id) as the example above):
````
{ 
    medium: "m.did.stack",
    address: "judecnelson.id"
}
````
## Tradeoffs

Instead of adding a new type of 3PID, DID could be defined as a new identifier
type (e.g. ``m.id.did``) as the user has created the DID herself, is in control
of it and can be used for authentication. However, DIDs in general and DID
methods in particular define their own namespaces that matches the concept of
3PID very well. Users make use of their DIDs in other context, e.g.
decentralized apps and might have an interest to make use of them in the
context of matrix as well as other users (or apps) know already the user's DID or the user's human-friendly name associated with the DID.

Furthermore, a new 3PID could be defined for each DID methods like
``m.did.stack`` or ``m.did.btcr``. However, it is not clear which methods will
be defined in the future and the DID method can also be derived from the address
if needed. Therefore, it is not necessary to distinguish mediums for all
different methods.

## Potential issues

More DID methods might provide human friendly names.

## Security considerations

Associating DIDs with email or phone number could have unwanted privacy
implications for the user. However, the user is free to choose which DID she
wants to publish or whether to publish one at all.

## Conclusion

Adding support for decentralized identifiers is inline with the vision of
matrix.org to build an open, decentralized communication network. The proposed
new 3PID type helps users to include their DID as they are used to in other
decentralized apps and as they are used to with email and phone numbers. With
their cryptographic properties DIDs have the potential to provide a new,
password-less, decentralized authentication flow.

