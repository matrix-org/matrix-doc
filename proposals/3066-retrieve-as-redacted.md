# MSC3066: Retrieve as Redacted

In some cases, we want to debug our servers or provide data to enforcement agencies with some fields
redacted. This proposal seeks to standardise the API endpoints for serving those redacted events. This
is a different concept from event redaction, which instructs all other participants to delete some
fields of those events.

## Proposal

This only applies to reads. Write results cannot have fields redacted using this method.

To retrieve events with fields redacted, the query parameter `filter` shall be set as an array of 
strings denoting URL-encoded JSON keys. The server will then return a response comprising of the event
with those fields filtered out.

## Potential issues

Draft

## Alternatives

Draft

## Security considerations

No adverse security problems.

## Unstable prefix

No implementations yet.
