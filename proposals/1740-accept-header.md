# MSC 1740: Using the Accept header to select an encoding

Matrix has always aimed to support many types of encoding. However, in practice the only supported option
is `application/json`. The assumption that all clients and servers make is that requests will be carried out in `application/json`.
This proposal aims to change that by using the `Accept` HTTP header to select the best encoding for the
client and the server. This proposal doesn't attempt to use the same header for federation (S2S) endpoints,
just for C2S endpoints.

The reason for supporing multiple encodings other than `application/json` would be to open the door to more efficent
encoding methods in the future for the HTTP transport, for example CBOR which was found to have a 20%
reduction in size. However, this proposal is not here to evaluate the merits of any one particular encoding.

## Proposal

### Servers

Servers can support multiple encodings for both reading requests and sending responses over HTTP. They
should read the `Accept` header [RFC7231](https://tools.ietf.org/html/rfc7231#section-5.3.2) from client
and decide based on the rules provided in the RFC what is the best encoding they can support.

If the rules of `Accept` fail (a satisfactory encoding could not be picked), the server SHOULD 
respond with `HTTP 406 Not Acceptable`.

If the clients request contains a `Content-Type` header that the server does not support, 
the server SHOULD respond with `HTTP 415 Unsupported Media Type`.

The body of the response is left to the server, although worth bearing in mind that confused developers
may be looking at the response looking for the fault in their code.

### Clients

Clients SHOULD supply `Accept` to all requests they make, and set `Content-Type` to the encoding
they intend to use. If a client doesn't supply an `Accept` header, then `application/json` must be presumed acceptable
to that client.

The client should not attempt to communicate with this homeserver if the response was 406, 
because it will mean that neither party have a supported encoding type. 
An appropriate error may be displayed to the user.

## Alternative solutions

### Negotiate transport(+encoding)

It's clear that this proposal still limits Matrix to serving HTTP. We could expand the proposal 
to negoitating transport either from within a HTTP header (which would `Upgrade` you to a different
transport), .well-known or a SRV record rather than limiting ourselves to `Accept`. The proposal 
does not currently look at negotiating transport as I believe the encoding should be negotiated 
within the transport and is a seperate proposal. 

## Potential issues

- This proposal does NOT specify any additional encoding formats for the time being, and could be dealt
with in future by another proposal.

# Security considerations

I cannot think of any security issues with doing this.

## Conclusion

This proposal allows implementations to broaden what encodings they support without
having to be configured on a case by case basis. This proposal uses standard HTTP headers
to deliver a simple method of determinign what encodings both parties support. This paves
the way for a more diverse and competitive ecosystem over speed and performance of different
encodings.
