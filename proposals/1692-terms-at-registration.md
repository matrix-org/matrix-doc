# MSC1692: Terms of service at registration

Homeservers may wish to force users to accept a set of policies or otherwise have
users be aware of changes to the terms of service, privacy policy, or other document.
This proposal describes how a server can present these documents during registration
for users to accept before gaining access to the service.

**Note**: This proposal used to contain an entire TOS API for clients to interact with.
This functionality has been moved to [MSC3012](https://github.com/matrix-org/matrix-doc/pull/3012).

## General principles and motivation

* The homeserver should be able to support multiple documents (ie: a TOS, privacy policy,
  and acceptable use policy).
* The policies should be versioned.
* The homeserver should be able to prevent use of the service if a given version of a document
  has not been accepted.

The primary use of this functionality is to address a user experience issue in most clients
where they are not aware of the terms of service until after they've registered. Given the
terms of service can change at any time, having a versioned set of documents is required to
ensure everyone has accepted the updated terms of service. Homeservers should additionally
be able to decide if the given change to their terms of service requires everyone to accept
the new terms or if no action is required by users, though this feature is covered by
[MSC3012](https://github.com/matrix-org/matrix-doc/pull/3012) instead of here.

The version for a policy should be arbitrary and potentially non-linear, similar to room
versions. The acceptable range of characters for a version is `[a-zA-Z0-9.-]`.

## UI authentication changes

This API makes changes to the registration and login flows for UI auth, and makes use of UI
auth at a later stage in this proposal.

### Registration

During registration it may be important to the homeserver that the user accepts a given policy.
This is described as a `m.login.terms` authentication type. The parameters for this authentication
type are:

```json
{
    "policies": {
        "terms_of_service": {
            "version": "1.2",
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-1.2-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-1.2-fr.html"
            }
        },
        "privacy_policy": {
            "version": "1.2",
            "en": {
                "name": "Privacy Policy",
                "url": "https://example.org/somewhere/privacy-1.2-en.html"
            },
            "fr": {
                "name": "Politique de confidentialité",
                "url": "https://example.org/somewhere/privacy-1.2-fr.html"
            }
        }
    }
}
```

Policies have a unique identifer represented by the key under `policies`. The `version` is
provided as a convience to the client, and is alongside the different language options for
each of the policies. The `name` of a policy is human-readable name for the document. The
`url` may point to any location. The implicit ID may only contain characters in `[a-zA-Z0-9_]`.

Policies supplied via this method are implied to be required and therefore blocking for the
registration to continue.

The client is not required to supply any additional information in the auth dict to complete
this stage. The client should present the user with a checkbox to accept each policy with a
link to said policy, or otherwise rely on the homeserver's fallback.
