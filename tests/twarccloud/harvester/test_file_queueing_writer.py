from tempfile import mkdtemp
import shutil
from queue import Queue
from twarccloud.harvester.file_queueing_writer import FileQueueingWriter
from twarccloud.harvester.file_mover_thread import AddFile
from tests import TestCase


class TestFileQueueingWriter(TestCase):
    def setUp(self):
        self.path = mkdtemp()
        self.file_queue = Queue()

    def tearDown(self):
        shutil.rmtree(self.path, ignore_errors=True)

    def test_write(self):
        filepath = '{}/test.txt'.format(self.path)
        with FileQueueingWriter(filepath, self.file_queue) as writer:
            writer.write('test')
        self.assertQueuedFile(filepath)
        self.assertEqual('test', open(filepath).read())

    def test_write_json(self):
        filepath = '{}/test.txt'.format(self.path)
        with FileQueueingWriter(filepath, self.file_queue) as writer:
            writer.write_json(['test'])
        self.assertQueuedFile(filepath)
        self.assertEqual('["test"]\n', open(filepath).read())

    def test_write_delete(self):
        filepath = '{}/test.txt'.format(self.path)
        with FileQueueingWriter(filepath, self.file_queue, delete=True) as writer:
            writer.write('test')
        self.assertQueuedFile(filepath, local_delete=True)
        self.assertEqual('test', open(filepath).read())

    # pylint: disable=invalid-name
    def assertQueuedFile(self, filepath, local_delete=False):
        queued_file = self.file_queue.get()
        self.file_queue.task_done()
        self.assertIsInstance(queued_file, AddFile)
        self.assertTrue(queued_file.delete == local_delete)
        self.assertEqual(filepath, queued_file.filepath)
