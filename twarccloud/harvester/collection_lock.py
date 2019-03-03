import os
import shutil
from queue import Queue
from twarccloud.harvester.file_mover_thread import S3FileMoverThread, DeleteFile, AddFile
from twarccloud.aws.aws_helper import sync_collection_config
from twarccloud.harvester.file_queueing_writer import FileQueueingWriter
from twarccloud.filepaths_helper import get_lock_file, get_last_harvest_file
from twarccloud import log


# Provides locking for a collection by placing and removing lock.json in the root of the collection.
class CollectionLock:
    def __init__(self, collections_path, collection_id, file_queue, collect_timestamp=None):
        self.lock_filepath = get_lock_file(collection_id, collections_path=collections_path)
        self.last_harvest_filepath = get_last_harvest_file(collection_id, collections_path=collections_path)
        self.collect_timestamp = collect_timestamp
        self.file_queue = file_queue

    # Lock the collection.
    def lock(self):
        log.debug('Locking')
        lock = {
            'harvest_id': self.collect_timestamp.isoformat()
        }
        with FileQueueingWriter(self.lock_filepath, self.file_queue) as lock_writer:
            lock_writer.write_json(lock, indent=2)

    # Unlock the collection.
    # Unless forced, moves lock.json to last_harvest.json.
    def unlock(self, force=False):
        if not os.path.exists(self.lock_filepath):
            log.warning('Not locked')
            return

        log.info('Unlocking')
        if force:
            os.remove(self.lock_filepath)
        else:
            shutil.move(self.lock_filepath, self.last_harvest_filepath)
            self.file_queue.put(AddFile(self.last_harvest_filepath, False))
        self.file_queue.put(DeleteFile(self.lock_filepath))

    def __enter__(self):
        self.lock()
        return self

    def __exit__(self, *args):
        self.unlock()


class LockedException(Exception):
    pass


# Returns True if lock file exists at the provided filepath.
def is_locked(lock_filepath):
    return os.path.isfile(lock_filepath)


# Raises a LockedException if lock file exists at the provided filepath.
def assert_locked(lock_filepath):
    if is_locked(lock_filepath):
        raise LockedException


# Forces the unlocking of a collection.
# pylint: disable=too-many-function-args
def force_unlock(local_collections_path, collection_id, bucket=None):
    if bucket:
        sync_collection_config(local_collections_path, collection_id, bucket)
    file_queue = Queue()
    with S3FileMoverThread(file_queue, local_collections_path, bucket):
        CollectionLock(local_collections_path, collection_id, file_queue).unlock(force=True)
