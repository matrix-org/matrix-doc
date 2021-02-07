Documentation Style
===================

Each document should begin with a brief single sentence to describe what this
file contains: in this case a description of the style to write documentation
in.

Format
------

Documentation is written either in github-flavored markdown or RST.

Sections
--------

RST support lots of different punctuation characters for underlines on sections.
Content in the specification MUST use the same characters in order for the
complete specification to be merged correctly. These characters are:

- ``=``
- ``-``
- ``~``
- ``+``
- ``^``
- \`````
- ``@``
- ``:``

If you find yourself using ``^`` or beyond, you should rethink your document
layout if possible.

Correct capitalisation for long section names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Headings should start with a capital letter, and use lower-case otherwise.


TODOs
-----

Any RST file in this repository may make it onto ``matrix.org``. We do not want
``TODO`` markers visible there. For internal comments, notes, TODOs, use standard
RST comments like so::

  .. TODO-Bob
    There is something to do here. This will not be rendered by something like
    rst2html.py so it is safe to put internal comments here.

You SHOULD put your username with the TODO so we know who to ask about it.

Line widths
-----------

We use 80 characters for line widths. This is a guideline and can be flouted IF
AND ONLY IF it makes reading more legible. Use common sense.

Stylistic notes
---------------

General
~~~~~~~

Try to write clearly and unambiguously. Remember that many readers will not
have English as their first language.

Prefer British English (colour, -ise) to American English.

The word "homeserver" is spelt thus (rather than "home server", "Homeserver",
or (argh) "Home Server"). However, an identity server is two words.

An "identity server" (spelt thus) implements the Identity Service API (also spelt
thus). However, "Application Services" (spelt thus) implement the Application Service
API. Application Services should not be called "appservices" in documentation.

.. Rationale: "homeserver" distinguishes from a "home server" which is a server
   you have at home. "identity server" is clear, whereas "identityserver" is
   horrible.

Lists should:

* Be introduced with a colon.
* Be used where they provide clarity.
* Contain entries which start with a capital and end with a full stop.

OpenAPI
~~~~~~~

When writing OpenAPI specifications for the API endpoints, follow these rules:

* ``summary``: a phrase summarising what this API does. Start with a capital,
  end with a full stop. Examples: "Sends an event."; "Searches the directory."

* ``description``: a longer description of the behaviour of this API, written
  in complete sentences. Use multiple paragraphs if necessary.

  Example:

      This API sends an event to the room. The server must ensure that the user
      has permission to post events to this room.

* ``operationId``: a camelCased unique identifier for this endpoint. This will
  be used to automatically generate bindings for the endpoint.

* Parameter and property ``description``\s: a phrase summarising the behaviour
  of this parameter or property, optionally followed by sentences giving more
  detailed explanations. Start with a capital, end with a full stop.

  The description is also the place to define default values for optional
  properties. Use the wording "Defaults to X [if unspecified]."

  Some descriptions start with the word "Optional" to explicitly mark optional
  properties and parameters. This is redundant. Instead, use the ``required``
  property to mark those that are required.
