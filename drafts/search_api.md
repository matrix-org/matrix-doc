# Search API

**THIS IS OUTDATED AND HERE FOR HISTORICAL REASONS.**

## Use Cases

1. Search for events in a particular room, a subset of rooms, or all rooms you have joined. For example, searching for every mention of "matrix.org is great".
2. Search for a particular room, e.g. "matrix dev", looking through rooms' current name, topic etc.
3. Searching for a particular user based on current profile information.
4. Global spotlight style search that looks through all the previous information.

These neatly fall into three distinct search categories, with a fourth "all" meta category.

### Types of queries

Due to performance concerns we do not (currently) want to support querying arbitrary JSON. Therefore, we shall explicitly enumerate all keys in each category which we want to support searching over, as well as the types of search supported (e.g. FTS vs exact matches).

Most keys can be ignored for searching (e.g. `prev_events` key in event json) as they aren't user facing. Other keys simply contain auto generated opaque ids (e.g. `room_id`) and so don't need to support FTS style querying.

For the spotlight style search we want to do a FTS/substring query across all supported keys.

There are several types of possible matching algorithms:

- Full text search, e.g. "dog jumps" matches "The dogs are jumping all over the place".
- Exact matching, e.g. "xyz" matches "xyz" only.
- Substring matching, e.g. "xyz" matches "xyzabc"
- Range matching, e.g. 5..20 matches 15.

## Search Categories and their supported keys

### Room events

This is for searching for things sent in a room.

Since we don't support querying arbitrary JSON, we limit ourselves to querying known keys on known event types. The following keys for the given events support searching with the given search algorithm.


* `m.room.message`:
    * `content.body` - FTS
    * `msgtype` - exact match

* `m.room.name`:
    * `content.name` - FTS / substring

* `m.room.topic`:
    * `content.topic` - FTS

* All supported events:
    * `sender` - substring
    * `origin_server_ts` - range
    * `room_id` - exact match

Returns `Room Event` JSON objects.


### Rooms

Used to search for particular rooms based on their identity, without searching within the rooms themselves.

- Current room name - FTS / substring
- Current room topic - FTS
- Current room aliases (that we know about?) - substring

### Profile

Used to search for particular users based on profile information. This will be more useful when profile support has been expanded 

- Display name - substring
- Matrix ID - substring

### "All"

The `all` meta category is handled in a special way. It searches through *all* categories and keys that support either FTS or substring searches.

## Implementation Concerns

Full text search is a complex operation. While there exists many off the shelf solutions, they all support different features and operations. As such it is important that the search API is both extensible and flexible, allowing different home server implementations to use different search backends.

## Grouping

It can be useful to have results grouped by certain keys. For example, having messages returned grouped by room or sender. Applying a limit to the number of results per group can ensure that a single group can't drown out valid results from other groups.

## Facets

Facets are effectively filters suggested by the server that the user may find helpful to apply to the result set. This allows users to quickly narrow down searches. An example facet would be a specific room or time range.

Facets are usually ranked by some order of relevancy.

Example use case would be attempting to find a conversation about video calling:

1. Do a FTS for "video calling".
2. Get given a list of results and facets: "Room: WebRTC", "During: January 2015", ...
3. The user remembers the conversation may have happened around Jan 2015, so selects that facet.
4. Server returns more results from that timeframes, and more facets: e.g. "Room: WebRTC", "Room: Matrix Dev", ...
5. User decides it was probably in "Matrix Dev", so selects that facet.
6. Server returns results for Jan 2015, Matrix Dev matching "video calling".
7. Users discovers the conversation he was looking for in the results list.

The important part here is that the facets are *suggested* (vaguely) intelligently by the search backend.


Facets are an optional feature.

## Pagination

Pagination is a request for more results. This could be with extra constraints, e.g. if results were grouped and a user requested more results for a given group.

We support this by returning tokens in the response at various positions. Clients can request more results by passing one of these tokens to the search API. The position of the token in the response indicates if it will return a filtered results, e.g. a pagination token defined in a group will return the next batch of results from that group.

Pagination is an optional feature. Servers that don't support pagination can omit returning any pagination tokens in the response.

## Request

The search query is made up of a list of constraints in one (or more) search categories. Each search category returns a distinct set of results in the response.

When supplying a pagination token no constraints should be specified.


`POST /search[?batch=<next_batch>]`

```json
{
    "search_categories": {
        "room_events": {
            "constraints": [
                {
                    "type": "FTS",
                    "key": "body",
                    "value": "lazy dog",
                }
            ],
            
            "groupings": {
                "group_by": [
                    {
                        "key": "room_id"
                    }
                ]
            },
        },
    },
    
    "limit": 20,
}
```

The format of the `value` of the individual constraints depends on the type of search.

- `FTS`: A string to pass to the FTS engine.
- `exact_match`: A list of strings, returns results that match any of the items.
- `substring`: A list of strings, returns results that match any of the items.
- `range`: A json object with keys `from` and `to` that have integer values. Range is inclusive of `from` and exclusive of `to`. 

The *all* search category is special cased, and has the following format:

```
"all": {
    "value": "lazy dog"
}

```


## Response

```json
{
    "search_categories": {
        "room_events": {
            "results": {
                "<id>": {
                    "rank": 0.5234156548,
                    "result": { }
                }
            },
          
            "groups": {
                "<group>": {
                    "rank": 0.214,
                    "results": ["<id>"],
                    "next_batch": "<some_token>"
                },
            },
            
            "facets": {
                "<facet_id>": {
                    "count": 52,
                    "rank": 0.5,
                    "key": "sender",
                    "value": "@erikj:jki.re",
                    "next_batch": "<some_token>"
                }
            },
          
            "count": 14,

            "next_batch": "<some_token>"
        }
    },

    "count": 14,
  
    "next_batch": "<some_token>"
}
```


# Open questions

1. Are facets and groups the same? Should they be treated the same?
2. Is this API flexible enough to cover most search backend and features? Is it too flexible?
3. Do servers want to mandate that a search request is over at least one indexed field?
4. Do we want to be more clever with searching based on timestamps? Currently we would base it off `origin_server_ts`, which isn't necessarily at all accurate. 
5. Should we support specifying substring matches as prefix, infix or suffix searches?
6. Support for highlighting search results?

# Examples


## Basic search

Search for all messages that contain "lazy dog"

``POST /search``

```json
{
    "search_categories": {
        "room_events": {
            "constraints": [
                {
                    "type": "FTS",
                    "key": "content.body"
                    "value": "lazy dog",
                }
            ],
        },
    }
}
```

Response:

```json
{
    search_categories": {
        "room_events": {
            "results": {
                "$wibble:example.com": {
                    "rank": 0.5234156548,
                    "result": {
                        "event_id": "$wibble:example.com",
                        "content": {
                            "body": "Those are such lazy dogs!"
                        },
                        "sender": "@erikj:jki.re",
                        "room_id": "!123:example.com",
                    }
                },
                "$wibble2:example.com": { ... }
            }
        }
    }
}
```


## Search a particular room

Search for all messages that contain "lazy dog" in a particular room.

``POST /search``

```json
{
    "search_categories": {
        "room_events": {
            "constraints": [
                {
                    "type": "FTS",
                    "key": "content.body"
                    "value": "lazy dog"
                },
                {
                    "type": "exact",
                    "key": "room_id"
                    "value": ["!foobar:example.com"]
                }
            ]
        }
    }
}
```

Response:

```json
{
    search_categories": {
        "room_events": {
            "results": {
                "$wibble3:wobble": {
                    "rank": 0.5234156548,
                    "result": {
                        "event_id": "$wibble3:wobble",
                        "content": {
                            "body": "Those are such lazy dogs!"
                        },
                        "room_id": "!foobar:example.com",
                        "sender": "@erikj:jki.re"
                    }
                }
            }
        }
    }
}
```

## Search everywhere

Search everywhere for "testing".

``POST /search``

```json
{
    "search_categories": {
        "all": {
            "value": "testing"
        },
    }
}
```

Response:

```json
{
    search_categories": {
        "room_events": {
            "results": {
                "$wibble3:wobble": {
                    "rank": 0.5234156548,
                    "result": {
                        "event_id": "$wibble3:wobble",
                        "content": {
                            "body": "This is just a test"
                        },
                        "room_id": "!foobar:example.com",
                        "sender": "@erikj:jki.re"
                    }
                }
            }
        },

        "rooms": {
            "results": {
                "!foobar:example.com": {
                    "rank": 0.7158,
                    "result": {
                        "name": "Testing Room",
                        "topic": "This is a room for testing",
                        "room_id": "!foobar:example.com"
                    }
                }
            }
        },

        "profiles": {
            "results": {
                "@testingaccount:example.com": {
                    "rank": 0.6158,
                    "result": {
                        "display_name": "Bob",
                        "user_id": "@testingaccount:example.com"
                    }
                }
            }
        }
    }
}
```
