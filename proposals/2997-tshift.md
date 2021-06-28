# MSC2997: "There's an MSC for that!"

Throughout fosdem 2021 multiple different features or ideas around matrix were discussed. As it turns
out, most of them already had an MSC for that! One feature that was keep being brought up, was to get
"There's an MSC for that!" onto a t-shirt. Unfortunately, there wasn't an MSC for that yet.

## Proposal

Get a t-shirt with "There's an MSC for that!" written on it. This T-shirt shall include a code block
typeset in a monospace block that should read
```json
{
  "type": "m.t-shirt",
  "content": {
    "body": "There's an MSC for that!"
  }
}
```
## Potential issues

Once the spec is complete and there are no more MSCs the t-shirt will be obsolete.

## Alternatives

Instead of a shirt, a sweater or thelike could be used.

Instead of just printing normal event contents on the shirt we might want to consider using
t-shirts-as-rooms. This would allow greater flexibility, as we could easily add any amount of metadata
to the t-shirt in the future, such as the amount of times it has been washed or what temperature to
iron it at.

## Security considerations

Unfortunately not all people are able to wear t-shirts, so a solution for those would have to be
found.

## Unstable prefix

In places where this proposal mentions `t-shirt`, `de.sorunome.t-shirt` is to be used instead
