# Collection types

## User timeline
User timelines are collected using the [GET statuses/user_timeline](https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline) method.

User timelines are always requested using the user id. User ids never change, while a screen name can change. When you
add users to a user timeline collection by screen name, Twarc-Cloud will lookup the user id.

The user id and screen name are stored in the collection configuration file. For example:

        "users": {
            "481186914": {
              "screen_name": "justin_littman",
            },
            "12": {
              "screen_name": "jack"
            }
        }

The user timeline method allows retrieving up to the last 2800 tweets for a user. Twarc-Cloud collects user timelines incrementally,
meaning that the first time a harvest collects a user timeline, all available tweets are collected. In subsequent harvests,
only new tweets are collected. The state is stored in the collection configuration file as well:

        "users": {
            "481186914": {
              "screen_name": "justin_littman",
              "since_id": "1101479829856149504"
            }
        }

In addition to retrieving the tweets for a user, Twarc-Cloud will retrieve information about the user using the
[GET users/show](https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-users-show) method.
These are stored in the `users.jsonl` file.

`user_changes.json` provides any changes that were found for users such as a screen name being changed or an account being
deleted.

If a changed screen name is found, `collection.json` will be updated with the new screen name. The `delete_users_for` setting
in `collection.json` will determine what happens if a user is deleted, suspended, or protected.

        "delete_users_for": [
            "protected",
            "suspended",
            "not_found"
          ]

If `protected` is included and a user is found to be protected, the user will be removed from `collection.json`. If
`suspended` is included and a user is found to be suspended, the user will be removed. And if `not_found` is included
and a user is not found, the user will be removed.

Users can be added to `collection.json` using the following commands:
* `collection-config userids`: Add a list of provided user ids.
* `collection-config userid-files`: Add a list of user ids contained in provided files.
* `collection-config screennames`: Add a list of provided screen names.
* `collection-config screenname-files`: Add a list of screen names contained in provided files.

For screen names, the _@_ is optional. Also, Twarc-Cloud will retrieve the user id for each screen name. This may take
some time.

User timeline collections can be scheduled with the `collection schedule` command and run once with the `collection
once` command.

## Search

Searches are collected using the [GET search/tweets.json](https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets) method.

Search queries are stored in the collection configuration file. For example:

      "search": {
        "query": "stone OR mueller"
      }
  
To limit the number of records collected per harvest, set `max_records`. For example:

      "search": {
        "query": "stone OR mueller",
        "max_records": "1000"
      }

Twarc-Cloud collects searches incrementally, meaning that the first time a harvest collects a search, all available
tweets are collected. Note that depending on the query, this initial harvest may take up to several days. In subsequent
harvests, only new tweets are collected. The state is stored in the collection configuration file.

Search collections can be scheduled with the `collection schedule` command and run once with the `collection
once` command.


## Filter stream
Filter streams are collected using the [POST statuses/filter](https://developer.twitter.com/en/docs/tweets/filter-realtime/overview/statuses-filter) method.

The filters for the filter stream are stored in the collection configuration file. For example:

        {
          "track": "mueller",
        }

Filter streams run continuously. They are turned on by the `filter start` command and stopped by the `filter stop` command.

Alternatively, if `max_records` is provided, a filter stream will stop after the specified number of tweets are collected.
For example:

        {
          "track": "mueller",
          "max_records": "100000"
        }


Twitter's API limits keys to being used for only a single filter stream at a time. Twarc-Cloud does not enforce this
limitation. If you use them for multiple filter stream collections, they will force each other to stop and mayhem will ensue.
