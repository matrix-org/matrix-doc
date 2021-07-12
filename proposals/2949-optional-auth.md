# Proposal to clarify "Requires auth" and "Rate-limited" in the spec
All endpoints in the spec have values for "Requires auth" and "Rate-limited".
The values are booleans, and the spec does not say how strictly they should be
interpreted. There are already multiple endpoints, such as [GET /publicRooms],
which don't require auth in the spec, but may require auth in [some server
implementations].

[GET /publicRooms]: https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-publicrooms
[some server implementations]: https://github.com/matrix-org/synapse/blob/v1.24.0/docs/sample_config.yaml#L103-L107

This ambiguity and inconsistency causes problems when client developers read
the values in the spec as requirements and don't pass authentication even when
they have a valid access token (see [ruma/ruma#380]).

[ruma/ruma#380]: https://github.com/ruma/ruma/issues/380

Inconsistencies in the "Rate-limited" value doesn't have consequences that are
as obvious, but it is a similar problem nevertheless: Synapse has rate limits
on multiple endpoints that are marked as not rate limited in the spec.

## Proposal
1. Make it clear that the rate-limited and requires auth values in the spec are
   merely recommendations and the actual rate limits and auth requirements may
   vary on different servers.
2. Recommend that clients always include authorization in requests to the
   homeserver if they have an access token.

## Potential issues
None that I can think of.

## Security considerations
None that I can think of.

## Alternatives
* Add a "maybe" value for "Requires auth" and define that any yes/no value is a
  requirement instead of recommendation.
* Change all the potentially-requires-auth endpoints to always require auth.
  This would mean viewing room directories always requires auth.
* Remove the whole "Rate-limited" value.

## Unstable prefix
Not applicable.
