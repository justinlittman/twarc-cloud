from threading import Thread
from time import sleep
import psutil
from twarccloud import log


# Thread that logs info on CPU, memory, swap, and disk usage on specified intervals.
class MonitoringThread(Thread):
    def __init__(self, interval_secs=30):
        self.interval_secs = interval_secs
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        while True:
            log.info('CPU percent: %s. Virtual memory: %s. Swap: %s. Disk usage: %s',
                     psutil.cpu_percent(),
                     psutil.virtual_memory(),
                     psutil.swap_memory(),
                     psutil.disk_usage('.'))
            sleep(self.interval_secs)
