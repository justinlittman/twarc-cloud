import shutil
import os
import botocore
from twarccloud.filepaths_helper import get_collection_config_filepath, get_lock_file, get_collection_path, \
    get_changesets_path
from twarccloud.aws import aws_resource


# Synchronize collection configuration from bucket to local.
def sync_collection_config(local_collections_path, collection_id, bucket):
    local_collection_path = get_collection_path(collection_id, collections_path=local_collections_path)
    shutil.rmtree(local_collection_path, ignore_errors=True)
    os.makedirs(local_collection_path)

    local_collection_config_filepath = get_collection_config_filepath(collection_id,
                                                                      collections_path=local_collections_path)
    bucket_collection_config_filepath = get_collection_config_filepath(collection_id)

    # Collection config file
    aws_resource('s3').Bucket(bucket).download_file(bucket_collection_config_filepath, local_collection_config_filepath)
    # Lock
    try:
        local_lock_filepath = get_lock_file(collection_id, collections_path=local_collections_path)
        bucket_lock_filepath = get_lock_file(collection_id)
        aws_resource('s3').Bucket(bucket).download_file(bucket_lock_filepath, local_lock_filepath)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] != "404":
            raise


# Synchronize changesets file from bucket to local.
def sync_changesets(local_collections_path, collection_id, bucket, clean=False):
    local_changesets_path = get_changesets_path(collection_id, collections_path=local_collections_path)
    if clean:
        shutil.rmtree(local_changesets_path, ignore_errors=True)
    os.makedirs(local_changesets_path, exist_ok=True)

    bucket_changesets_path = get_changesets_path(collection_id)
    paginator = aws_resource('s3').meta.client.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/',
                                     Prefix='{}/'.format(bucket_changesets_path)):
        for content in result.get('Contents'):
            key = content['Key']
            changeset_filename = os.path.basename(key)
            local_changeset_filepath = '{}/{}'.format(local_changesets_path, changeset_filename)
            if not os.path.exists(local_changeset_filepath):
                aws_resource('s3').Bucket(bucket).download_file(key, local_changeset_filepath)


# Synchronize collection configuration file from bucket to local.
def sync_collection_config_file(local_collections_path, collection_id, bucket):
    local_collection_path = get_collection_path(collection_id, collections_path=local_collections_path)
    os.makedirs(local_collection_path, exist_ok=True)

    local_collection_config_filepath = get_collection_config_filepath(collection_id,
                                                                      collections_path=local_collections_path)
    bucket_collection_config_filepath = get_collection_config_filepath(collection_id)

    # Collection config file
    aws_resource('s3').Bucket(bucket).download_file(bucket_collection_config_filepath, local_collection_config_filepath)
