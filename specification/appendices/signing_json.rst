.. Copyright 2016 OpenMarket Ltd
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Signing JSON
------------

Various points in the Matrix specification require JSON objects to be
cryptographically signed. This requires us to encode the JSON as a binary
string. Unfortunately the same JSON can be encoded in different ways by
changing how much white space is used or by changing the order of keys within
objects.

Signing an object therefore requires it to be encoded as a sequence of bytes
using `Canonical JSON`_, computing the signature for that sequence and then
adding the signature to the original JSON object.

Canonical JSON
~~~~~~~~~~~~~~

We define the canonical JSON encoding as:

- A JSON value with the shortest UTF-8 string.
- Encoded with dictionary keys lexicographically sorted by unicode codepoint.
- With numbers in the JSON as integers in the range ``[-(2**53)+1, (2**53)-1]``.

We pick UTF-8 as the encoding as it should be available to all platforms and
JSON received from the network is likely to be already encoded using UTF-8.
We sort the keys to give a consistent ordering. We force integers to be in the
range where they can be accurately represented using IEEE double precision
floating point numbers since a number of JSON libraries represent all numbers
using this representation.

.. WARNING::
   Events in room versions 1, 2, 3, 4, and 5 might not be fully compliant with
   these restrictions. Servers SHOULD be capable of handling JSON which is considered
   invalid by these restrictions where possible.

   The most notable consideration is that integers might not be in the range
   specified above.

.. Note::
   Float values are not permitted by this encoding.

.. code:: python

 import json

 def canonical_json(value):
     return json.dumps(
         value,
         # Encode code-points outside of ASCII as UTF-8 rather than \u escapes
         ensure_ascii=False,
         # Remove unnecessary white space.
         separators=(',',':'),
         # Sort the keys of dictionaries.
         sort_keys=True,
         # Encode the resulting unicode as UTF-8 bytes.
     ).encode("UTF-8")

Grammar
+++++++

Adapted from the grammar in http://tools.ietf.org/html/rfc7159 removing
insignificant whitespace, fractions, exponents and redundant character escapes.

.. code::

 value     = false / null / true / object / array / number / string
 false     = %x66.61.6c.73.65
 null      = %x6e.75.6c.6c
 true      = %x74.72.75.65
 object    = %x7B [ member *( %x2C member ) ] %7D
 member    = string %x3A value
 array     = %x5B [ value *( %x2C value ) ] %5B
 number    = [ %x2D ] int
 int       = %x30 / ( %x31-39 *digit )
 digit     = %x30-39
 string    = %x22 *char %x22
 char      = unescaped / %x5C escaped
 unescaped = %x20-21 / %x23-5B / %x5D-10FFFF
 escaped   = %x22 ; "    quotation mark  U+0022
           / %x5C ; \    reverse solidus U+005C
           / %x62 ; b    backspace       U+0008
           / %x66 ; f    form feed       U+000C
           / %x6E ; n    line feed       U+000A
           / %x72 ; r    carriage return U+000D
           / %x74 ; t    tab             U+0009
           / %x75.30.30.30 (%x30-37 / %x62 / %x65-66) ; u000X
           / %x75.30.30.31 (%x30-39 / %x61-66)        ; u001X

Examples
++++++++

To assist in the development of compatible implementations, the following test
values may be useful for verifying the canonical transformation code.

Given the following JSON object:

.. code:: json

    {}

The following canonical JSON should be produced:

.. code:: json

    {}

Given the following JSON object:

.. code:: json

    {
        "one": 1,
        "two": "Two"
    }

The following canonical JSON should be produced:

.. code:: json

    {"one":1,"two":"Two"}

Given the following JSON object:

.. code:: json

    {
        "b": "2",
        "a": "1"
    }

The following canonical JSON should be produced:

.. code:: json

    {"a":"1","b":"2"}

Given the following JSON object:

.. code:: json

    {"b":"2","a":"1"}

The following canonical JSON should be produced:

.. code:: json

    {"a":"1","b":"2"}

Given the following JSON object:

.. code:: json

    {
        "auth": {
            "success": true,
            "mxid": "@john.doe:example.com",
            "profile": {
                "display_name": "John Doe",
                "three_pids": [
                    {
                        "medium": "email",
                        "address": "john.doe@example.org"
                    },
                    {
                        "medium": "msisdn",
                        "address": "123456789"
                    }
                ]
            }
        }
    }


The following canonical JSON should be produced:

.. code:: json

    {"auth":{"mxid":"@john.doe:example.com","profile":{"display_name":"John Doe","three_pids":[{"address":"john.doe@example.org","medium":"email"},{"address":"123456789","medium":"msisdn"}]},"success":true}}


Given the following JSON object:

.. code:: json

    {
        "a": "日本語"
    }

The following canonical JSON should be produced:

.. code:: json

    {"a":"日本語"}

Given the following JSON object:

.. code:: json

    {
        "本": 2,
        "日": 1
    }

The following canonical JSON should be produced:

.. code:: json

    {"日":1,"本":2}

Given the following JSON object:

.. code:: json

    {
        "a": "\u65E5"
    }

The following canonical JSON should be produced:

.. code:: json

    {"a":"日"}

Given the following JSON object:

.. code:: json

    {
        "a": null
    }

The following canonical JSON should be produced:

.. code:: json

    {"a":null}

Signing Details
~~~~~~~~~~~~~~~

JSON is signed by encoding the JSON object without ``signatures`` or keys grouped
as ``unsigned``, using the canonical encoding described above. The JSON bytes are then signed using the
signature algorithm and the signature is encoded using `unpadded Base64`_.
The resulting base64 signature is added to an object under the
*signing key identifier* which is added to the ``signatures`` object under the
name of the entity signing it which is added back to the original JSON object
along with the ``unsigned`` object.

The *signing key identifier* is the concatenation of the *signing algorithm*
and a *key identifier*. The *signing algorithm* identifies the algorithm used
to sign the JSON. The currently supported value for *signing algorithm* is
``ed25519`` as implemented by NACL (http://nacl.cr.yp.to/). The *key identifier*
is used to distinguish between different signing keys used by the same entity.

The ``unsigned`` object and the ``signatures`` object are not covered by the
signature. Therefore intermediate entities can add unsigned data such as
timestamps and additional signatures.


.. code:: json

  {
     "name": "example.org",
     "signing_keys": {
       "ed25519:1": "XSl0kuyvrXNj6A+7/tkrB9sxSbRi08Of5uRhxOqZtEQ"
     },
     "unsigned": {
        "age_ts": 922834800000
     },
     "signatures": {
        "example.org": {
           "ed25519:1": "s76RUgajp8w172am0zQb/iPTHsRnb4SkrzGoeCOSFfcBY2V/1c8QfrmdXHpvnc2jK5BD1WiJIxiMW95fMjK7Bw"
        }
     }
  }

.. code:: python

  def sign_json(json_object, signing_key, signing_name):
      signatures = json_object.pop("signatures", {})
      unsigned = json_object.pop("unsigned", None)

      signed = signing_key.sign(encode_canonical_json(json_object))
      signature_base64 = encode_base64(signed.signature)

      key_id = "%s:%s" % (signing_key.alg, signing_key.version)
      signatures.setdefault(signing_name, {})[key_id] = signature_base64

      json_object["signatures"] = signatures
      if unsigned is not None:
          json_object["unsigned"] = unsigned

      return json_object

Checking for a Signature
~~~~~~~~~~~~~~~~~~~~~~~~

To check if an entity has signed a JSON object an implementation does the
following:

1. Checks if the ``signatures`` member of the object contains an entry with
   the name of the entity. If the entry is missing then the check fails.
2. Removes any *signing key identifiers* from the entry with algorithms it
   doesn't understand. If there are no *signing key identifiers* left then the
   check fails.
3. Looks up *verification keys* for the remaining *signing key identifiers*
   either from a local cache or by consulting a trusted key server. If it
   cannot find a *verification key* then the check fails.
4. Decodes the base64 encoded signature bytes. If base64 decoding fails then
   the check fails.
5. Removes the ``signatures`` and ``unsigned`` members of the object.
6. Encodes the remainder of the JSON object using the `Canonical JSON`_
   encoding.
7. Checks the signature bytes against the encoded object using the
   *verification key*. If this fails then the check fails. Otherwise the check
   succeeds.
