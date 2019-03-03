import json
import os
from .file_mover_thread import AddFile


# A File-like writer that adds files to a provided file queue.
class FileQueueingWriter:
    def __init__(self, filepath, file_queue, delete=False, mode='w'):
        self.file_queue = file_queue
        self.filepath = filepath
        self.delete = delete
        self.mode = mode
        self.file = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.file = open(self.filepath, self.mode)
        return self

    def __exit__(self, *args):
        self.file.flush()
        os.fsync(self.file.fileno())
        self.file.close()
        self.file_queue.put(AddFile(self.filepath, self.delete))

    def write(self, string):
        self.file.write(string)

    def write_json(self, json_obj, **kwargs):
        json.dump(json_obj, self.file, **kwargs)
        self.file.write('\n')
