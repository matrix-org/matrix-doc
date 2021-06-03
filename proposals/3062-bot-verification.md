# MSC3062: Bot verification

It is generally recommended that key verification should be done in person.
However, it is usually difficult to meet a bot in person for the purposes of
verifying their keys.  This proposal introduces a mechanism for verifying a bot
via HTTPS.

## Proposal

A new verification method, `m.bot_verification.v1`, is introduced.

With this verification method, the human initiates the verification (we do not
support two bots verifying each other using this method) by sending a
`m.key.verification.request` that includes `m.bot_verification.v1` in the
`methods` property.

The bot then responds with `m.key.verification.ready`, offering
`m.bot_verification.v1` as the only option.  The bot then immediately sends an
`m.key.verification.start` message with `m.bot_verification.v1` as the method.
The `m.key.verification.start` message also contains a `url` property that
indicates a URL that can be used to verify the bot.  The URL must be an HTTPS
URL.

The human's client displays the URL to the human, to allow them to verify that
the URL looks legitimate (e.g. that it belongs to a domain that the human
trusts to be associated with the bot's operators).  If the human accepts the
URL, the client makes a POST request to the URL with the request body being a
JSON object with the following properties:

- `transaction_id`: the transaction ID from the `m.key.verification.start`
  message
- `nonce`: a random nonce
- `from_device`: the device ID that the human is using
- `keys`: a map of key ID to public key for each key that the client wants to
  attest to

The HTTPS server responds with an HTTP code of:

- `200` if the keys match the expected values
- `404` if the `transaction_id` is unknown
- `400` if the keys do not match the expected values
- `303` if the server wants the human to perform additional steps to verify
  their identity (see "[Verifying the human](#verifying-the-human)" below)

Upon successful completion of this step, the bot sends a
`m.key.verification.mac` message to the human's client.  The format is the same
as the format of the message used in SAS verification, but the MAC keys are
produced by using HKDF with the salt equal to the nonce given in the HTTPS
request, and the info parameter composed by concatenating:

- the string `MATRIX_KEY_VERIFICATION_MAC|`,
- the Matrix ID of the human, followed by `|`,
- the device ID of the human, followed by `|`,
- the Matrix ID of the bot, followed by `|`,
- the `transaction_id`, followed by `|`,
- the Key ID of the key being MAC-ed, or the string `KEY_IDS` if the item being
  MAC-ed is the list of key IDs.

The bot also sends a `m.key.verification.done` message.

The human's client calculates the MAC keys and verifies that the MACs for the
keys given in the `m.key.verification.mac` match the expected values.  If they
do, the human's client marks the keys as being verified and sends a
`m.key.verification.done` message.  Otherwise, the human's client displays an
error to the human and sends a `m.key.verification.cancel` message with
`m.key_mismatch` as the `reason`.

### Verifying the human

The above steps allow the human to verify the bot.  However, they do not allow
the bot to verify the human.  In general, there is no way for a bot to verify a
human unless the human has some other account that the bot can use, for example,
if the human has an account with the organization that operates the bot.  For
example, a GitLab bot could verify the human by having them log into their
GitLab account.

If the bot wishes to do this, then it must respond to the HTTPS request with a
status code of `303` and a `Location` header pointing to a URL.  The human's
client then opens the given URL in a browser, allowing the human to perform any
steps necessary to verify their identity.  The bot should ensure that the
identity given in this way matches the expected identity, or record that the
given identity is associated with the human's Matrix ID.

## Potential issues

TODO

## Alternatives

TODO

## Security considerations

The security of this verification method depends on:

- HTTPS,
- the human being able to distinguish a trusted URL from an untrusted URL,
- the bot's operator's ability to secure their web server.

When the human's client makes the HTTPS request, this will expose the human's
IP address to the bot's operators.

## Unstable prefix

Until this feature lands in the spec, the verification method name should be
`org.matrix.msc3062.bot_verification`.
