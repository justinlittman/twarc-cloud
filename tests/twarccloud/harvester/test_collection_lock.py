from tempfile import mkdtemp
import shutil
from datetime import datetime
from queue import Queue
import os
from twarccloud.harvester.collection_lock import CollectionLock, AddFile, DeleteFile, is_locked, assert_locked, \
    LockedException
from twarccloud.filepaths_helper import get_lock_file, get_last_harvest_file
from tests import TestCase


class TestCollectionLock(TestCase):
    def setUp(self):
        self.collections_path = mkdtemp()
        self.timestamp = datetime.utcnow()
        self.file_queue = Queue()
        self.collection_id = 'test_id'
        self.lock_file = get_lock_file(self.collection_id, collections_path=self.collections_path)
        self.last_harvest_file = get_last_harvest_file(self.collection_id, collections_path=self.collections_path)

    def tearDown(self):
        shutil.rmtree(self.collections_path, ignore_errors=True)

    def test_lock(self):
        with CollectionLock(self.collections_path, self.collection_id, self.file_queue,
                            harvest_timestamp=self.timestamp):
            self.assertTrue(os.path.exists(self.lock_file))
            self.assertQueuedFile(self.lock_file)

        self.assertTrue(os.path.exists(self.last_harvest_file))
        self.assertQueuedFile(self.last_harvest_file)
        self.assertFalse(os.path.exists(get_lock_file(self.collection_id, collections_path=self.collections_path)))
        self.assertQueuedFile(self.lock_file, is_add=False)

    def test_is_locked(self):
        self.assertFalse(is_locked(self.lock_file))
        with CollectionLock(self.collections_path, self.collection_id, self.file_queue,
                            harvest_timestamp=self.timestamp):
            self.assertTrue(is_locked(self.lock_file))
            with self.assertRaises(LockedException):
                assert_locked(self.lock_file)
        self.assertFalse(is_locked(self.lock_file))
        assert_locked(self.lock_file)

    # pylint: disable=invalid-name
    def assertQueuedFile(self, filepath, is_add=True):
        queued_file = self.file_queue.get()
        self.file_queue.task_done()
        self.assertIsInstance(queued_file, AddFile if is_add else DeleteFile)
        self.assertEqual(filepath, queued_file.filepath)
