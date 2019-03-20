import threading
from queue import Empty
from time import sleep
import os
from collections import namedtuple
from twarccloud.filepaths_helper import DEFAULT_COLLECTIONS_PATH
from twarccloud.aws import aws_client
from twarccloud import log


AddFile = namedtuple('AddFile', ['filepath', 'delete'])
DeleteFile = namedtuple('DeleteFile', ['filepath'])


# Thread that moves files to S3 that are placed on a provided queue.
class S3FileMoverThread(threading.Thread):
    def __init__(self, queue, collections_path, bucket):
        self.queue = queue
        self.collections_path = collections_path
        self.bucket = bucket
        self.stop_event = threading.Event()
        self.exception = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            log.debug('Starting file processor thread')
            while not self.stop_event.is_set() or not self.queue.empty():
                try:
                    src_file = self.queue.get_nowait()
                    if self.bucket:
                        self._move(src_file)
                    else:
                        log.debug('Skipping moving %s since local', src_file.filepath)
                    self.queue.task_done()
                except Empty:
                    sleep(.5)
            log.debug('Ending file processor thread')
        # pylint: disable=broad-except
        except Exception as exception:
            self.exception = exception

    def _move(self, src_file):
        dest_filepath = src_file.filepath.replace(self.collections_path, DEFAULT_COLLECTIONS_PATH)
        if isinstance(src_file, AddFile):
            log.debug('Copying %s to s3://%s/%s', src_file.filepath, self.bucket, dest_filepath)
            aws_client('s3').upload_file(src_file.filepath, self.bucket, dest_filepath)
            if src_file.delete:
                os.remove(src_file.filepath)
        else:
            log.debug('Deleting s3://%s/%s', self.bucket, dest_filepath)
            aws_client('s3').delete_object(Bucket=self.bucket, Key=dest_filepath)

    def stop(self):
        self.stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
        self.join()
        if self.exception:
            raise self.exception
