# Proposal to add DIDs and DID names as admin accounts

Distributed Identifiers (DIDs) are defined as 3PIDs in [MSC
1762](https://github.com/matrix-org/matrix-doc/pull/1762). Furthermore, a method
to login with cryptographic keys is defined in [MSC
1768](https://github.com/matrix-org/matrix-doc/pull/1768).

This MSC brings both parts together.

Adding DIDs as administrative accounts enables the user to login using the
public keys associated with their DID or DID name.

## Proposal

A Distributed Identifier (DID) is a user-owned identifier that allows
third-parties to proof the ownership of the DID using cryptographic methods.
There are different DID methods, some of them provide human-friendly names, here
called DID names. This removes dependencies to other communication methods like
email protocol. 

In order to use DIDs and DID names as admin accounts the ``medium`` parameter in
the API calls for the administrative accounts should be extended to ``m.did``
and to the class of human-friendly names ``m.did.*``. At the time of writing
only ``m.did.stack`` and ``m.did.erc725`` is defined.

The extension of the enum applies to section 5.6.1, 5.6.3 of the
[Specification](https://matrix.org/docs/spec/client_server/r0.4.0.html#adding-account-administrative-contact-information).

## Tradeoffs

## Potential issues

Implementation could rely on the restricted enum for ``medium`` to two elements.


The specification states that these information are contact information.
However, there are only suggestion in the DID standard how to define
communication ways for DIDs or DID names using [DID service
endpoints](https://w3c-ccg.github.io/did-spec/#service-endpoints). 

## Security considerations


## Conclusion

With this proposal, DIDs and DIDs names can be used for login.