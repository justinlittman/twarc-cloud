import threading
from datetime import datetime


# Summary information about a harvester.
class HarvestInfo:
    def __init__(self, collection_id, harvest_timestamp):
        self.collection_id = collection_id
        self.tweets = AtomicInteger()
        self.files = AtomicInteger()
        self.file_bytes = AtomicInteger()
        self.harvest_timestamp = harvest_timestamp
        self.harvest_end_timestamp = None

    def end(self):
        self.harvest_end_timestamp = datetime.utcnow()

    def to_dict(self):
        harvest_info = {
            'collection_id': self.collection_id,
            'harvest_timestamp': self.harvest_timestamp.isoformat(),
            'tweets': self.tweets.value,
            'files': self.files.value,
            'file_bytes': self.file_bytes.value
        }
        if self.harvest_end_timestamp:
            harvest_info['harvest_end_timestamp'] = self.harvest_end_timestamp.isoformat()

        return harvest_info


# Thread-safe incrementer.
# From https://stackoverflow.com/questions/23547604/python-counter-atomic-increment
class AtomicInteger:
    def __init__(self, value=0):
        self._value = value
        self._lock = threading.Lock()

    def incr(self, amount=1):
        with self._lock:
            self._value += amount
            return self._value

    @property
    def value(self):
        with self._lock:
            return self._value
