import json
import fileinput
import dateutil.parser
from twarccloud.filepaths_helper import get_collection_config_filepath, get_changeset_file, get_changesets_path
from twarccloud.collection_config import config_template
from twarccloud.aws.aws_helper import sync_changesets
from twarccloud.aws.s3 import download_file, upload_json, download_json
from twarccloud.collection_config import CollectionConfig
from twarccloud.changeset_helper import describe_changes
from twarccloud.exceptions import TwarcCloudException
from twarccloud.config_helpers import get_twitter_keys, bucket_value


def add_collection_config_subparser(subparsers):
    collection_config_parser = subparsers.add_parser('collection-config',
                                                     help='Collection configuration-related commands.')
    collection_config_subparser = collection_config_parser.add_subparsers(help='sub-command help', dest='subcommand')

    # Create collection template
    collection_config_template_parser = collection_config_subparser.add_parser('template',
                                                                               help='Create a template for a '
                                                                                    'collection configuration file.')
    collection_config_template_parser.add_argument('type', choices=['user_timeline', 'filter', 'search'],
                                                   help='Type of collection.')
    collection_config_template_parser.add_argument('--id', help='An identifier for the collection.')

    # Download collection config
    collection_config_download_parser = collection_config_subparser.add_parser('download',
                                                                               help='Download collection configuration '
                                                                                    'file.')
    collection_config_download_parser.add_argument('collection_id')
    collection_config_download_parser.add_argument('--bucket')

    # Update collection config
    collection_config_update_parser = collection_config_subparser.add_parser('update',
                                                                             help='Update a collection config.')
    collection_config_update_parser.add_argument('--collection-config-filepath', default='collection.json',
                                                 help='Filepath of collection configuration file. Default is '
                                                      'collection.json.')
    collection_config_update_parser.add_argument('--bucket')

    # Describe collection config changes
    collection_config_change_parser = collection_config_subparser.add_parser('changes',
                                                                             help='Describe changes made to a '
                                                                                  'collection config.')
    collection_config_change_parser.add_argument('collection_id')
    collection_config_change_parser.add_argument('--bucket')
    collection_config_change_parser.add_argument('--temp', default='temp', help='Path for temporary files.')
    collection_config_change_parser.add_argument('--deletes-only', action='store_true', help='Only describe deletes.')

    # Add user_ids
    collection_config_user_ids_parser = collection_config_subparser.add_parser('userids',
                                                                               help='Add user ids to a user timeline '
                                                                                    'collection config file.')
    collection_config_user_ids_parser.add_argument('--collection-config-filepath', default='collection.json',
                                                   help='Filepath of collection configuration file. Default is '
                                                        'collection.json.')
    collection_config_user_ids_parser.add_argument('user_ids', nargs='*',
                                                   help="One or more user ids, separated by spaces.")

    collection_config_user_id_files_parser = collection_config_subparser.add_parser('userid-files',
                                                                                    help='Add user ids to a user '
                                                                                         'timeline collection config '
                                                                                         'file from files.')
    collection_config_user_id_files_parser.add_argument('--collection-config-filepath', default='collection.json',
                                                        help='Filepath of collection configuration file. Default is '
                                                             'collection.json.')
    collection_config_user_id_files_parser.add_argument('files', nargs='*',
                                                        help='Filepaths of text file(s) containing user ids. If none '
                                                             'are provided, uses stdin.')

    # Add screen_names
    collection_config_screen_names_parser = collection_config_subparser.add_parser('screennames',
                                                                                   help='Add screen names to a user '
                                                                                        'timeline collection config '
                                                                                        'file.')
    collection_config_screen_names_parser.add_argument('--collection-config-filepath', default='collection.json',
                                                       help='Filepath of collection configuration file. Default is '
                                                            'collection.json.')
    collection_config_screen_names_parser.add_argument('screen_names', nargs='*',
                                                       help="One or more screen names, separated by spaces.")

    collection_config_screen_name_files_parser = collection_config_subparser.add_parser('screenname-files',
                                                                                        help='Add screen names to a '
                                                                                             'user timeline collection '
                                                                                             'config file from files.')
    collection_config_screen_name_files_parser.add_argument('--collection-config-filepath', default='collection.json',
                                                            help='Filepath of collection configuration file. Default '
                                                                 'is collection.json.')
    collection_config_screen_name_files_parser.add_argument('files', nargs='*',
                                                            help='Filepaths of text file(s) containing screen names. '
                                                                 'If none are provided, uses stdin.')

    # Add keys
    collection_config_keys_parser = collection_config_subparser.add_parser('keys',
                                                                           help='Add Twitter keys '
                                                                                'managed by Twarc to a '
                                                                                'collection config file.')
    collection_config_keys_parser.add_argument('--collection-config-filepath', default='collection.json',
                                               help='Filepath of collection configuration file. Default is '
                                                    'collection.json.')
    collection_config_keys_parser.add_argument('--twarc-config-filepath',
                                               help='Filepath of Twarc keys configuration file. Default '
                                                    'is ~/.twarc.')
    collection_config_keys_parser.add_argument('--profile',
                                               help='Profile within the Twarc configuration file. Not necessary'
                                                    'if Twarc configuration only has one set of keys.')
    return collection_config_parser


def handle_collection_config_command(args, ini_config, collection_config_parser):
    if args.subcommand == 'template':
        collection_config_template_command(args.type, collection_id=args.id)
    elif args.subcommand == 'download':
        collection_config_download_command(bucket_value(args, ini_config), args.collection_id)
    elif args.subcommand == 'update':
        collection_config_update_command(bucket_value(args, ini_config), args.collection_config_filepath)
    elif args.subcommand == 'changes':
        collection_config_changes_command(bucket_value(args, ini_config), args.collection_id, args.temp,
                                          args.deletes_only)
    elif args.subcommand == 'userids':
        collection_config_user_ids_command(args.collection_config_filepath, args.user_ids)
    elif args.subcommand == 'userid-files':
        collection_config_user_ids_command(args.collection_config_filepath,
                                           fileinput.input(files=args.files if args.files else ('-',)))
    elif args.subcommand == 'screennames':
        collection_config_screen_names_command(args.collection_config_filepath, args.screen_names)
    elif args.subcommand == 'screenname-files':
        collection_config_screen_names_command(args.collection_config_filepath,
                                               fileinput.input(files=args.files if args.files else ('-',)))
    elif args.subcommand == 'keys':
        collection_config_keys_command(args.collection_config_filepath, args.twarc_config_filepath,
                                       args.profile)
    else:
        collection_config_parser.print_help()
        exit(1)


def collection_config_template_command(collection_type, collection_id=None):
    with open('collection.json', 'w') as file:
        json.dump(config_template(collection_type, collection_id=collection_id), file, indent=2)
    print('Template written to collection.json.')
    if collection_type == 'user_timeline':
        print('Add the collection before adding users to collect.')


def collection_config_download_command(bucket, collection_id):
    download_file(bucket, get_collection_config_filepath(collection_id), 'collection.json')
    print('Downloaded to collection.json.')


def collection_config_update_command(bucket, collection_config_filepath):
    new_config = load_collection_config(collection_config_filepath)
    collection_config_update(bucket, collection_config_filepath)
    print('Collection configuration updated.')
    if new_config['type'] == 'filter':
        print('Stop and start the collection for the changes to go into effect.')


def collection_config_user_ids_command(collection_config_filepath, user_ids):
    collection_config = load_collection_config(collection_config_filepath)
    assert_collection_type(collection_config, ('user_timeline',))
    collection_config.add_users_by_user_ids((user_id.rstrip() for user_id in user_ids))
    assert_collection_config_valid(collection_config)
    _write_collection_config(collection_config_filepath, collection_config)
    print('Added user ids to {}.'.format(collection_config_filepath))


def collection_config_screen_names_command(collection_config_filepath, screen_names):
    collection_config = load_collection_config(collection_config_filepath)
    assert_collection_type(collection_config, ('user_timeline',))
    print('Getting users ids for screen names. This may take some time ...')
    not_found_screen_names = collection_config.add_users_by_screen_names(
        (screen_name.rstrip() for screen_name in screen_names))
    assert_collection_config_valid(collection_config)
    _write_collection_config(collection_config_filepath, collection_config)
    print('Added screen names to {}.'.format(collection_config_filepath))
    if not_found_screen_names:
        print('Following screen names where not found:')
        for screen_name in not_found_screen_names:
            print(screen_name)


def collection_config_keys_command(collection_config_filepath, twarc_config, profile):
    collection_config = load_collection_config(collection_config_filepath)
    collection_config['keys'] = get_twitter_keys(profile=profile, twarc_config=twarc_config)
    assert_collection_config_valid(collection_config)
    _write_collection_config(collection_config_filepath, collection_config)
    print('Added keys to {}.'.format(collection_config_filepath))


def collection_config_changes_command(bucket, collection_id, temp_path, deletes_only):
    sync_changesets(temp_path, collection_id, bucket, clean=False)
    for change in describe_changes(get_changesets_path(collection_id, collections_path=temp_path),
                                   deletes_only=deletes_only):
        print(change)


def load_collection_config(collection_config_filepath):
    # Load collection config
    with open(collection_config_filepath) as file:
        new_config = CollectionConfig(json.load(file))
    return new_config


def collection_config_update(bucket, collection_config_filepath, add=False):
    new_config = load_collection_config(collection_config_filepath)
    # Make sure the collection config is valid.
    assert_collection_config_valid(new_config)
    # If the collection already exists, read existing collection_config.
    if add:
        orig_config = CollectionConfig(id=new_config['id'], type=new_config['type'])
    else:
        orig_config = get_collection_config(bucket, new_config['id'])

    # Create the changeset.
    changeset = orig_config.diff(new_config)
    assert_has_changes(changeset)
    # If existing collection config has timestamp, compare timestamps.
    if 'timestamp' in orig_config and orig_config['timestamp'] != new_config.get('timestamp'):
        if not _verify_changes(changeset):
            print('Cancelling')
            return
    # Set timestamp using diff timestamp on new collection config.
    new_config['timestamp'] = changeset['change_timestamp']
    # Write new collection config and diff to bucket.
    _put_collection_config(bucket, new_config)
    _put_changeset(bucket, orig_config['id'], changeset)
    _write_collection_config(collection_config_filepath, new_config)


def _verify_changes(changeset):
    print('There is a new collection configuration file.')
    print('Here are the changes that will be applied: {}'.format(json.dumps(changeset, indent=2)))
    return input('Proceed? (Y/N) ').lower() == 'y'


def _write_collection_config(collection_config_filepath, collection_config):
    with open(collection_config_filepath, 'w') as file:
        json.dump(collection_config, file, indent=2)


def _put_collection_config(bucket, collection_config):
    upload_json(bucket, get_collection_config_filepath(collection_config['id']), collection_config)


def _put_changeset(bucket, collection_id, changeset):
    change_timestamp = dateutil.parser.parse(changeset['change_timestamp'])
    upload_json(bucket, get_changeset_file(collection_id, change_timestamp), changeset)


def assert_collection_config_valid(collection_config):
    reasons = collection_config.invalid_reasons()
    if not reasons:
        return
    print('Invalid reasons:')
    for reason in reasons:
        print(reason)
    raise TwarcCloudException('Collection configuration is invalid.')


def assert_has_changes(changeset):
    if not changeset.has_changes():
        raise TwarcCloudException('No changes in collection configuration.')


def assert_collection_type(collection_config, collection_types):
    if collection_config['type'] not in collection_types:
        raise TwarcCloudException('Collection is not a {}.'.format(' or '.join(collection_types)))


def get_collection_config(bucket, collection_id):
    return CollectionConfig(download_json(bucket, get_collection_config_filepath(collection_id)))
