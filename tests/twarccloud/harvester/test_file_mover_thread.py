from unittest.mock import patch, MagicMock
from tempfile import mkdtemp
from queue import Queue
import os
from twarccloud.filepaths_helper import get_collection_file
from twarccloud.harvester.file_mover_thread import S3FileMoverThread, AddFile, DeleteFile
from tests import TestCase


class TestS3FileMoverThread(TestCase):
    def setUp(self):
        self.collections_path = mkdtemp()
        self.file_queue = Queue()
        self.collection_id = 'test_id'
        self.filepath = get_collection_file(self.collection_id, 'test.txt', collections_path=self.collections_path)
        self.bucket = 'test_bucket'

    def test_no_bucket(self):
        with S3FileMoverThread(self.file_queue, self.collections_path, None):
            os.makedirs(os.path.dirname(self.filepath))
            with open(self.filepath, 'w') as file:
                file.write('test')
            self.file_queue.put(AddFile(self.filepath, True))
        self.assertTrue(self.file_queue.empty())
        self.assertTrue(os.path.exists(self.filepath))

    @patch('twarccloud.harvester.file_mover_thread.aws_client')
    def test_move(self, mock_aws_client_factory):
        mock_aws_client = MagicMock()
        mock_aws_client_factory.return_value = mock_aws_client
        with S3FileMoverThread(self.file_queue, self.collections_path, self.bucket):
            os.makedirs(os.path.dirname(self.filepath))
            with open(self.filepath, 'w') as file:
                file.write('test')
            self.file_queue.put(AddFile(self.filepath, True))
        self.assertTrue(self.file_queue.empty())
        # File was deleted.
        self.assertFalse(os.path.exists(self.filepath))
        mock_aws_client.upload_file.assert_called_once_with(self.filepath, self.bucket,
                                                            get_collection_file(self.collection_id, 'test.txt'))

    @patch('twarccloud.harvester.file_mover_thread.aws_client')
    def test_move_without_delete(self, mock_aws_client_factory):
        mock_aws_client = MagicMock()
        mock_aws_client_factory.return_value = mock_aws_client
        with S3FileMoverThread(self.file_queue, self.collections_path, self.bucket):
            os.makedirs(os.path.dirname(self.filepath))
            with open(self.filepath, 'w') as file:
                file.write('test')
            self.file_queue.put(AddFile(self.filepath, False))
        self.assertTrue(self.file_queue.empty())
        # File was not deleted.
        self.assertTrue(os.path.exists(self.filepath))
        mock_aws_client.upload_file.assert_called_once_with(self.filepath, self.bucket,
                                                            get_collection_file(self.collection_id, 'test.txt'))

    @patch('twarccloud.harvester.file_mover_thread.aws_client')
    def test_delete(self, mock_aws_client_factory):
        mock_aws_client = MagicMock()
        mock_aws_client_factory.return_value = mock_aws_client
        with S3FileMoverThread(self.file_queue, self.collections_path, self.bucket):
            self.file_queue.put(DeleteFile(self.filepath))
        self.assertTrue(self.file_queue.empty())
        mock_aws_client.delete_object.assert_called_once_with(Bucket=self.bucket,
                                                              Key=get_collection_file(self.collection_id, 'test.txt'))
