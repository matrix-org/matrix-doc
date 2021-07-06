# MSC3174: Error codes for spam rejections

Some Matrix server implementations, including Synapse, support spam-check filters.
This proposal simply attempts to standardize spam rejection.

## Proposal

### Introduction

A spam-checker may decide to reject a message, a registration attempt, etc. for any
number of reasons. However, while every other rejection from the server has an
error code `M_*`, spam rejections do not have, rather hardcoding a message from the
server.

This has several consequences:

- error messages are hardcoded on the server and cannot be internationalized;
- there is no support for spam-checkers displaying different kinds of rejections
(e.g. "this account is temporarily deactivated pending investigation",
"registrations are temporarily deactivated due to suspicion of DoS",
"this server rejects federation from that server", etc.)

This proposal simply attempts to standardize HTTP responses to spam-check rejections.

The expection is that Matrix servers can adapt their API to take advantage of this
proposal.

### Proposal

1. Add a new error code `M_ANTISPAM_REJECTION`;
2. Any `M_ANTISPAM_REJECTION` error MAY come with a field `kind`, which may contain any of the following values:

    - `m.reject.spam` -- spam has been detected (e.g. message or username is spam);
    - `m.reject.inappropriate` -- unacceptable content has been detected (e.g. a user attempting to register `@deathtojews:...`);
    - `m.reject.investigation` -- account is suspected of being a spambot and is deactivated pending investigation;
    - `m.reject.server` -- federation with this server has been deactivated (e.g. because server is used to send spam);

It is expected that future MSCs will extend the list of possible values for `kind`.

#### Server behavior

The server MAY now issue `M_ANTISPAM_REJECTION` errors.

The server MAY add a field `kind` to `M_ANTISPAM_REJECTION` errors. The server does not have to specify a field `kind`,
typically if the rejection does not fit into any of the possible values for `kind`, or if the spam filter used does not
provide sufficient information to determine a category.

#### Client behavior

The client SHOULD display a human-readable, internationalized error message from `kind`. If `kind` is absent
or if the value of `kind` is not known to the client, the client SHOULD display a generic, internationalized
error message (e.g. "Message rejected by the spam filter").

In particular, in case of `m.reject.investigation` or `m.reject.server`, it SHOULD link to procedures
for appealing the case.


### Alternatives

I can't think of any good alternative at the moment.

### Security considerations

There may be a small security risk that spammers can use the `kind` as an oracle to try and refine spam attacks.
This is considered a minor risk.

## Unstable prefix

All the kinds `m.reject` will initially be prefixed as `org.matrix.msc3174.reject`.
