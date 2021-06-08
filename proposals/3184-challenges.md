# MSC3184: Challenges

In matrix we already have vibrant discussions going on in rooms, but we often miss a fair method to resolve a dispute between several parties.

This proposal improve matrix by adding several methods to fairly choose between several options by:

 - Defining the standard shape for extensible challenges messages, such as 
     - Rock/Paper/scissors
     - Coin Flip
     - Drawing Straws
 - Defining extensible commitment schemes allowing to define the level for binding vs concealing property of the challenge




## Proposal


This proposal does not require new server APIs, and only define new message types as well as new event relations ( as per MSC2674: Event Relationships)

### General framework

#### Creating a challenge

To start a challenge, Alice will send an `m.challenge` event with the following properties in its contents:

- `body`: a fallback message to alert users that their client does not support challenges
- `challenge_type`: Type of challenge  like `m.challenge.rock_paper_scissors` or `m.challenge.coin`
- `commitment_scheme`: the commitment scheme to use, e.g `random_sha_256`
- `to`: a list of user ids, Users can only respond to this challenge if
  they are named in this field. `m.challenge.*` events that have relation to this challenge but which was not sent by one the these users should be ignored
  
````
{
    "type": "m.challenge",
    "content": {
        "body": "Alice is challenging Bob to Rock Paper Scissors",
        "m.challenge_type": "m.challenge.rock_paper_scissors",
        "commitment_scheme" : "random_sha_256",
        "to": ["@bob:exemple.com"]
    }
}
````

  
#### Commitment phase


Now each participant must send a commitment message regarding the created challenge. For example in the case of rock paper scissors, the participant choose one of ✌️, 🤚, or ✊ and then apply the commitment scheme that will hide the choice to the other participant, while binding to it (the reveal phase will proove that the user did not cheat)

````
{
    "type": "m.challenge.commit",
    "content": {
        "commitment": "kvGuecVHbPcjqSecX3Yz+DrGsNWEezdrfHyk6y1T4iE",
        "m.relates_to": {
            "rel_type": "m.reference",
            "event_id": "$challenge_event_id"
        }
    }
}
````

#### Reveal phase

When each participant in the challenge did send their commitment, now can start the reveal phase.

Each participant will send a reveal message, the reveal message will contain their answer to the challenge as well as the info to verify the commitment

````
{
    "type": "m.challenge.reveal",
    "content": {
        "secret": "✌️",
        "random": "dnNwdmR2bGYsZ21sa2Rudm1xZGZvbmRxbW5mZHFtbHbDpycow6DDpychKA=="
        "m.relates_to": {
            "rel_type": "m.reference",
            "event_id": "$challenge_event_id"
        }
    }
}
````


#### Verification phase

Now each participant can verify that the reveal match the commitments and determinate the challenge result

Using the provided info and commitment scheme, all participants can check if the reveal is valid and matches the initial commitment

`Commit(secret, random) = commitment`

For `m.challenge.rock_paper_scissors` it's just determining if it's win/loose/draw based on the revealed secret ✌️🤚✊


## Commitment schemes

A first commitment scheme `random_sha_256` is defined in this MSC, but more could be added later.

Let `alice_secret` be the answer to the challenge done by alice, and `random` a random 256bit number base64 encoded.

`Commit(alice_secret) = sha256(alice_secret || random)`


In case of a Rock-Paper_Scissors, alice computes a random `rA` number, concatenates ✌️ and rA then compute the hash   that will be sent as `commitment` of the `m.challenge.commit`message

````
{
    "type": "m.challenge.commit",
    "content": {
        "commitment": <sha256(✌️ || rA)>
        [...]
````

In the reveal phase, alice then sends

````
{
    "type": "m.challenge.reveal",
    "content": {
        "secret": "✌️",
        "random": "rA"
````

Bob can then check that `sha256(secret, random) == commitment`


## Challenge types

This MSC defines 3 challenges:

| Challenge        | Id         |
| ------------- |:-------------:| 
| Rock Paper Scissors    | `m.challenge.rock_paper_scissors`|
| Coin Flip  | `m.challenge.coin` |
| Drawing Straws | `m.challenge.straws` |


### Rock Paper Scissors

**Use Case:** 
Settle a dispute or make an unbiased group decision. 

**Participant number:** 2

Possible `secret` values are ✌️🤚✊
Each participant commit on a secret value, and results is defined as follow:
- ✌️ beats 🤚
- 🤚 beats ✊
- ✊ beats ✌️

### Coin Flip

**Use Case:**
Randomly choose between two alternatives
 
**Participant number:** 2

Possible `secret` values are `head` or `tail`

The challenge creator (alice) commits on the outcome of the coin flip (`head`|`tail`)
The other partipant (Bob) choose one of `head`|`tail`

After the reveal phase, Bob wins if he corretly guess the coin flip outcome commited by Alice


### Drawing Straws

**Use case:**
Choose one member of the group to perform a task after none has volunteered for it

**Participant number:** 2 or more

The challenge creator (alice), commits on the ordering of n straws, e.g:
`===`
`=`
`==`
`====`


Each participant will choose one of the straws, by commiting to a number [1,n].
In order to resolve disputes, each participant must commit the straws by order of preference, e.g (1,3,2,4). If straw 1 was already taken, then try to peek 3, and so on.

Alice as the creator must take the last remaining straw.

The participant with the shortest straw wins the challenge.



## Potential issues


## Alternatives


## Security considerations

## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`m.challenge` | event type | `org.billcarsonfr.challenge`
`m.challenge.commit` | event type | `org.billcarsonfr.challenge.commit`
`m.challenge.reveal` | event type | `org.billcarsonfr.challenge.reveal`
`commitment_scheme` | event content field | `org.billcarsonfr.commitment_scheme` 
`m.challenge_type` | event content field | `org.billcarsonfr.challenge_type`
`commitment` | event content field | `org.billcarsonfr.commitment`
`secret` | event content field | `org.billcarsonfr.secret`
`random` | event content field | `org.billcarsonfr.random`