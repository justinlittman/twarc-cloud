# Requirements

## Python 3 and pip 3

    $ python3 -V
    Python 3.7.0
    $ pip3 -V
    pip 18.0 from /usr/local/lib/python3.7/site-packages/pip (python 3.7)
    
It is recommended that you use [virtualenv](https://virtualenv.pypa.io) or similar to isolate your python environment.

    $ virtualenv -p python3 ENV
    $ source ENV/bin/activate
    
## Terraform

Terraform is used to manager your AWS environment. Download instructions are available [here](https://www.terraform.io/downloads.html).

On a Mac, you can `brew install terraform`.

    $ terraform -v
    Terraform v0.11.11
    
## Twitter API developer account and app

To access the Twitter API, you need a [developer account](https://developer.twitter.com/en/apply-for-access). Note that
once you apply, receiving approval will take at least several days. Filling out the application as completely and 
accurately as possible will speed up the approval process.

Once you have a developer account, you can create an app for Twarc-Cloud. Please make sure to give your application a
unique name, e.g., _twarc-cloud-justinlittman_. Twarc-Cloud will require the consumer API keys for the app.

## AWS account

To run Twarc-Cloud, you need an [Amazon Web Services](https://aws.amazon.com/) account.

By default, you will have a root user. For security reasons, it is recommended that you create a separate user with 
the _AdministratorAccess_ policy and use that user with Twarc-Cloud.

For either the root user or the administrator user, Twarc-Cloud will require access keys.

For the root user, in the AWS Console, this is under your account > My Security Credentials > Access keys.

For an administrator user, in the AWS Console, this is under Services > IAM > Users then select your user and then
Security credentials > Access keys.

_It is very important that you keep these keys secure._ If they are ever compromised, you can revoke them from the AWS
Console.

## Twarc-Cloud

Either clone Twarc-Cloud:

    $ git clone https://github.com/justinlittman/twarc-cloud.git
    
or [download](https://github.com/justinlittman/twarc-cloud/archive/master.zip) and unzip it.

Then install the requirements:

    $ cd twarc-cloud
    $ pip install -r requirements.txt
    
## Honeybadger (optional)

Honeybadger provides notification of errors that occur during harvesting. It is recommended that you [create an account](https://app.honeybadger.io/users/sign_up?plan_id=30151).
Note that the Solo plan is sufficient.

Once you have created an account, create a project for Twarc-Cloud. Twarc-Cloud will require the project's API key.
