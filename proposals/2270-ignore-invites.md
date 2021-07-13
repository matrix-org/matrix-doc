# Proposal for ignoring invites

## Problem

There is currently no way to ignore an invite in Matrix without explicitly
rejecting it and informing the inviter of the rejection. There are many social
situations where a user may want to silently ignore the invite instead.

The closest you can currently get is to ignore the user who sent the invite -
but this will then ignore all activity from that user, which may not be
desirable.

## Solution

Currently we support ignoring users by maintaining an `m.ignored_user_list` event in
account_data, as per https://matrix.org/docs/spec/client_server/r0.5.0#id189.

We could do also silently ignore rooms (including invites) with an equivalent
`m.ignored_room_list` event, with precisely the same semantics but listing
room IDs rather than user IDs.

## Tradeoffs

 * We're limited to ~65KB worth of room IDs (although we could change the
   limits for account_data 'events', given they're more freeform JSON than
   events)
 * We waste initial sync bandwidth with account_data info for ignored rooms
   which we may never care about ever again.
 * The list will grow unbounded over time (unless the user occasionally
   unignores and explicitly rejects the invites), especially if invite spam
   accelerates.
 * We could instead have a dedicated API for this:
   * `PUT /user/{userId}/ignore/{txnId}`
   * `PUT /rooms/{roomId}/ignore/{txnId}`
   * `GET /user/{userId}/ignore`
   * `GET /rooms/{roomId}/ignore`
   * `GET /ignore` (for querying the current lists)
   * ...and a custom block in `/sync` responses to synchronise ignore changes
   * ...except it feels that yet another custom API & custom response block
     is even more complicated and clunky than making account_data a bit more
     flexible.
 * Alternatively, we could extend `/leave` with a `silent` parameter of some kind,
   and rely on the invitee's HS to track these 'silent' leaves and ignore the
   room on behalf of the invitee.  However, it may be nice to let the user track
   ignored invites cross-client so they can undo if necessary, which account_data
   gives us for free.  Plus semantically it seems a bit wrong to use `/leave`
   to describe the act of ignoring an invite, when you're not actually leaving it.