# MSC3051: Scalable relations

Edits, reactions, replies, threads, message annotations and other MSCs have
shown, that relations between events are very powerful and useful. Currently the
format from [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) is
used. That format however limits each event to exactly one relation. As a result
events rely on other ways to represent secondary relations. For example edits
keep the relation from the previous event. Their support to change or delete
that relation is limited. In theory you could pass that in `m.new_content`, but
clients don't seem to support that and the actual deletion of a relation is
unexplored as well.

There are many cases where 2 or more relations on an event would be useful. This
MSC proposes a simple way to do that and replace the currently proposed format.

## Proposal

To support multiple relations per file this MSC proposes the following format:

```json
{
  "content": {
    "m.relations": [
      {
        "event_id": "$some-other-event",
        "rel_type": "m.in_reply_to"
      },
      {
        "event_id": "$some-third-event",
        "rel_type": "m.replaces"
      },
      {
        "event_id": "$event-four",
        "rel_type": "org.example.custom_relation",
        "key": "some_aggregation_key"
      }
    ]
  },
  "event_id": "$something",
  "type": "m.room.message"
}
```

This has a few benefits:

- You can relate to multiple events at the same time. (I.e. you have a
    description for multiple files you sent.)
- You can have multiple different relation types at once. (I.e. an edit, that
    is also a reply, or a reaction inside a thread.)
- You don't need to look up reply relations in multiple events for edits. The
  edited event is canonical and can be used standalone, without having to look
  up the original event to figure out, what was replied to. You can also remove
  a relation with an edit now. (Useful if you replied to the wrong message or
  didn't mean to reply to anyone.)
- This format is conceptually a lot simpler, if an event has multiple relations.
    You don't run into issues with packing relations into `m.new_content`,
    especially for encrypted events, etc. You just have a list of relations.

If clients want to stay backwards compatible (for a while at least), in many
instances it is possible to generate an `m.relates_to` object from the relations
list. This can be done by picking a primary relation, i.e. the edit relation,
and then packaging up the remaining relations in `m.new_content` or simply
throwing them away. Since this proposal uses `m.relations`, this does not
conflict with the current relations from the other MSCs. One can also generate
the relations object from this MSC from the old relations, since the new
relations are a strict superset, which may be useful to make handling inside of
a client easier.

## Potential issues

### Ordering

The list of relations is not hierarchical. As such there is no order like where
you have a top level relation and a lower level relation like an edit having
priority over a reply.

I don't believe that is an issue in practice. If you edit a message with a
reply, there is a natural meaning to the combination of both relations. You can
even apply them in any order, imo. But there may be other relations, where this
causes more issues. An MSC introducing such a relation should specify how to
handle conflicts then.

### Conflicting relations

Some relation types should probably not be combined. For example you may
disallow editing a reaction, because clients probably won't be handling that
correctly. This MSC however does not disallow that. Specifications that define relations should specify,
how clients should handle that and clients sending such combinations should be
aware, that those probably won't get handled. I don't think just allowing 1
relation is the solution to handling such conflicts and I don't think they will
happen much in practice.

## Alternatives

- We could just stick with the existing proposal to only have 1 relation per
    event. This is obviously limiting, but works well enough for a lot of
    relation types.
- There are a few other ways to structure relations like using an object instead
    of an array, etc. I believe this is the most usable one.

## Security considerations

Multiple releations may increase load on the server and the client and provide
more opportunities to introduce bad data. Servers and clients should take
additional care and validate accordingly. It should not be considerably worse
than single relations though and servers may limit relations to a reasonable
amount (like they do for devices already).

## Unstable prefix

Clients should use `im.nheko.relations.v1.relations` instead of `m.relations`
and `im.nheko.relations.v1.in_reply_to` as the relation type for replies in the
mean time.
