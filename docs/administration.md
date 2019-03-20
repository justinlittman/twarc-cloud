# Administration

## Unlocking a collection
To prevent multiple harvests being performed concurrently for a collection, a lock file (`lock.json`) is written to a
collection's base directory during a harvest. Harvesters check to see if the lock file is present before beginning.

If a harvest raises a `LockedException` this indicates that a harvest is currently in process or a previous harvest
exited uncleanly.

If a collection is locked because multiple harvests are attempting to run concurrently then adjust the schedule.

If a collection is locked because a previous harvest exited uncleanly, then force it be unlocked. To unlock, delete `lock.json`
or execute `tweet_harvester`'s `aws unlock` command. For example:

        $ python3 tweet_harvester.py aws unlock twarc_cloud test_collection
        Unlocked
        
## Removing AWS environment

Before removing your AWS environment, all of the files in your S3 bucket must be deleted. This can be done from the AWS
console or AWS CLI.

Your AWS environment can then be removed with `terraform destroy`.

## Logs
Logs for harvest ECS tasks are available from AWS Cloudwatch (Services > Cloudwatch > Logs) in the `twarc-cloud-container`
log group.