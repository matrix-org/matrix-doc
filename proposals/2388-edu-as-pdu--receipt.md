# MSC2388 - Read-Receipt PDU type

### Background

Receipts are a feature in Matrix intended for clients to acknowledge a message. The only type of
receipt at present is the m.read read-receipt for when the user has seen a message. This feature
is specified as an EDU such that the reliability of their transmission is not guaranteed and there
is no record of them. They were designed this way because an order of magnitude more receipts are
expected by this system than other PDU messages.

### Problem

In practice, implementations treat read-receipt EDU's no different than other PDU messages. Upon
reception they must be persisted for effective client synchronization. Implementations also employ
additional complexity to transmit prior EDU's to other servers long after they were received.
These implementation choices were made to provide a consistent, expected user experience, where
the same receipts render the same for everyone. That consistency is beneficial to the social
atmosphere.

### Solution

We specify the Event type m.receipt. Within the content of this event, an m.relates_to with a
rel_type of m.read provides and replaces the functionality of the existing receipt EDU.
