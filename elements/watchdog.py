import threading
import time

DOG_FILE = "/tmp/watchdog_hen.txt"


class WatchDog:
    def __init__(self, delay=300):
        self.running = True
        self.delay = delay
        self.send()

    def send(self):
        utc_time = int(time.time())
        with open(DOG_FILE, 'w') as f:
            f.write(str(utc_time))

        if self.running:
            # save date each 5 minutes
            timer = threading.Timer(self.delay, self.send)
            timer.start()

    def stop(self):
        self.running = False