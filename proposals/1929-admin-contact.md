# MSC 1929 Homeserver Admin Contact and Support page

Currently, contacting a homeserver admin is difficult because you need to have insider knowledge
of who the admin actually is. This proposal aims to fix that by specifying a way to add contact details
of admins, as well as a link to a support page for users who are having issues with the service.

This proposal aims to fix https://github.com/matrix-org/matrix-doc/issues/484

## Proposal

The proposal suggests adding a new endpoint: `.well-known/matrix/support`.

The response format should be:

```javascript
{
    admins: [{
        matrix_id: "@admin:domain.tld",
        email_address: "admin@domain.tld",
        role: "admin" # If omitted, the default will be "admin"
    },
    {
        email_address: "security@domain.tld",
        role: "security"
    }],
    support_page: "https://domain.tld/support.html"
}
```

The `matrix_id` and `email_address` do NOT need to have the same domain as the homeserver. It is expected that
an admin will have a "backup" contact address if the server is down, like an email or alternative mxid on a different homeserver.

Entries may have a `matrix_id` OR an `email_address`, but at least one MUST be specified.

`role` is an informal description of what the address(es) are used for. The only two specified in this
proposal are "admin" and "security." Admins are a catchall user for any queries, where security is intended
for sensitive requests.

`admins` is optional, but recommended.

`support_page` is an optional property to specify a affiliated page of the homserver to give users help
specific to the homeserver, like extra login/registration steps.

## Alternative solutions

Hardcode a given user localpart that should be used as an admin address.
 - The account would need to either internally redirect messages intended for @admin:domain.tld to another account(s)
 - OR require an admin to regularly sign into this special account to check for messages. Neither of which is useful.

Specify the same content inside a homeserver endpoint, rather than use `.well-known`.
 - This requires the homeserver to be up or responsive, which might be not very useful if trying to report issues with
   connectivity.
   
Use vCards.
 - vCards would add bloat, as the vast majority of a vcards contents is not useful for contacting an admin.

## Security considerations

If the host is compromised, any information could be specified in the well known file which may direct users to send
sensitive information to a malicious user.
