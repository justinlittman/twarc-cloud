import argparse
import os
import shutil
from twarccloud.filepaths_helper import get_collection_config_filepath, DEFAULT_COLLECTIONS_PATH, get_collection_path
from twarccloud.aws.s3 import list_keys, download_all, file_exists
from twarccloud.aws.ecs import run_task, register_task_definition, schedule_task, service_exists, start_service, \
    stop_schedule, stop_service, list_tasks, tags_for_task, list_scheduled_tasks
from twarccloud.config_helpers import bucket_value
from twarccloud.exceptions import TwarcCloudException
from twarccloud.cli.collection_config import load_collection_config, collection_config_update, \
    assert_collection_type, get_collection_config


def add_collection_subparser(subparsers):
    collection_parser = subparsers.add_parser('collection', help='Collection-related commands.')
    collection_subparser = collection_parser.add_subparsers(help='sub-command help', dest='subcommand')

    # List collections
    collection_list_parser = collection_subparser.add_parser('list', help='List collections')
    collection_list_parser.add_argument('--bucket')

    # Add collection
    collection_add_parser = collection_subparser.add_parser('add', help='Add a new collection.')
    collection_add_parser.add_argument('--bucket')
    collection_add_parser.add_argument('--collection-config-filepath', default='collection.json',
                                       help='Filepath of collection configuration file. Default is collection.json.')

    # Add user_ids/screen names to collection config

    # This is shared by collection once and collection start
    common_collection_start_parser = argparse.ArgumentParser(add_help=False)
    common_collection_start_parser.add_argument('collection_id')
    common_collection_start_parser.add_argument('--bucket')

    # Run-once collection
    collection_subparser.add_parser('once', help='Harvest once.', parents=[common_collection_start_parser])

    # Schedule collection
    collection_schedule_parser = collection_subparser.add_parser('schedule',
                                                                 help='Harvest according to a schedule. Will replace '
                                                                      'an existing schedule.',
                                                                 parents=[common_collection_start_parser])
    # pylint: disable=line-too-long
    collection_schedule_parser.add_argument('schedule',
                                            help='Cron or rate expression, e.g., rate(7 days). See '
                                            'https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html.')

    # Stop schedule
    collection_schedule_stop_parser = collection_subparser.add_parser('stop',
                                                                      help='Stop harvesting according to a schedule.')
    collection_schedule_stop_parser.add_argument('collection_id')
    collection_schedule_stop_parser.add_argument('--bucket')

    # List scheduled
    collection_scheduled_parser = collection_subparser.add_parser('scheduled',
                                                                  help='List scheduled collections.')
    collection_scheduled_parser.add_argument('--bucket')


    # Start stream collection
    collection_subparser.add_parser('filter-start', help='Start filter stream collecting.',
                                    parents=[common_collection_start_parser])

    # Stop stream collection
    collection_stop_stream_parser = collection_subparser.add_parser('filter-stop',
                                                                    help='Stop filter stream collecting.')
    collection_stop_stream_parser.add_argument('collection_id')
    collection_stop_stream_parser.add_argument('--bucket')

    # Download collection
    collection_download_parser = collection_subparser.add_parser('download', help='Download all collection files.')
    collection_download_parser.add_argument('collection_id')
    collection_download_parser.add_argument('--bucket')
    collection_download_parser.add_argument('--collection-path',
                                            help='Path for download. Default is download/<bucket>/<collection_id>.')
    collection_download_parser.add_argument('--clean', action='store_true',
                                            help='Delete any files that have already been downloaded.')

    return collection_parser


def handle_collection_command(args, ini_config, aws_config, collection_parser):
    if args.subcommand == 'list':
        collection_list_command(bucket_value(args, ini_config))
    elif args.subcommand == 'download':
        collection_download_command(bucket_value(args, ini_config), args.collection_id,
                                    local_collection_path=args.collection_path, clean=args.clean)
    elif args.subcommand == 'once':
        collection_once_command(bucket_value(args, ini_config), args.collection_id, aws_config)
    elif args.subcommand == 'schedule':
        collection_schedule_command(bucket_value(args, ini_config), args.collection_id, args.schedule, aws_config)
    elif args.subcommand == 'stop':
        collection_stop_schedule_command(bucket_value(args, ini_config), args.collection_id)
    elif args.subcommand == 'scheduled':
        collection_list_scheduled_command(bucket_value(args, ini_config))
    elif args.subcommand == 'filter-start':
        collection_service_start_command(bucket_value(args, ini_config), args.collection_id, aws_config)
    elif args.subcommand == 'filter-stop':
        collection_service_stop_command(bucket_value(args, ini_config), args.collection_id, aws_config)
    elif args.subcommand == 'add':
        collection_add_command(bucket_value(args, ini_config), args.collection_config_filepath)
    else:
        collection_parser.print_help()
        exit(1)


def collection_list_command(bucket):
    print('Collections:')
    for collection_name in list_keys(bucket, DEFAULT_COLLECTIONS_PATH):
        print(collection_name)


def collection_add_command(bucket, collection_config_filepath):
    new_config = load_collection_config(collection_config_filepath)
    assert_collection_not_exists(bucket, new_config['id'])
    collection_config_update(bucket, collection_config_filepath, add=True)
    print('Collection added.')
    print('Don\'t forget to start or schedule the collection.')


def collection_download_command(bucket, collection_id, local_collection_path=None, clean=False):
    if not local_collection_path:
        local_collection_path = os.path.join('download', bucket, DEFAULT_COLLECTIONS_PATH, collection_id)

    if clean:
        shutil.rmtree(local_collection_path, ignore_errors=True)

    download_all(bucket, get_collection_path(collection_id), local_collection_path)
    print('Collection downloaded to {}'.format(local_collection_path))


def collection_once_command(bucket, collection_id, aws_config):
    assert_collection_exists(bucket, collection_id)
    assert_collection_type(get_collection_config(bucket, collection_id), ('user_timeline', 'search'))
    task_definition_arn = register_task_definition(_task_definition_family(bucket, collection_id, aws_config.image_tag),
                                                   _tags(bucket, collection_id),
                                                   _command(bucket, collection_id, shutdown=True), aws_config,
                                                   skip_if_exists=True)
    run_task(task_definition_arn, aws_config)
    print('Started')


def collection_schedule_command(bucket, collection_id, schedule, aws_config):
    assert_collection_exists(bucket, collection_id)
    assert_collection_type(get_collection_config(bucket, collection_id), ('user_timeline', 'search'))
    task_definition_arn = register_task_definition(_task_definition_family(bucket, collection_id, aws_config.image_tag),
                                                   _tags(bucket, collection_id),
                                                   _command(bucket, collection_id, shutdown=True), aws_config,
                                                   skip_if_exists=True)
    # Note that this will replace existing rules and targets.
    schedule_task(task_definition_arn, _rule_name(bucket, collection_id), schedule, aws_config)
    print('Scheduled')


def collection_stop_schedule_command(bucket, collection_id):
    stop_schedule(_rule_name(bucket, collection_id))
    print('Stopped')


# List all scheduled collections for a bucket.
def collection_list_scheduled_command(bucket):
    scheduled_tasks = list(list_scheduled_tasks('{}_'.format(bucket), enabled_only=True))
    if scheduled_tasks:
        for rule in scheduled_tasks:
            print('{} => {}'.format(rule['Description'], rule['ScheduleExpression']))
    else:
        print('No scheduled tasks.')


def collection_service_start_command(bucket, collection_id, aws_config):
    assert_collection_exists(bucket, collection_id)
    assert_collection_type(get_collection_config(bucket, collection_id), ('filter',))
    assert_no_service(bucket, collection_id, aws_config)
    task_definition_arn = register_task_definition(_task_definition_family(bucket, collection_id, aws_config.image_tag),
                                                   _tags(bucket, collection_id), _command(bucket, collection_id),
                                                   aws_config)
    start_service(task_definition_arn, _tags(bucket, collection_id), _service_name(bucket, collection_id), aws_config)

    print('Started')


def collection_service_stop_command(bucket, collection_id, aws_config):
    assert_collection_exists(bucket, collection_id)
    assert_service(bucket, collection_id, aws_config)

    for task in list_tasks(aws_config):
        tags = tags_for_task(task)
        if bucket == tags.get('bucket') and collection_id == tags.get('collection_id'):
            print('Stopping ...')
            stop_service(_service_name(bucket, collection_id), task, aws_config)
            print('Stopped')
            return

    print('Running harvester for {} not found'.format(collection_id))


def collection_exists(bucket, collection_id):
    return file_exists(bucket, get_collection_config_filepath(collection_id))


def _rule_name(bucket, collection_id):
    return '{}_{}_schedule'.format(bucket, collection_id)


def _service_name(bucket_id, collection_id):
    return '{}_{}_service'.format(bucket_id, collection_id)


def _task_definition_family(bucket, collection_id, image_tag):
    return 'twarc-cloud_{}_{}_{}'.format(bucket, collection_id, image_tag)


def _command(bucket, collection_id, monitor=False, shutdown=False):
    command = ['aws', 'harvester', bucket, collection_id]
    if monitor:
        command.append('--monitor')
    if shutdown:
        command.append('--shutdown')
    return command


def _tags(bucket, collection_id):
    return [
        {
            'key': 'bucket',
            'value': bucket
        },
        {
            'key': 'collection_id',
            'value': collection_id
        }
    ]


def assert_collection_exists(bucket, collection_id):
    if not collection_exists(bucket, collection_id):
        raise TwarcCloudException('Collection does not exist.')


def assert_collection_not_exists(bucket, collection_id):
    if collection_exists(bucket, collection_id):
        raise TwarcCloudException('Collection already exists.')


def assert_no_service(bucket, collection_id, aws_config):
    if service_exists(_service_name(bucket, collection_id), aws_config):
        raise TwarcCloudException('Collection already started.')


def assert_service(bucket, collection_id, aws_config):
    if not service_exists(_service_name(bucket, collection_id), aws_config):
        raise TwarcCloudException('Collection not already started.')
