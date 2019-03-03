# Twarc-Cloud commandline

## General
### Help
For any command or subcommand, `-h` will provide additional help.

### Bucket
By default the bucket is specified in `twarc_cloud.ini`. For many commands, it can be overridden with `--bucket`.

## Collection configuration commands
Collection configuration commands are for creating and updating collection configuration files.

By default, `collection.json` is the collection configuration file. For many commands, it can be overridden 
with `--collection-config-filepath`.

### Create a template

        $ python3 twarc_cloud.py collection-config template filter
        Template written to collection.json.
        
        $ cat collection.json
        {
          "id": "<Identifier for collection. Should not have spaces. Must be unique for bucket.>",
          "keys": {
            "consumer_key": "<Your Twitter API consumer key>",
            "consumer_secret": "<Your Twitter API consumer secret>",
            "access_token": "<Your Twitter API access token>",
            "access_token_secret": "<Your Twitter API access token secret>"
          },
          "type": "filter",
          "filter": {
            "track": "<Comma separated list of terms or hashtags>",
            "follow": "<Comma separated list of user ids>",
            "max_records": "<Optional. Maximum number of records to collect per harvest."
          }
        }

You can now fill in the template or use other collection configuration commands to populate it.

### Get the latest collection configuration file
To download the latest collection configuration file for an existing collection:

        $ python twarc_cloud.py collection-config download test_collection
        Downloaded to collection.json.

### Add Twitter API keys

        $ python twarc_cloud.py collection-config keys
        Added keys to collection.json.

### Add users
To add users by screen names provided on the commandline:

        $ python twarc_cloud.py collection-config screennames @justin_littman @jack @not_justin_littman
        Getting users ids for screen names. This may take some time ...
        Added screen names to collection.json.
        Following screen names where not found:
        not_justin_littman

To add users by screen names from files:

        $ python twarc_cloud.py collection-config screenname-files screennames.txt
        Getting users ids for screen names. This may take some time ...
        Added screen names to collection.json.

To add users by user ids provided on the commandline:

        $ python twarc_cloud.py collection-config userids 481186914
        Added user ids to collection.json.


To add users by user ids from files:

        $ python twarc_cloud.py collection-config userid-filenames userids.txt
        Added user ids to collection.json.

### Update

        $ python twarc_cloud.py collection-config update
        Collection configuration updated.

Updating the collection configuration file creates a changeset file and copies both to your S3 bucket.    

### List changes

        $ python twarc_cloud.py collection-config changes test_collection
        credentials -> consumer_key changed from None to mBbq9ruEckIngQztUir8Kn0 on 2019-03-09T15:33:04.577744
        credentials -> consumer_secret changed from None to Pf28yReBUD9fpLVOsb4r5idZnKQ6xlOomBAjDfs5npFEQ6Rm on 2019-03-09T15:33:04.577744
        credentials -> access_token changed from None to 4811346914-5yIyfryJqfscH4dV29YVLOIzjseVsYuRzCLmwO6 on 2019-03-09T15:33:04.577744
        credentials -> access_token_secret changed from None to S51yYftbEsgdf4WMKMGendxbZO014Zvmv38Tfvc on 2019-03-09T15:33:04.577744
        users -> 481186914 -> screen_name changed from None to justin_littman on 2019-03-09T15:33:26.730416
        keys -> consumer_key changed from None to mBbq9ruEckIngQztTHUir8Kn0 on 2019-03-10T02:51:34.267589
        keys -> consumer_secret changed from None to Pf28yReBUD9Xz0pLVOsb4r5idZnKCKQ6xlOomBAjD5npFEQ6Rm on 2019-03-10T02:51:34.267589
        keys -> access_token changed from None to 481186914-5yIyfryJqcH4dV29YVL37BOIzjseVsYuRzCLmwO6 on 2019-03-10T02:51:34.267589
        keys -> access_token_secret changed from None to S51yY5HjfftbEs4WMKMgvGendxbZVsZO014Zvmv38Tfvc on 2019-03-10T02:51:34.267589
        users -> 12 -> screen_name changed from None to jack on 2019-03-10T02:51:34.267589

The changes are derived from the changeset files that are created whenever a change is made to a collection configuration file.

## Collection commands
Collection commands are for managing collections.

### List collections

        $ python3 twarc_cloud.py collection list
        Collections:
        candidates_for_congress
        mueller

### Add a collection

        $ python3 twarc_cloud.py collection add
        Collection added.
        Don't forget to start or schedule the collection.
        
The default collection configuration file is `collection.json`. When added, it is copied to your S3 bucket.

### Schedule, run once, and stop user timeline and search collections

Before running, a collection must be added.

To run once:

        $ python3 twarc_cloud.py collection once test_collection
        Started

To schedule:

        $ python3 twarc_cloud.py collection schedule test_collection "rate(7 days)"
        Scheduled

The schedule can be specified using a [rate or cron expression](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html).

To stop a scheduled collection:

        $ python3 twarc_cloud.py collection stop test_collection
        Stopped
        
And to list scheduled collections:

        $ python3 twarc_cloud.py collection scheduled
        twarc-cloud2_test_collection_schedule => rate(7 days)

### Start and stop filter collections

Before starting, a collection must be added.

To start:

         $ python3 twarc_cloud.py collection timeline-start test_filter
         Started
         
To stop:

        $ python3 twarc_cloud.py collection timeline-stop test_filter
        Stopping ...
        Stopped
        
Stopping a filter collection may take a few minutes.

### Download a collection

        $ python3 twarc_cloud.py collection download test_collection
        Collection downloaded to download/twarc-cloud2/collections/test_collection

Files that have already been downloaded will be skpped unless `--clean` is provided.

## Harvest commands
### List running harvests

        $ python twarc_cloud.py harvest list
        mueller => Bucket: twarc-cloud2. Status: RUNNING
  
### Get info on a running harvest

        $ python3 twarc_cloud.py harvest running mueller
        mueller => Bucket: twarc-cloud2. Harvest timestamp: 2019-03-10T02:57:27.196194. Tweets: 1252. Files: 2 (15MB)
        
### Get info on the last harvest

        $ python3 twarc_cloud.py harvest last test_collection
        test_collection => Bucket: twarc-cloud2. Harvest timestamp: 2019-03-09T15:35:07.464791. Tweets: 2,140. Files: 1 (855K)
        No user changes.
