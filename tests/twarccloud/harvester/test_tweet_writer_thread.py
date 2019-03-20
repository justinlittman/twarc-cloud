from tempfile import mkdtemp
import shutil
from datetime import datetime
from queue import Queue
import glob
import gzip
import json
import os
from time import sleep
from twarccloud.harvester.tweet_writer_thread import TweetWriterThread
from twarccloud.harvester.harvest_info import HarvestInfo
from twarccloud.filepaths_helper import get_harvest_path, get_harvest_manifest_filepath
from tests import TestCase


class TestTweetWriterThread(TestCase):
    def setUp(self):
        self.collections_path = mkdtemp()
        self.collection_id = 'test_id'
        self.harvest_timestamp = datetime.utcnow()
        self.file_queue = Queue()
        self.harvest_info = HarvestInfo(self.collection_id, self.harvest_timestamp)
        self.harvest_path = get_harvest_path(self.collection_id, self.harvest_timestamp,
                                             collections_path=self.collections_path)

    def tearDown(self):
        shutil.rmtree(self.collections_path, ignore_errors=True)

    def test_write(self):
        with TweetWriterThread(self.collections_path, self.collection_id, self.harvest_timestamp, self.file_queue,
                               self.harvest_info) as writer:
            writer.write(self.generate_tweet(1))
            writer.write(self.generate_tweet(2))
        tweet_files = glob.glob('{}/*.jsonl.gz'.format(self.harvest_path))
        self.assertEqual(1, len(tweet_files))
        # Wrote to file.
        self.assertTweetsInFile(tweet_files[0], 1, 2)
        self.assertQueuedFiles(tweet_files)
        # Added to manifest.
        self.assertManifestFile(tweet_files)
        # Updated harvest info.
        self.assertEqual(2, self.harvest_info.tweets.value)
        self.assertEqual(1, self.harvest_info.files.value)
        self.assertTrue(self.harvest_info.file_bytes.value)

    def test_rollover_by_tweet_count(self):
        with TweetWriterThread(self.collections_path, self.collection_id, self.harvest_timestamp, self.file_queue,
                               self.harvest_info, tweets_per_file=2) as writer:
            writer.write(self.generate_tweet(1))
            writer.write(self.generate_tweet(2))
            # Sleep so that file has new timestamp
            sleep(1)
            writer.write(self.generate_tweet(3))
            writer.write(self.generate_tweet(4))
        tweet_files = glob.glob('{}/*.jsonl.gz'.format(self.harvest_path))
        self.assertEqual(2, len(tweet_files))
        self.assertQueuedFiles(tweet_files)
        self.assertManifestFile(tweet_files)
        self.assertEqual(4, self.harvest_info.tweets.value)
        self.assertEqual(2, self.harvest_info.files.value)
        self.assertTrue(self.harvest_info.file_bytes.value)

    def test_rollover_by_time(self):
        with TweetWriterThread(self.collections_path, self.collection_id, self.harvest_timestamp, self.file_queue,
                               self.harvest_info, secs_per_file=1) as writer:
            writer.write(self.generate_tweet(1))
            writer.write(self.generate_tweet(2))
            # Sleep so that rollover
            sleep(1.25)
            writer.write(self.generate_tweet(3))
            writer.write(self.generate_tweet(4))
        tweet_files = glob.glob('{}/*.jsonl.gz'.format(self.harvest_path))
        self.assertEqual(2, len(tweet_files))
        self.assertQueuedFiles(tweet_files)
        self.assertManifestFile(tweet_files)
        self.assertEqual(4, self.harvest_info.tweets.value)
        self.assertEqual(2, self.harvest_info.files.value)
        self.assertTrue(self.harvest_info.file_bytes.value)

    @staticmethod
    def generate_tweet(tweet_id):
        return {
            'tweet_id': tweet_id
        }

    # pylint: disable=invalid-name
    def assertTweetsInFile(self, filepath, start_tweet_id, stop_tweet_id):
        with gzip.open(filepath) as tweet_file:
            for tweet_id in range(start_tweet_id, stop_tweet_id + 1):
                line = tweet_file.readline()
                self.assertDictEqual(self.generate_tweet(tweet_id), json.loads(line))

    # pylint: disable=invalid-name
    def assertQueuedFiles(self, tweet_files):
        queued_files = self.get_queued_files()
        for tweet_file in tweet_files:
            self.assertTrue(tweet_file in queued_files)

    # pylint: disable=invalid-name
    def assertManifestFile(self, tweet_files):
        manifest_files = self.get_manifest_files()
        tweet_filenames = set()
        for tweet_file in tweet_files:
            tweet_filenames.add(os.path.basename(tweet_file))
        self.assertSetEqual(manifest_files, tweet_filenames)

    def get_queued_files(self):
        files = set()
        while not self.file_queue.empty():
            queued_file = self.file_queue.get()
            files.add(queued_file.filepath)
            self.file_queue.task_done()
        return files

    def get_manifest_files(self):
        files = set()
        with open(get_harvest_manifest_filepath(self.collection_id, self.harvest_timestamp,
                                                collections_path=self.collections_path)) as file:
            for line in file:
                files.add(line.split()[1])
        return files
