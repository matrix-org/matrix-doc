# MSC3012: Post-registration terms of service API

[MSC1692](https://github.com/matrix-org/matrix-doc/pull/1692) introduces a concept of "terms of service"
for new users to accept during registration, though does not deal with the problem of terms changing.
Originally the MSC did handle such behaviour, however the proposed solution wasn't quite worked out well
enough and thus has been broken out here for review. As of writing, server operators have been operating
okay with MSC1692's core functionality without this MSC's proposed solution to terms changing after
registration.

## Proposal

See [MSC1692](https://github.com/matrix-org/matrix-doc/pull/1692) for details on the guiding principles
and goals of this MSC - they are the same. MSC1692 also defines a lot of the structure which leads into
this MSC.

### Login

Given the Client-Server specification doesn't use UI auth on the login routes, mimicking the
process used for registration is more difficult. The homeserver would not be aware of who is
logging in prior to the user submitting their details (eg: token, password, etc) and therefore
cannot provide exact details on which policies the user must accept as part of the initial login
process. Instead, the login endpoints should be brought closer to how UI auth works using the
following process:

1. The client requests the login flows (unchanged behaviour) - policies are not referenced yet.
2. The client submits the user's details (eg: password) to the homeserver (unchanged behaviour).
3. If the credentials are valid, the homeserver checks if the user has any required policies to
   accept. If the user does not have any pending policies, skip to step 6.
4. The homeserver responds with a 401 as per the UI auth requirements (an `errcode` of `M_FORBIDDEN`
   and `error` saying something like `"Please accept the terms and conditions"`). The `completed`
   stages would have the user's already-accepted step listed (eg: `m.login.password`). The
   `m.login.terms` authentication type shares the same data structure as the one used during
   registration.
5. The client submits the request again as if it were following the UI auth requirements (ie: for
   the purpose of `m.login.terms`, submitting an empty auth dict).
6. The homeserver logs the user in by generating a token and returning it to the client as per
   the specification.

This process is chosen to begin introducing the UI auth mechanism to login without breaking clients.
In the future, the login endpoints should be migrated fully to use UI auth instead of a different
approach. By nature of having the homeserver return a 401 when the user must accept terms before
continuing, older clients will not be able to work around the limitation. Modern clients would be
expected to support the UI auth flow (after the initial password submission), therefore allowing
the user to actually log in.

## Asking for acceptance after login/registration

The homeserver should maintain a read-only `m.terms` account data event with `content` similar
to:

```json
{
    "accepted": {
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
    },
    "pending": {
        "terms_of_service": {
            "version": "2.0",
            "required": true,
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-2.0-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-2.0-fr.html"
            }
        },
        "code_of_conduct": {
            "version": "1.0",
            "required": false,
            "en": {
                "name": "Code of Conduct",
                "url": "https://example.org/somewhere/code-of-conduct-1.0-en.html"
            },
            "fr": {
                "name": "Code de conduite",
                "url": "https://example.org/somewhere/code-of-conduct-1.0-fr.html"
            }
        }
    }
}
```

In this example, the user has already accepted the Terms of Service v1.2 and Privacy Policy v1.2,
but has not signed the new Terms of Service or accepted the Code of Conduct. This provides homeservers
with a way to communicate new policies as well as updates to policies. Because the `name` is unique
amongst policies, the client can determine whether a policy is being updated or introduced. The
homeserver will push this account data event to the client as it would for any other account data
event.

*Note*: [MSC2140](https://github.com/matrix-org/matrix-doc/pull/2140) requires the client to treat
URLs for policies returned by this API to be de-duplicated. The expectation is that clients will
continue to use this terms of service API to manage approval of policies with their homeserver and
consider duplicated policies from the identity server/integration manager where appropriate. Ultimately,
the client may end up making several requests to all 3 servers despite only rendering a single
checkbox for the user to click. This only applies to a post-MSC2140 world and does not otherwise
affect this proposal.

The `required` boolean indicates whether the homeserver is going to prevent use of the account (without
logging the user out) by responding with a 401 `M_TERMS_NOT_SIGNED` error, including setting a `soft_logout`
flag as per [MSC1466](https://github.com/matrix-org/matrix-doc/issues/1466). Clients should not log
out the user if they understand the error code, instead opting to prompt the user to accept the new
policies required by the homeserver. The error will include an additional `policies` property like in
the following example:

```json
{
    "errcode": "M_TERMS_NOT_SIGNED",
    "error": "Please sign the terms of service",
    "soft_logout": true,
    "policies": {
        "terms_of_service": {
            "version": "2.0",
            "en": {
                "name": "Terms of Service",
                "url": "https://example.org/somewhere/terms-2.0-en.html"
            },
            "fr": {
                "name": "Conditions d'utilisation",
                "url": "https://example.org/somewhere/terms-2.0-fr.html"
            }
        }
    }
}
```

The homeserver should not prevent the use of `/sync` (and similar endpoints) but may withhold any
event that is not an update to the `m.terms` account data event. If a server is witholding events,
it MUST set `withheld: true` as a top level field in the sync response. This is to ensure
that clients are not left in the dark when another client for the user accepts the terms of service,
or when the user accepts the terms elsewhere.

*Note*: `withheld` was chosen over `limited` due to `limited` already having special meaning in
the context of sync.

In addition, the homeserver should not prevent the use of the special "terms acceptance" API
described in the next section.

### Terms acceptance API

One way to accept the terms of service is to force the user to log in again, however that is
likely to be less than desireable for most users. Instead, the client may make a request to
`/_matrix/client/r0/terms` using the user-interactive authentication approach with a valid
access token. The homeserver may decide which additional stages it wants the user to complete
but must at least include the `m.login.terms` stage in every flow. The authentication type's
behaviour is exactly the same as how it works for registering an account: the policies the
homeserver wants the user to accept are provided as the parameters for the stage, which should
include policies that are `"required": false` in the user's account data. This is because the
same API is used by the client to acknowledge a non-blocking policy (such as the Code of Conduct
in the prior example).

## Why use account data and not a special /sync property or polling API?

The user's account data was picked because (almost) every client is aware of the concept and
requires few changes to support it. Many clients additionally have optimized the lookup for
account data via caching, making the information essentially always available. If
[MSC1339](https://github.com/matrix-org/matrix-doc/issues/1339) were to be approved, this
lookup becomes even easier.

Clients are almost certainly going to want to show the information somewhere in their UI,
sometimes due to a legal requirement. The information should therefore be easily accessible.

A special key in `/sync` was not picked because it leads to clients having to support yet
another field on the sync response. It would also require clients that don't sync to sync,
which should not be the case (although currently they would until MSC1339 lands anyways).

A dedicated API for the client to poll against was also not picked due to similar reasons.
The client shouldn't have to poll yet another API just for policies.
