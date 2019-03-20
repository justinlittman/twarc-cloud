from tempfile import mkdtemp
import shutil
import json
import os
import socket
from contextlib import closing
from unittest.mock import patch, MagicMock
from threading import Timer
import requests
from tweet_harvester import TweetHarvester
from twarccloud.harvester.twarc_thread import TwarcThread
from twarccloud.filepaths_helper import get_collection_config_filepath, get_harvest_file, get_changesets_path
from tests import TestCase, timeline_config


class TestTweetHarvester(TestCase):
    def setUp(self):
        self.collection_id = 'test_id'
        self.collections_path = mkdtemp()
        self.collection_config_filepath = get_collection_config_filepath(self.collection_id,
                                                                         collections_path=self.collections_path)
        self.write_collection_config()

    def tearDown(self):
        shutil.rmtree(self.collections_path, ignore_errors=True)

    @patch('tweet_harvester.TwarcThread')
    def test_harvest(self, mock_twarc_thread_class):
        mock_twarc_thread = MagicMock(TwarcThread, exception=None)
        mock_twarc_thread_class.return_value = mock_twarc_thread

        harvester = TweetHarvester(self.collection_id, self.collections_path, shutdown=True, port=self.find_free_port())
        # Make a change to changeset
        harvester.changeset.update_user('screen_name', 'real_justin_littman', '481186914')
        harvester.harvest()

        # Test collection config written to harvest
        harvest_collection_config_filepath = get_harvest_file(self.collection_id, harvester.harvest_timestamp,
                                                              'collection.json', collections_path=self.collections_path)
        self.assertTrue(os.path.exists(harvest_collection_config_filepath))
        harvest_collection_config = self.load_collection_config(harvest_collection_config_filepath)
        self.assertFalse('consumer_secret' in harvest_collection_config['keys'])
        self.assertFalse('access_token_secret' in harvest_collection_config['keys'])

        # Test changeset
        collection_config = self.load_collection_config(self.collection_config_filepath)
        self.assertEqual('real_justin_littman', collection_config['users']['481186914']['screen_name'])
        self.assertEqual(1, len(
            os.listdir(get_changesets_path(self.collection_id, collections_path=self.collections_path))))

        # Test events
        self.assertTrue(harvester.stopped_event.is_set())
        self.assertTrue(harvester.shutdown_event.is_set())

    @patch('tweet_harvester.TwarcThread')
    def test_harvest_exception(self, mock_twarc_thread_class):
        mock_twarc_thread = MagicMock(TwarcThread, exception=Exception('Darn'))
        mock_twarc_thread_class.return_value = mock_twarc_thread

        harvester = TweetHarvester(self.collection_id, self.collections_path, shutdown=True, port=self.find_free_port())
        with self.assertRaises(Exception):
            harvester.harvest()

    @patch('tweet_harvester.TwarcThread')
    def test_harvest_without_shutdown(self, mock_twarc_thread_class):
        mock_twarc_thread = MagicMock(TwarcThread, exception=None)
        mock_twarc_thread_class.return_value = mock_twarc_thread

        harvester = TweetHarvester(self.collection_id, self.collections_path, shutdown=False,
                                   port=self.find_free_port())

        def test_shutdown_timer():
            self.assertFalse(harvester.shutdown_event.is_set())

        Timer(.5, test_shutdown_timer).start()

        def shutdown_timer():
            requests.get('http://localhost:{}/shutdown'.format(harvester.port))

        Timer(1, shutdown_timer).start()
        harvester.harvest()

        # Test events
        self.assertTrue(harvester.stopped_event.is_set())
        self.assertTrue(harvester.shutdown_event.is_set())

    def write_collection_config(self):
        os.makedirs(os.path.dirname(self.collection_config_filepath))
        with open(self.collection_config_filepath, 'w') as file:
            json.dump(timeline_config(), file)

    @staticmethod
    def load_collection_config(filepath):
        with open(filepath) as file:
            return json.load(file)

    @staticmethod
    def find_free_port():
        # pylint: disable=no-member
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind(('', 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return sock.getsockname()[1]
