from datetime import datetime
from twarccloud.harvester.harvest_info import HarvestInfo, AtomicInteger
from tests import TestCase


class TestHarvestInfo(TestCase):
    def test_to_dict(self):
        collection_id = 'test'
        harvest_timestamp = datetime.utcnow()
        harvest_info = HarvestInfo(collection_id, harvest_timestamp)
        harvest_info.tweets.incr(amount=5)
        harvest_info.files.incr()
        harvest_info.file_bytes.incr(amount=2048)
        harvest_info.end()

        harvest_dict = harvest_info.to_dict()
        self.assertEqual('test', harvest_dict['collection_id'])
        self.assertEqual(5, harvest_dict['tweets'])
        self.assertEqual(1, harvest_dict['files'])
        self.assertEqual(2048, harvest_dict['file_bytes'])
        self.assertTrue('harvest_timestamp' in harvest_dict)
        self.assertTrue('harvest_end_timestamp' in harvest_dict)


class TestAtomicInteger(TestCase):
    def test_incr(self):
        atomic_int = AtomicInteger(value=10)
        self.assertEqual(10, atomic_int.value)

        atomic_int.incr()
        self.assertEqual(11, atomic_int.value)

        atomic_int.incr(amount=5)
        self.assertEqual(16, atomic_int.value)
