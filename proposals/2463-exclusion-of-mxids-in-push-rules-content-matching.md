# MSC2463: Exclusion of MXIDs in push rules content matching

Currently, push notifications for mentions and highlights are computed by checking whether the user's display name,
username or custom keywords are sub-words of a message's content body. Because those tokens may be part of another
user's MXID, unintended notifications are being generated.

This problem is particularly apparent when someone's name is an infix word of someone else's. In this situation,
`@pierre:somedomain.tld` is notified every time a message is addressed to `@jean.pierre:otherdomain.tld` in rooms they
share. This includes all quotes and replies to the latter's messages. Even worse, a server owner whose username is part
of the hosting domain is notified for every message and reply mentionning anyone on the same homeserver.


## Proposal

While it is tricky to prevent all forms of unintended mentions, the explicit ones taking the form of whole MXIDs should
be interpreted correctly and generate notifications only for the explicitly targeted user.

To ensure this, it is proposed:

* to exclude MXIDs from the search buffer when looking for patterns in the content of messages, and
* to handle whole MXIDs separately.

This change will affect the push module of the client-server API and require changes in both homeserver and client
implementations, which are the respective components in charge of computing notifications for unencrypted and
end-to-end encrypted rooms.


## Potential issues

None.


## Alternatives

### Excluding rendered objects

String objects whose form is rendered before being presented to the user, such as hyperlinks in addition to MXIDs,
could be candidate for exclusion from notifications. This would require some kind of interpretation on the server's
side to filter out what would be visible or not once rendered by clients. Restrictions on acceptable formats (Markdown,
HTML, ...) would be needed. It would also be hard to determine the displayed and hidden parts of the content as the
rendering behaviour might differ from one client application to another.


### Excluding common known objects

Other common string objects, such as URLs and email addresses, could be candidate for exclusion from notifications as
well. However, some users may actually want to be notified when some URL linking to their personal page is being shared
for instance. This is different from MXIDs which already constitute explicit mentions on their own with no ambiguity.


## Security considerations

None.
