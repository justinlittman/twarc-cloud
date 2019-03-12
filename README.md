# twarc-cloud
[![CircleCI](https://circleci.com/gh/justinlittman/twarc-cloud.svg?style=svg)](https://circleci.com/gh/justinlittman/twarc-cloud)
[![Documentation Status](https://readthedocs.org/projects/twarc-cloud/badge/?version=latest)](https://twarc-cloud.readthedocs.io/en/latest/?badge=latest)

Docs: [http://twarc-cloud.readthedocs.io/](http://twarc-cloud.readthedocs.io/)

An AWS-friendly wrapper for Twarc for collecting Twitter data from Twitter's API.

Twarc-Cloud is a CLI that manages AWS Fargate Elastic Container Service (ECS) tasks that retrieve Twitter data from Twitter's API
and stores in AWS S3 storage.

Collecting from the following Twitter API methods is supported:
* [GET statuses/user_timeline](https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline)
* [GET search/tweets.json](https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets)
* [POST statuses/filter](https://developer.twitter.com/en/docs/tweets/filter-realtime/overview/statuses-filter)

## Design principles

* Serverless: No server to maintain or pay for when not in use.
* Use as few AWS services as possible: To reduce complexity and cost.

Thus, there is no web server, database, message queue, etc.

## AWS costs

As of March 2019, the costs for the used AWS services are:
* [Fargate ECS](https://aws.amazon.com/fargate/pricing/): (1/4 CPU x $0.04048 per CPU per hour) + 1/2 GB x $0.004445 per GB per hour) = $0.012345 per harvest per hour
* [S3](https://aws.amazon.com/s3/pricing/): $0.023 per GB per month

Costs will vary depending on how much data you collect. However, overall it is ridiculously cheap.

## Unit tests and linting
First:
```
pip install pylint
```

then:
```
python -m unittest discover
pylint *.py twarccloud

```

_Twarc-Cloud is currently under-tested; writing new tests is a priority._ 


## Docker
The Docker image [justinlittman/twarc-cloud](https://hub.docker.com/r/justinlittman/twarc-cloud) is set to autobuild on commit:
* `latest` is master.
* `version-<major>` is the most recent tagged major version.
* `version-<major.minor.patch>` is the most recent tagged version.

A Twarc-Cloud harvester running as an ECS task is tied to a major version; each time a new ECS task is started, the most
recent Docker image is pulled. Any breaking change will result in a new major version. 

To manually build and push a Docker image:
```
docker build . -t 'justinlittman/twarc-cloud:latest'
docker push justinlittman/twarc-cloud:latest
```

## Documentation

To install the requirements:
```
pip install sphinx recommonmark sphinx-autobuild sphinx_rtd_theme

```

To run a live version of the docs:
```
cd docs
make livehtml
```

A live version of the docs will available on [http://localhost:8000](http://localhost:8000).

## Release process
1. Update version in `twarccloud/__init__.py`.
2. Commit and push.
3. Tag a release in Github named with the version, e.g., _1.0.0_.

## Acknowledgements

Twarc-Cloud is inspired by and borrows heavily from DocNow's [Twarc](https://github.com/DocNow/twarc) and 
George Washington University Libraries' [Social Feed Manager](http://go.gwu.edu/sfm).
