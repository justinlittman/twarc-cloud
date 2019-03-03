# pylint: disable=inconsistent-return-statements
import uuid
from . import aws_resource, aws_client
from .container import send_stop, wait_for_stopped


# Run a task.
def run_task(task_definition_arn, aws_config):
    aws_client('ecs').run_task(
        cluster=aws_config.cluster,
        taskDefinition=task_definition_arn,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    aws_config.subnet,
                ],
                'securityGroups': [
                    aws_config.security_group,
                ],
                'assignPublicIp': 'ENABLED'
            }
        },
        propagateTags='TASK_DEFINITION'
    )


# Schedule a task.
def schedule_task(task_definition_arn, rule_name, schedule, aws_config):
    # Note that this will replace existing rules and targets.
    aws_client('events').put_rule(
        Name=rule_name,
        ScheduleExpression=schedule,
        State='DISABLED',
        Description=rule_name.replace('_', ' '),
        RoleArn=aws_config.event_role_arn
    )
    aws_client('events').put_targets(
        Rule=rule_name,
        Targets=[{
            'Id': '{}_target'.format(rule_name),
            'Arn': _cluster_arn(aws_config),
            'RoleArn': aws_config.event_role_arn,
            'EcsParameters': {
                'TaskDefinitionArn': task_definition_arn,
                'TaskCount': 1,
                'LaunchType': 'FARGATE',
                'NetworkConfiguration': {
                    'awsvpcConfiguration': {
                        'Subnets': [
                            aws_config.subnet,
                        ],
                        'SecurityGroups': [
                            aws_config.security_group,
                        ],
                        'AssignPublicIp': 'ENABLED'
                    }
                }
            },
        }]
    )
    aws_client('events').enable_rule(
        Name=rule_name
    )


# Unschedule a scheduled task.
def stop_schedule(rule_name):
    aws_client('events').disable_rule(
        Name=rule_name
    )


# Returns an iterator of scheduled tasks with the provided rule name prefix.
def list_scheduled_tasks(rule_prefix, enabled_only=False):
    response_iterator = aws_client('events').get_paginator('list_rules').paginate(
        NamePrefix=rule_prefix
    )
    for response in response_iterator:
        for rule in response['Rules']:
            if not enabled_only or rule['State'] == 'ENABLED':
                yield rule


# Register a task definition.
def register_task_definition(task_definition_family, tags, command, aws_config,
                             skip_if_exists=True):

    if skip_if_exists and _has_task_definition(task_definition_family):
        return _task_definition_arn(task_definition_family)
    response = aws_client('ecs').register_task_definition(
        family=task_definition_family,
        taskRoleArn=aws_config.task_role_arn,
        executionRoleArn=aws_config.task_execution_role_arn,
        networkMode='awsvpc',
        containerDefinitions=[
            {
                'name': 'twarc-cloud-container',
                'image': 'justinlittman/twarc-cloud:{}'.format(aws_config.image_tag),
                'essential': True,
                'command': command,
                'environment': _environment(aws_config),
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': aws_config.log_group,
                        'awslogs-region': _cluster_region(aws_config),
                        'awslogs-stream-prefix': task_definition_family
                    }
                },
            },
        ],
        requiresCompatibilities=['FARGATE'],
        cpu='256',
        memory='512',
        tags=tags
    )
    return response['taskDefinition']['taskDefinitionArn']


def _environment(aws_config):
    environment = [
        {
            'name': 'secret_key',
            'value': uuid.uuid4().hex
        }
    ]
    if aws_config.honeybadger_key:
        environment.append({
            'name': 'HONEYBADGER_API_KEY',
            'value': aws_config.honeybadger_key
        })
    return environment

# Returns True if service exists.
def service_exists(service_name, aws_config):
    response = aws_client('ecs').describe_services(
        cluster=aws_config.cluster,
        services=[service_name]
    )
    for service in response['services']:
        if service['status'] != 'INACTIVE':
            return True
    return False


# Create and start a service.
def start_service(task_definition_arn, tags, service_name, aws_config):
    aws_client('ecs').create_service(
        cluster=aws_config.cluster,
        serviceName=service_name,
        taskDefinition=task_definition_arn,
        desiredCount=1,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    aws_config.subnet,
                ],
                'securityGroups': [
                    aws_config.security_group,
                ],
                'assignPublicIp': 'ENABLED'
            }
        },
        schedulingStrategy='REPLICA',
        deploymentController={
            'type': 'ECS'
        },
        tags=tags,
        propagateTags='TASK_DEFINITION'
    )


# Stop a service.
def stop_service(service_name, task, aws_config):
    secret_key = _env_variable(task, 'secret_key')
    dns_name = public_ip(task)
    send_stop(dns_name, secret_key)
    wait_for_stopped(dns_name, secret_key)
    _delete_service(service_name, task['taskArn'], aws_config)


def _delete_service(service_name, task_arn, aws_config):
    aws_client('ecs').update_service(
        cluster=aws_config.cluster,
        service=service_name,
        desiredCount=0)
    waiter = aws_client('ecs').get_waiter('tasks_stopped')
    waiter.wait(
        cluster=aws_config.cluster,
        tasks=[
            task_arn,
        ]
    )
    aws_client('ecs').delete_service(
        cluster=aws_config.cluster,
        service=service_name,
        force=False
    )


# List all tasks running on an ECS cluster.
def list_tasks(aws_config):
    paginator = aws_client('ecs').get_paginator('list_tasks')
    for list_result in paginator.paginate(cluster=aws_config.cluster):
        if list_result['taskArns']:
            describe_task_response = aws_client('ecs').describe_tasks(
                cluster=aws_config.cluster,
                tasks=list_result['taskArns'],
                include=['TAGS']
            )
            for task in describe_task_response['tasks']:
                yield task


# Returns tags as task
# May require getting from task definition until https://github.com/aws/containers-roadmap/issues/89 is resolved.
def tags_for_task(task):
    return _to_tags_dict(task if task['tags'] else _task_definition(task['taskDefinitionArn']))


# Return tags as a dictionary.
def _to_tags_dict(tagged_obj):
    tags_dict = {}
    for tag in tagged_obj['tags']:
        tags_dict[tag['key']] = tag['value']
    return tags_dict


def _env_variable(task, name):
    task_definition = _task_definition(task['taskDefinitionArn'])
    container = _container(task_definition)
    for env_variable in container['environment']:
        if env_variable['name'] == name:
            return env_variable['value']
    assert False


# Returns the public DNS name for a task's network interface.
def public_ip(task):
    for attachment in task['attachments']:
        for detail in attachment['details']:
            if detail['name'] == 'networkInterfaceId':
                network_interface_id = detail['value']
                network_interface = aws_resource('ec2').NetworkInterface(network_interface_id)
                return network_interface.association_attribute['PublicIp']
    assert False


def _container(task_definition):
    for container in task_definition['taskDefinition']['containerDefinitions']:
        if container['name'] == 'twarc-cloud-container':
            return container
    assert False


def _task_definition(task_definition_arn):
    return aws_client('ecs').describe_task_definition(
        taskDefinition=task_definition_arn,
        include=[
            'TAGS',
        ]
    )


def _has_task_definition(task_definition_family):
    response = aws_client('ecs').list_task_definition_families(
        familyPrefix=task_definition_family,
        status='ACTIVE'
    )
    for family in response['families']:
        if family == task_definition_family:
            return True
    return False


def _task_definition_arn(task_definition_family):
    response = aws_client('ecs').describe_task_definition(
        taskDefinition=task_definition_family
    )
    return response['taskDefinition']['taskDefinitionArn']


def _cluster_arn(aws_config):
    response = aws_client('ecs').describe_clusters(
        clusters=[aws_config.cluster]
    )
    for cluster in response['clusters']:
        if cluster['clusterName'] == aws_config.cluster:
            return cluster['clusterArn']
    assert False


def _cluster_region(aws_config):
    return _cluster_arn(aws_config).split(':')[3]
