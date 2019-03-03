import dateutil.parser
from hurry.filesize import size
from twarccloud.filepaths_helper import get_last_harvest_file, get_harvest_info_file, get_user_changes_filepath
from twarccloud.aws.s3 import file_exists, download_json
from twarccloud.aws.ecs import list_tasks, tags_for_task, public_ip
from twarccloud.aws.container import fetch_info
from twarccloud.config_helpers import bucket_value
from twarccloud.exceptions import TwarcCloudException
from twarccloud.cli.collection_config import get_collection_config


def add_harvest_subparser(subparsers):
    # Harvest-related
    harvest_parser = subparsers.add_parser('harvest', help='Harvest-related commands.')
    harvest_subparser = harvest_parser.add_subparsers(help='sub-command help', dest='subcommand')

    # Running harvests
    harvest_subparser.add_parser('list', help='List running harvests')

    # Info on a running harvester
    harvest_info_parser = harvest_subparser.add_parser('running',
                                                       help='Get information on a running harvester for a collection.')
    harvest_info_parser.add_argument('collection_id')
    harvest_info_parser.add_argument('--bucket')

    harvest_last_parser = harvest_subparser.add_parser('last',
                                                       help='Get information on the last completed harvester for a '
                                                            'collection.')
    harvest_last_parser.add_argument('collection_id')
    harvest_last_parser.add_argument('--bucket')
    return harvest_parser


def handle_harvest_command(args, aws_config, ini_config, harvest_parser):
    if args.subcommand == 'list':
        harvest_list_command(aws_config)
    elif args.subcommand == 'running':
        harvest_running_command(bucket_value(args, ini_config), args.collection_id, aws_config)
    elif args.subcommand == 'last':
        harvest_last_command(bucket_value(args, ini_config), args.collection_id)
    else:
        harvest_parser.print_help()
        exit(1)


def harvest_list_command(aws_config):
    tasks = list(list_tasks(aws_config))
    if tasks:
        for task in tasks:
            tags = tags_for_task(task)
            print('{} => Bucket: {}. Status: {}'.format(tags.get('collection_id', 'Unknown'),
                                                        tags.get('bucket', 'Unknown'),
                                                        task['lastStatus']))
    else:
        print('No running harvests.')


def harvest_running_command(bucket, collection_id, aws_config):
    dns_name = public_ip(_task(bucket, collection_id, aws_config))
    harvest_info = fetch_info(dns_name)
    _print_harvest_info(bucket, harvest_info)


def harvest_last_command(bucket, collection_id):
    last_harvest_filepath = get_last_harvest_file(collection_id)
    if not file_exists(bucket, last_harvest_filepath):
        print('Cannot find last harvester for this collection.')
        return

    last_harvest_timestamp = dateutil.parser.parse(download_json(bucket, last_harvest_filepath)['harvest_id'])
    harvest_info = download_json(bucket, get_harvest_info_file(collection_id, last_harvest_timestamp))
    _print_harvest_info(bucket, harvest_info)

    if get_collection_config(bucket, collection_id)['type'] == 'user_timeline':
        user_changes_file = get_user_changes_filepath(collection_id, last_harvest_timestamp)
        user_changes = download_json(bucket, user_changes_file)
        if user_changes:
            for change_details in user_changes:
                print('User {} ({}): {}'.format(change_details['user_id'], change_details.get('screen_name'),
                                                change_details['change']))
        else:
            print('No user changes.')


def _print_harvest_info(bucket, harvest_info):
    print(
        '{} => Bucket: {}. Harvest timestamp: {}. Tweets: {:,}. Files: {:,} ({})'.format(harvest_info['collection_id'],
                                                                                         bucket,
                                                                                         harvest_info[
                                                                                             'harvest_timestamp'],
                                                                                         harvest_info['tweets'],
                                                                                         harvest_info['files'],
                                                                                         size(harvest_info[
                                                                                             'file_bytes'])))


def _task(bucket, collection_id, aws_config):
    for task in list_tasks(aws_config):
        tags = tags_for_task(task)
        if tags.get('bucket') == bucket and tags.get('collection_id') == collection_id:
            return task
    raise TwarcCloudException('Task not found.')
