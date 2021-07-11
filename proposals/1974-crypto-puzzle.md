# Crypto Puzzle Challenge

Proof-of-Work rate-limiting, via cryptographic puzzle challenge, to fight spam.

## Proposal

New Errors:

  - M_PUZZLE_NEEDED
    - extra field `seed` (String)
    - extra field `bits` (Integer)
    - extra field `algorithm` (String `bcrypt`)
  - M_PUZZLE_INVALID

New Headers:

  - X-Matrix-Puzzle
    - `seed:bits:algorithm:n` - where `n` is an integer
    - When this header is hashed with `algorithm` is must produce at least `bits` many leading zeros

In response to a request, the receiving party may error with a `M_PUZZLE_NEEDED` challenge, which requires a crypto-puzzle be solved and request re-submitted with proof-of-work attached as `X-Matrix-Puzzle`.
The puzzle is solved by incrementing `n` and re-hashing the header using `algorithm`, then checking for leading zeros.

Inspired by [Hashcash](https://en.wikipedia.org/wiki/Hashcash)

## Tradeoffs

The original Hashcash is not a request-response challenge but instead only opt-in by the sender. This allows for pre-computation and does not allow dynamic `bits` to be requested (necessary as computers get faster) or a change in algorithm (again, necessary because of dedicated hardware (ASICs)). Though it could be made viable by re-specifying these in the Matrix spec.

`bcrypt` is used here but there are other options e.g. `Argon2d`, `scrypt`. bcrypt was chosen because it's popular (and thus most software ecosystems should have a package for it) and because it is hard to parallelize on GPU/ASIC hardware.

## Potential issues

Giving clients free-reign over when to use the error and how much work they require could lead to some unintended consequences.

E.g. If the major server implementations use too high values as their default then it might force out low-end hardware altogether (and make running your own server potentially costly (in CPU time), decreasing decentralization).


## Conclusion

This proposal provides a powerful spam-fighting mechanism which relies on compute resource consumption.
