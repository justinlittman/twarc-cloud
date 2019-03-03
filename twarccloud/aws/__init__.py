import boto3

_AWS_RESOURCES = {}
_AWS_CLIENTS = {}


def aws_resource(resource_type):
    if resource_type not in _AWS_RESOURCES:
        _AWS_RESOURCES[resource_type] = boto3.resource(resource_type)
    return _AWS_RESOURCES[resource_type]


def aws_client(client_type):
    if client_type not in _AWS_CLIENTS:
        _AWS_CLIENTS[client_type] = boto3.client(client_type)
    return _AWS_CLIENTS[client_type]
