import json
import io
import os
import botocore
from twarccloud.aws import aws_resource
from twarccloud import log


# Iterable of all keys at a path
def list_keys(bucket, path):
    paginator = aws_resource('s3').meta.client.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=_prefix(path)):
        for prefix in result.get('CommonPrefixes'):
            yield prefix.get('Prefix').split('/')[1]


# Download all files at a path and descendants.
def download_all(bucket, path, local_path):
    paginator = aws_resource('s3').meta.client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket, Prefix=_prefix(path)):
        for obj in result['Contents']:
            object_key = obj['Key']
            if object_key.endswith('/'):
                continue

            dest_filepath = os.path.join(local_path, _remove_prefix(object_key, path))
            if os.path.isfile(dest_filepath) and os.path.getsize(dest_filepath) == obj['Size']:
                log.debug('Skipping downloading s3://%s/%s to %s', bucket, object_key, dest_filepath)
            else:
                log.debug('Downloading s3://%s/%s to %s', bucket, object_key, dest_filepath)
                os.makedirs(os.path.dirname(dest_filepath), exist_ok=True)
                aws_resource('s3').Bucket(bucket).download_file(object_key, dest_filepath)


# Download a single file.
def download_file(bucket, filepath, local_filepath):
    aws_resource('s3').Bucket(bucket).download_file(filepath, local_filepath)


# Upload an object as json
def upload_json(bucket, filepath, obj):
    body = json.dumps(obj, indent=2).encode('utf-8')
    aws_resource('s3').Bucket(bucket).put_object(Body=body, Key=filepath)


# Download json as an object
def download_json(bucket, filepath):
    file = io.BytesIO()
    aws_resource('s3').Bucket(bucket).download_fileobj(filepath, file)
    return json.loads(file.getvalue().decode('utf-8'))


def _prefix(path):
    return path + '/' if not path.endswith('/') else ''


def _remove_prefix(string, prefix):
    return string[len(_prefix(prefix)):] if string.startswith(prefix) else string


# Returns True if a file exists.
def file_exists(bucket, key):
    try:
        aws_resource('s3').meta.client.head_object(Bucket=bucket, Key=key)
        return True
    except botocore.exceptions.ClientError as exception:
        if exception.response['Error']['Code'] == "404":
            return False
        raise
