# Twitter API keys
Accessing Twitter's API requires application keys and user keys.

## Application keys
Each instance of Twarc-Cloud requires a set of application keys. You can apply for application keys
at [https://developer.twitter.com/en/apply-for-access](https://developer.twitter.com/en/apply-for-access). Once
you have application keys, they can be provided to Twarc-Cloud as described below.

Application keys are called _consumer key_ and _consumer secret_.

## User keys
By authorizing a Twarc-Cloud application, a user is given a set of user keys for a Twitter account. A separate 
set of user keys can be issued for each Twitter account. User keys are acquired as described below.

User keys are called _access token_ and _access token secret_.

## Managing keys
Twarc is used to acquire and manage Twitter API keys. Twarc can manage multiple set of keys. These are 
stored in `~/.twarc`.

To add keys, execute `twarc configure` and follow the prompts.

To add keys to a `collection.json`, use the `collection-config keys` command. A specific key can be specified by
`--profile`. For example:

        $ python3 twarc_cloud.py collection-config keys --profile justin_littman
        Added keys to collection.json.

