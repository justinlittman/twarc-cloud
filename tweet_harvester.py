import argparse
from threading import Event
from queue import Queue
from datetime import datetime
import json
import os
from time import sleep
import signal
import copy
import dateutil.parser
from twarccloud.harvester.server_thread import ServerThread
from twarccloud.harvester.twarc_thread import TwarcThread
from twarccloud.filepaths_helper import get_harvest_path, get_lock_file, get_collection_config_filepath, \
    get_harvest_info_file, get_changeset_file
from twarccloud.harvester.file_mover_thread import S3FileMoverThread
from twarccloud.harvester.collection_lock import CollectionLock, assert_locked
from twarccloud.aws.aws_helper import sync_collection_config, sync_collection_config_file
from twarccloud.harvester.collection_lock import force_unlock
from twarccloud.harvester.monitoring_thread import MonitoringThread
from twarccloud.harvester.harvest_info import HarvestInfo
from twarccloud.harvester.file_queueing_writer import FileQueueingWriter
from twarccloud.collection_config import CollectionConfig
from twarccloud.changeset import Changeset
from twarccloud.config_helpers import setup_logging, setup_honeybadger, load_ini_config, setup_aws_keys
from twarccloud import log, __version__


# pylint: disable=too-many-instance-attributes
class TweetHarvester:
    # pylint: disable=too-many-arguments
    def __init__(self, collection_id, collections_path, bucket=None, tweets_per_file=None, monitor=False,
                 shutdown=False):
        self.harvest_timestamp = datetime.utcnow()
        self.collection_id = collection_id
        self.collections_path = collections_path
        self.bucket = bucket
        self.tweets_per_file = tweets_per_file
        self.monitor = monitor

        # When running in AWS as a service:
        # 1. twarc_cloud calls /stop, which sets stop_event.
        # 2. Harvesting exits cleanly.
        # 2. twarc_cloud polls waiting for /is_stopped to return true.
        # 3. twarc_cloud stops service, which send SIGKILL.
        # 4. SIGKILL triggers shutdown event which causes the app to exit.

        self.file_queue = Queue()
        self.harvest_info = HarvestInfo(self.collection_id, self.harvest_timestamp)
        self.changeset = Changeset()
        self.changeset['harvest_timestamp'] = self.harvest_timestamp.isoformat()
        self.changeset['note'] = 'Changes based on harvester.'

        # This stops harvesting and cleans up.
        self.stop_event = Event()
        # This indicates that harvesting is done.
        self.stopped_event = Event()
        # This allows the app to exit.
        self.shutdown_event = Event()
        # If shutdown, then trigger the shutdown event. This will cause the app to exit after harvesting is completed.
        if shutdown:
            self.shutdown_event.set()

        # Setup shutdown signals
        # pylint: disable=unused-argument
        def signal_handler(signum, frame):
            self.stop_event.set()
            self.shutdown_event.set()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self._config = None

    def harvest(self):
        log.info('Starting harvester')
        # Sync
        if self.bucket:
            sync_collection_config(self.collections_path, self.collection_id, self.bucket)

        # Check if collection is locked
        assert_locked(self.lock_filepath())

        # Start the server
        ServerThread(self.stop_event, self.stopped_event, self.shutdown_event, self.harvest_info).start()

        # Start the monitor
        if self.monitor:
            MonitoringThread().start()

        # Load the collection config
        collection_config = self._load_collection_config()

        with S3FileMoverThread(self.file_queue, self.collections_path, self.bucket), CollectionLock(
                self.collections_path, self.collection_id, self.file_queue, collect_timestamp=self.harvest_timestamp):
            # Write the collection config file to harvester
            self._write_harvest_collection_config(collection_config)

            # Start collecting
            twarc_thread = TwarcThread(collection_config, self.collections_path, self.harvest_timestamp,
                                       self.file_queue, self.changeset, self.stop_event, self.harvest_info,
                                       self.tweets_per_file)
            twarc_thread.start()

            # Wait for collection to stop
            twarc_thread.join()
            if twarc_thread.exception:
                raise twarc_thread.exception

            # Save harvester info
            with FileQueueingWriter(get_harvest_info_file(self.collection_id, self.harvest_timestamp,
                                                          collections_path=self.collections_path),
                                    self.file_queue) as harvest_info_writer:
                harvest_info_writer.write_json(self.harvest_info.to_dict(), indent=2)
            if self.changeset.has_changes():
                # Sync again
                if self.bucket:
                    sync_collection_config_file(self.collections_path, self.collection_id,
                                                self.bucket)
                latest_collection_config = self._load_collection_config()
                if latest_collection_config.get('timestamp', 1) != collection_config.get('timestamp', 2):
                    # If it has changed, then delete any updates from changeset for users that no longer exist.
                    log.debug('Cleaning changeset')
                    self.changeset.clean_changeset(latest_collection_config)
                # Merge changes into latest config
                latest_collection_config.merge_changeset(self.changeset)
                # Write config
                with FileQueueingWriter(
                        get_collection_config_filepath(self.collection_id, collections_path=self.collections_path),
                        self.file_queue) as changeset_writer:
                    changeset_writer.write_json(latest_collection_config, indent=2)

                # Write changeset
                change_timestamp = dateutil.parser.parse(self.changeset['change_timestamp'])
                with FileQueueingWriter(
                        get_changeset_file(self.collection_id, change_timestamp,
                                           collections_path=self.collections_path),
                        self.file_queue) as changeset_writer:
                    changeset_writer.write_json(self.changeset, indent=2)

        log.info('Harvesting stopped')
        # All done
        self.stopped_event.set()

        log.debug('Waiting to shut down')
        while not self.shutdown_event.is_set():
            sleep(.5)
        log.info('Shut down')

    def _load_collection_config(self):
        with open(
                get_collection_config_filepath(self.collection_id,
                                               collections_path=self.collections_path)) as config_file:
            return CollectionConfig(json.load(config_file))

    def _write_harvest_collection_config(self, collection_config):
        harvest_collection_config_filepath = os.path.join(
            get_harvest_path(self.collection_id, self.harvest_timestamp, collections_path=self.collections_path),
            'collection.json')
        os.makedirs(os.path.dirname(harvest_collection_config_filepath), exist_ok=True)
        # Remove secrets
        clean_config = copy.deepcopy(collection_config)
        del clean_config['keys']['consumer_secret']
        del clean_config['keys']['access_token_secret']
        with FileQueueingWriter(harvest_collection_config_filepath, self.file_queue) as config_writer:
            config_writer.write_json(clean_config, indent=2)

    def lock_filepath(self):
        return get_lock_file(self.collection_id, collections_path=self.collections_path)

def add_local_subparser(subparsers):
    local_parser = subparsers.add_parser('local', help='Collect in local mode.')
    local_subparser = local_parser.add_subparsers(help='sub-command help', dest='subcommand')

    local_harvest_parser = local_subparser.add_parser('harvester', help='Harvest tweets')
    local_harvest_parser.add_argument('collection_id', help='Collection id')
    local_harvest_parser.add_argument('--collections-path', default='collections',
                                      help='Base path for collections. Default: collections.')
    local_harvest_parser.add_argument('--tweets-per-file', default='250000', type=int,
                                      help='Tweets per file. Default is 250,000.')
    local_harvest_parser.add_argument('--monitor', action='store_true', help='Log monitoring information.')

    local_unlock_parser = local_subparser.add_parser('unlock', help='Unlock a collection')
    local_unlock_parser.add_argument('collection_id', help='Collection id')
    local_unlock_parser.add_argument('--collections-path', default='collections',
                                     help='Base path for collections. Default: collections.')
    return local_parser

def add_aws_subparser(subparsers):
    aws_parser = subparsers.add_parser('aws', help='In AWS mode.')
    aws_subparser = aws_parser.add_subparsers(help='sub-command help', dest='subcommand')

    aws_harvest_parser = aws_subparser.add_parser('harvester', help='Harvest tweets')
    aws_harvest_parser.add_argument('bucket', help='S3 bucket')
    aws_harvest_parser.add_argument('collection_id', help='Collection id')
    aws_harvest_parser.add_argument('--temp', default='temp', help='Path for temporary files.')
    aws_harvest_parser.add_argument('--tweets-per-file', default='250000', type=int,
                                    help='Tweets per file. Default is 250,000.')
    aws_harvest_parser.add_argument('--monitor', action='store_true', help='Log monitoring information.')
    aws_harvest_parser.add_argument('--shutdown', action='store_true', help='Shutdown after completing harvester.')

    aws_unlock_parser = aws_subparser.add_parser('unlock', help='Unlock a collection')
    aws_unlock_parser.add_argument('bucket', help='S3 bucket')
    aws_unlock_parser.add_argument('collection_id', help='Collection id')
    aws_unlock_parser.add_argument('--temp', default='temp', help='Path for temporary files.')
    return aws_parser


def main():
    setup_honeybadger()

    parser = argparse.ArgumentParser(description='Wrap Twarc in a cloudy sort of way for collecting Twitter data.')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('-V', '--version', action='store_true', help='Show version and exit')
    subparsers = parser.add_subparsers(help='command help', dest='command')

    local_parser = add_local_subparser(subparsers)
    aws_parser = add_aws_subparser(subparsers)

    m_args = parser.parse_args()
    setup_logging(debug=m_args.debug)

    if m_args.version:
        print('Version {}'.format(__version__))
    elif m_args.command == 'aws':
        if os.path.exists('twarc_cloud.ini'):
            setup_aws_keys(load_ini_config('twarc_cloud.ini'))
        if m_args.subcommand == 'harvester':
            harvester = TweetHarvester(m_args.collection_id, m_args.temp, bucket=m_args.bucket,
                                       tweets_per_file=m_args.tweets_per_file, monitor=m_args.monitor,
                                       shutdown=m_args.shutdown)
            harvester.harvest()
        elif m_args.subcommand == 'unlock':
            force_unlock(m_args.temp, m_args.collection_id, bucket=m_args.bucket)
            print('Unlocked')
        else:
            aws_parser.print_help()
            exit(1)

    elif m_args.command == 'local':
        if m_args.subcommand == 'harvester':
            harvester = TweetHarvester(m_args.collection_id, m_args.collections_path,
                                       tweets_per_file=m_args.tweets_per_file, monitor=m_args.monitor, shutdown=True)
            harvester.harvest()
        elif m_args.subcommand == 'unlock':
            force_unlock(m_args.collections_path, m_args.collection_id)
            print('Unlocked')
        else:
            local_parser.print_help()
            exit(1)
    else:
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    main()
