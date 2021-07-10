# MSC2870: Protect server ACLs from redaction

[Server ACLs](https://matrix.org/docs/spec/client_server/r0.6.1#server-access-control-lists-acls-for-rooms)
are a way to prevent malicious/untrusted homeservers from participating in a given room. These ACLs
are represented by a state event which is easily capable of demolishing all useful functionality of
a federated room. Typically this sort of design flaw would be worked out during the MSC process, and
in this particular case it was acknowledged as a potential source of accidental mistake, however the
impact of making a mistake appears to be larger than anticipated.

Specifically, the ACLs do not default to allowing all servers when they are set but missing an `allow`
field. When an `allow` rule is missing, it means that all servers can no longer participate in the
room. The natural reaction to such a disaster is to try sending a new ACL event, however all the
receiving servers rightly refuse the event because the specification says so and it's not yet
possible to tell if a trusted server is publishing the new ACLs (due to the social nature of the
problem space rather than the technical side). Redacting a server ACL event causes the event content
to become `{}`, which means no `allow` rule is present.

## Proposal

In a future room version, the `allow`, `deny`, and `allow_ip_literals` fields of the `m.room.server_acl`
state event are protected from redaction. Typically this measure is only taken when a field is critical
to the operation of the protocol, such as in the case of protecting power levels from redactions. ACLs
are not as critical to the protocol as most of the other protected event fields, however the consequences
of accidentally redacting a server ACL event are disproportionately large.

## Potential issues

None foreseen - this MSC should remedy a problem encountered in the wild.

## Alternatives

We could instead dictate that a lack of `allow` rule implicitly means `allow: ["*"]`, however this is
a behavioural change which is easily missed between room versions. We could also define that `{}` means
applying the same mechanics of ACLs when the state event isn't set, however again this is subject to
being missed as a behavioural change. Behavioural changes are hard to represent in the specification as
room versions are not meant to contain information about how a room might react in the eyes of a room
administrator or client implementation, where possible. They are more intended to change server-side
algorithms, like the redaction algorithm, to change the functionality under the hood without impacting
the room administrator's understanding of their room's function.

## Security considerations

It may be desirable to redact server ACLs due to abusive server names needing to be banned. Clients
are encouraged to *not* display the differences to the ACLs without the user opting in to seeing the
changes (such as by clicking a 'show details' link).

## Unstable prefix

Implementations looking to test this MSC before it lands in a released room version can use `org.matrix.msc2870`
as the room version.
