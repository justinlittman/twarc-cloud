# Quick start

## Setup
1. Install the [requirements](requirements.md).
2. Configure Terraform.

        $ cd terraform
        $ cp example.terraform.tfvars terraform.tfvars

    and then update `terraform.tfvars` with your root or administrator AWS access keys and also select a new name for your S3 bucket.    

3. Set up your AWS environment using Terraform.

        $ terraform init
        $ terraform apply
        
    Terraform will output some values that are needed in the next step.
    
    Note that the root or administrator AWS access keys are no longer required by Twarc-Cloud so you can remove them.
    
4. Configure Twarc-Cloud.

        $ cd ..
        $ cp example.twarc_cloud.ini twarc_cloud.ini
        
   and then update `twarc_cloud.ini` with the values output by Terraform from the previous step. You can also optionally
   provide a Honeybadger API key.

5. Acquire a Twitter API keys using Twarc.

        $ twarc configure
        
   and then provide your consumer keys. Twarc will then ask you paste a url into a browser, where you will be asked to log
   into your Twitter account and authorize Twarc-Cloud to access your account.
   
6. Make sure everything is working:

        $ python3 twarc_cloud.py
        usage: twarc_cloud.py [-h] [-V] [--debug]
                              {collection-config,collection,harvest} ...
        
        Manage AWS resources for Twarc Cloud.
        
        positional arguments:
          {collection-config,collection,harvest}
                                command help
            collection-config   Collection configuration-related commands.
            collection          Collection-related commands.
            harvest             Harvest-related commands.
        
        optional arguments:
          -h, --help            show this help message and exit
          -V, --version         Show version and exit
          --debug
  
        $ python twarc_cloud.py harvest list
        No running harvests.
        
## Create a user timeline collection
1. Create a collection configuration file.
    
        $ python3 twarc_cloud.py collection-config template user_timeline --id=test_collection
        Template written to collection.json.
        Add the collection before adding users to collect.
        $ cat collection.json 
        {
          "id": "test_collection",
          "credentials": {
            "consumer_key": "<Your Twitter API consumer key>",
            "consumer_secret": "<Your Twitter API consumer secret>",
            "access_token": "<Your Twitter API access token>",
            "access_token_secret": "<Your Twitter API access token secret>"
          },
          "type": "user_timeline",
          "users": {},
          "delete_users_for": [
            "protected",
            "suspended",
            "not_found"
          ]
        }
2. Add credentials to the collection configuration.

        $ python3 twarc_cloud.py collection-config credentials
        Added credentials to collection.json.

    This adds the Twitter API keys that you acquired earlier with Twarc.

3. Add the collection.

        $ python3 twarc_cloud.py collection add
        Collection added.
        Don't forget to start or schedule the collection.
        
   This copies the collection configuration file to your S3 bucket.
   
4. Add users to the collection.

        $ python3 twarc_cloud.py collection-config screennames @justin_littman @not_justin_littman
        Getting users ids for screen names. This may take some time ...
        Added screen names to collection.json.
        Following screen names where not found:
        not_justin_littman

    Twarc-cloud will notify you if any of the users cannot be found. You can also add users by user id and load them from
    files.

5. Update the collection.

        $ python3 twarc_cloud.py collection-config update
        Collection configuration updated.
        
6. Schedule the collection.

        $ python3 twarc_cloud.py collection schedule test_collection "rate(7 days)"
        Scheduled

That's it! A harvest will be performed immediately and then again every 7 days.

## Download the collection

        $ python3 twarc_cloud.py collection download test_collection
        Collection downloaded to download/twarc-cloud/collections/test_collection
        
        $ find download/twarc-cloud2/collections/test_collection -type f
        download/twarc-cloud2/collections/test_collection/harvests/2019/03/09/15/35/07/tweets-20190309153508.jsonl.gz
        download/twarc-cloud2/collections/test_collection/harvests/2019/03/09/15/35/07/users.jsonl
        download/twarc-cloud2/collections/test_collection/harvests/2019/03/09/15/35/07/manifest-sha1.txt
        download/twarc-cloud2/collections/test_collection/harvests/2019/03/09/15/35/07/user_changes.json
        download/twarc-cloud2/collections/test_collection/harvests/2019/03/09/15/35/07/collection.json
        download/twarc-cloud2/collections/test_collection/harvests/2019/03/09/15/35/07/harvest.json
        download/twarc-cloud2/collections/test_collection/changesets/change-20190309153326.json
        download/twarc-cloud2/collections/test_collection/changesets/change-20190309153507.json
        download/twarc-cloud2/collections/test_collection/changesets/change-20190309153304.json
        download/twarc-cloud2/collections/test_collection/collection.json
        download/twarc-cloud2/collections/test_collection/last_harvest.json

Some explanation:
* `download/twarc-cloud2/collections/test_collection/harvests/2019/03/09/15/35/07/` contains the files created by the harvest.
    * `tweets-20190309153508.jsonl.gz` contains the tweets as in a newline-delimited, gzip compressed JSON format as 
       retrieved from Twitter's API. In this case there is only one file; depending on the number of tweets and how long
       a harvest takes, there may be multiple files.
    * `users.jsonl` contains the users in a newline-delimited JSON format as retrieved from Twitter's API.
    * `manifest-sha1.txt` contains a SHA1 checksum for each tweet file in the harvest.
    * `user_changes.json` describes any changes that were found for users, e.g., changed screen names.
    * `collection.json` is the collection configuration file used to perform this harvest.
    * `harvest.json` contains information about the harvest such as the number of tweets collected.
* `download/twarc-cloud2/collections/test_collection/changesets/` contains changeset files that record every change made
  to the collection configuration.
  
## Stop the collection

        $ python twarc_cloud.py collection stop test_collection
        Stopped
