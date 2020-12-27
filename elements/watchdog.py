import threading
import time
import logging

logger = logging.getLogger('watch_dog')

DOG_FILE = "/tmp/watchdog_hen.txt"


class WatchDog:
    def __init__(self, delay=300):
        self.running = True
        self.delay = delay
        logger.debug("start watchdog: " + str(self.delay))
        self.send()

    def send(self):
        utc_time = int(time.time())
        with open(DOG_FILE, 'w') as f:
            logger.debug("update time")
            f.write(str(utc_time))

        if self.running:
            # save date each 5 minutes
            timer = threading.Timer(self.delay, self.send)
            logger.debug("next watchdog: " + str(self.delay))
            timer.start()

    def stop(self):
        self.running = False