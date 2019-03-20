import json
from datetime import datetime
import gzip
import os
from time import sleep
from threading import Timer, Thread, Lock, Event
import hashlib
from twarccloud.filepaths_helper import get_harvest_path, get_harvest_manifest_filepath
from twarccloud.harvester.file_queueing_writer import FileQueueingWriter, AddFile
from twarccloud import log


# A thread for writing tweets to a gzip-compressed, newline-delimited JSON file.
# Files will be added to a provided file queue and rolled over based on a provided number of tweets per file
# or seconds per file.
# pylint: disable=too-many-instance-attributes
class TweetWriterThread(Thread):
    # pylint: disable=too-many-arguments
    def __init__(self, collections_path, collection_id, harvest_timestamp, file_queue, harvest_info,
                 tweets_per_file=None, secs_per_file=30 * 60):
        self.tweets_per_file = tweets_per_file or 250000
        self.collections_path = collections_path
        self.collection_id = collection_id
        self.harvest_timestamp = harvest_timestamp
        self.file_queue = file_queue
        self.harvest_info = harvest_info
        self.secs_per_file = float(secs_per_file)
        self.file = None
        self.filepath = None
        self.timer = None
        self.stop_event = None
        self.tweet_count = 0
        self.file_lock = Lock()
        Thread.__init__(self)

    def run(self):
        while not self.stop_event.is_set():
            sleep(.5)

    def __enter__(self):
        self._new_file()
        self.stop_event = Event()
        self.start()
        return self

    def __exit__(self, *args):
        self._close_file()
        self.stop_event.set()
        self.join()

    def write(self, tweet):
        if self.tweet_count == self.tweets_per_file:
            log.debug('Rolling over because tweet count is %s', self.tweet_count)
            self._new_file()
        with self.file_lock:
            self.file.write('{}\n'.format(json.dumps(tweet)).encode('utf-8'))
        self.tweet_count += 1
        self.harvest_info.tweets.incr()

    def _new_file(self):
        with self.file_lock:
            self._close_file()
            self.filepath = self._generate_filepath()
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            log.debug('Starting to write to %s', self.filepath)
            self.file = gzip.open(self.filepath, 'wb')
            self.tweet_count = 0
            # Start a timer
            self.timer = Timer(self.secs_per_file, self._new_file)
            self.timer.start()

    def _close_file(self):
        # Stop the timer
        if self.timer:
            self.timer.cancel()
        if self.file:
            log.debug('Closing %s', self.filepath)
            self.file.close()
            self.harvest_info.files.incr()
            self.harvest_info.file_bytes.incr(os.path.getsize(self.filepath))
            self._add_to_manifest()
            log.debug('Adding %s to file queue', self.filepath)
            self.file_queue.put(AddFile(self.filepath, True))

    def _generate_filepath(self):
        return "{}/tweets-{}.jsonl.gz".format(
            get_harvest_path(self.collection_id, self.harvest_timestamp, collections_path=self.collections_path),
            datetime.utcnow().strftime('%Y%m%d%H%M%S'))

    def _add_to_manifest(self):
        log.debug('Adding %s to manifest', self.filepath)
        with FileQueueingWriter(get_harvest_manifest_filepath(self.collection_id, self.harvest_timestamp,
                                                              collections_path=self.collections_path),
                                self.file_queue, mode='a') as writer:
            writer.write('{}  {}\n'.format(self._sha1(), os.path.basename(self.filepath)))

    def _sha1(self):
        with open(self.filepath, 'rb') as file:
            return hashlib.sha1(file.read()).hexdigest()
