# MSC3226: Per Room Spellcheck Language

It is common for people on the Internet to talk in more than one language. English will probably be
the most used one, but for many it is not their mother tongue and they will use the latter as well.

Clients can offer spell checking functionality, but in order to provide helpful suggestions they need
to know which language the user is currently writing in. When spell checking is available, the language
can usually be selected e.g. via the right click menu, but it becomes tedious when one switches back and
forth between two or more of them.

This proposal aims at providing users with a way to set a language per room, so that switching between
conversations held in different languages automatically switches to the appropriate dictionary.


## Proposal

Clients offering spell checking should default their dictionary to the system language. They should offer
a way to change it and when the user sets a specific language, then they should store the language code
as `m.input_language` account data for the room where it was set. Language codes must be
[RFC3066](https://datatracker.ietf.org/doc/html/rfc3066) compliant.


## Alternatives

The language could be defined as a room property: a room administrator could set it once and then every
member would get it for free. However, not everyone in a given room necessarily talks in the same language
(or even language variant, e.g. en_US vs en_GB) and there would need to be a way for users to override the
room property. This MSC could be used as a mechanism to do said override, if such a room property were ever
defined. Adding a room property requires more work and thought, and can be done in another MSC. It is thus
considered out of scope for this one.

The feature can also work without actually adding it to the Matrix specification. There is indeed already
one existing implementation (see [Unstable prefix](#unstable-prefix) below). Standardising the account data
type though has the benefit that it is not client specific anymore, and the setting can be more easily reused
by any number of clients.


## Unstable prefix

Fractal already successfully offers this proposed feature. It stores the language code under the
`org.gnome.fractal.language` account data type. This was released on the stable channel as part of
Fractal 4.4 on August 7th 2020.
