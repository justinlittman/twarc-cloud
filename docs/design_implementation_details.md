# Design and implementation details

## Design principles

* Serverless: No server to maintain or pay for when not in use.
* Use as few AWS services as possible: To reduce complexity and cost.

Thus, there is no web server, database, message queue, etc.

## AWS
Harvests are run as Fargate Elastic Container Service (ECS) tasks with a single container.
* Filter stream are setup as ECS services so that they are restarted if the container fails.
* Scheduled harvests are setup as Cloudwatch Events.

S3 is used to store collections. Twarc-Cloud has its own bucket.

Twarc-Cloud is deployed in its own VPC and has its own ECS cluster.

## Harvester implementation
It is important that a harvest be able to terminate cleanly, where terminate cleanly means writing all of the necessary
files and uploading them to S3. In particular, it is necessary to be able to interrupt filter streams which run continuously
and are setup as ECS services.

To support interrupting a harvest, the harvester runs a server which supports a `/stop` endpoint, which begins
the process of stopping the harvest. It also supports a `/is_stopped` endpoint which returns if the harvest is
done stopping. Thus, the process for stopping a filter stream is:
1. twarc_cloud.py invokes `/stop`.
2. The harvester begins stopping the harvest. When the harvest is stopped, the harvester does not exit. (If the harvester
   exited, ECS would start a new container.)
3. twarc_cloud.py polls `/is_stopped` until the harvester is stopped.
4. twarc_cloud.py stop the ECS service.
5. ECS send a terminate signal to the harvester.
6. The harvester exits.

The harvester's server is also used to provide real-time harvest information (the `/` endpoint) to twarc_cloud.py (the `harvest running` command).
