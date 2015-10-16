Third party invites
===================

.. _module:third_party_invites:

This module adds in support for inviting new members to a room where their
Matrix user ID is not known, instead addressing them by a third party identifier
such as an email address.

There are two flows here; one if a Matrix user ID is known for the third party
identifier, and one if not. Either way, the client calls ``/invite`` with the
details of the third party identifier.

The homeserver asks the identity server whether a Matrix user ID is known for
that identifier. If it is, an invite is simply issued for that user.

If it is not, the homeserver asks the identity server to record the details of
the invitation, and to notify the client of this pending invitation if it gets
a binding for this identifier in the future. The identity server returns a token
and public key to the homeserver.

If a client then tries to join the room in the future, it will be allowed to if
it presents both the token, and a signature of that token from the identity
server which can be verified with the public key.

Events
------

{{m_room_third_party_invite_event}}

Client behaviour
----------------

A client asks a server to invite a user by their third party identifier.

Server behaviour
----------------

All homeservers MUST verify that sig(``token``, ``public_key``) = ``signature``,
where ``signature`` is the only signature in the ``signatures`` property.

If a client of the current homeserver is joining by an
``m.room.third_party_invite``, that homesever MUST validate that the public
key used for signing is still valid, by checking ``key_validity_url``. It does
this by making an HTTP GET request to ``key_validity_url``:

.. TODO: Link to identity server spec when it exists

Schema::

    => GET $key_validity_url?public_key=$public_key
    <= HTTP/1.1 200 OK
    {
        "valid": true|false
    }


Example::

    key_validity_url = https://identity.server/is_valid
    public_key = ALJWLAFQfqffQHFqFfeqFUOEHf4AIHfefh4
    => GET https://identity.server/is_valid?public_key=ALJWLAFQfqffQHFqFfeqFUOEHf4AIHfefh4
    <= HTTP/1.1 200 OK
    {
        "valid": true
    }

with the querystring
?public_key=``public_key``. A JSON object will be returned.
The invitation is valid if the object contains a key named ``valid`` which is
``true``. Otherwise, the invitation MUST be rejected. This request is
idempotent and may be retried by the homeserver.

If a homeserver is joining a room for the first time because of an
``m.room.third_party_invite``, the server which is already participating in the
room (which is chosen as per the standard server-server specification) MUST
validate that the public key used for signing is still valid, by checking
``key_validity_url`` in the above described way.

No other homeservers may reject the joining of the room on the basis of
``key_validity_url``, this is so that all homeservers have a consistent view of
the room. They may, however, indicate to their clients that a member's'
membership is questionable.

For example:

    If room R has two participating homeservers, H1, H2

    And user A on H1 invites a third party identifier to room R

    H1 asks the identity server for a binding to a Matrix user ID, and has none,
    so issues an ``m.room.third_party_invite`` event to the room.

    When the third party user validates their identity, they are told about the
    invite, and ask their homeserver, H3, to join the room.

    H3 validates that sign(``token``, ``public_key``) = ``signature``, and may check
    ``key_validity_url``.

    H3 then asks H1 to join it to the room. H1 *must* validate that
    sign(``token``, ``public_key``) = ``signature`` *and* check ``key_validity_url``.

    Having validated these things, H1 writes the join event to the room, and H3
    begins participating in the room. H2 *must* accept this event.

The reason that no other homeserver may reject the event based on checking
``key_validity_url`` is that we must ensure event acceptance is deterministic.
If some other participating server doesn't have a network path to the keyserver,
or if the keyserver were to go offline, or revoke its keys, that other server
would reject the event and cause the participating servers' graphs to diverge.
This relies on participating servers trusting each other, but that trust is
already implied by the server-server protocol. Also, the public key signature
verification must still be performed, so the attack surface here is minimized.

