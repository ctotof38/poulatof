import ephem
from datetime import datetime, timezone
import threading
import time
import logging

logger = logging.getLogger('automatic_door')


class AutomaticControl:
    # fake_time set time to next event instead of ephemeris value. in milliseconds
    def __init__(self, configuration, motor, fake_time=None):
        try:
            self.delta = configuration['security_time']
        except KeyError:
            self.delta = 1800
        self.longitude = configuration['longitude']
        self.latitude = configuration['latitude']
        self.motor = motor
        self.timer = None
        # to simulate ephemeris
        self.fake_time = fake_time
        self.fake_start = None
        self.fake_order = True
        if self.fake_time:
            self.fake_start = datetime.now()

    # first is set to False when call after automatic open/close door, to not open/close door a new time
    def automatic_control(self, first=True):
        observer = ephem.Observer()
        observer.lat, observer.lon = self.latitude, self.longitude
        observer.date = ephem.Date(datetime.now(timezone.utc))

        next_goodbye_sun = observer.next_setting(ephem.Sun()).datetime()
        security_time = next_goodbye_sun.timestamp() + self.delta
        next_goodbye_sun = datetime.fromtimestamp(security_time)

        next_hello_sun = observer.next_rising(ephem.Sun()).datetime()
        today = datetime.now(timezone.utc)

        if self.fake_time:
            ts = (today - datetime(1970, 1, 1)).total_seconds() + self.fake_time
            if self.fake_order:
                self.fake_order = False
                next_hello_sun = datetime.fromtimestamp(ts)
                next_goodbye_sun = datetime.fromtimestamp(ts + 1)
            else:
                self.fake_order = True
                next_goodbye_sun = datetime.fromtimestamp(ts)
                next_hello_sun = datetime.fromtimestamp(ts + 1)

        if next_hello_sun < next_goodbye_sun:
            if first:
                # in this case, door must be closed
                self.motor.close_door()
            logger.info("next open UTC: " + str(next_hello_sun))
            next_time = (next_hello_sun - today).total_seconds()
            self.timer = threading.Timer(next_time, self.open_door)
            self.timer.start()
        else:
            if first:
                # in this case, door must be opened
                self.motor.open_door()
            logger.info("next close UTC: " + str(next_goodbye_sun))
            next_time = (next_goodbye_sun - today).total_seconds()
            self.timer = threading.Timer(next_time, self.close_door)
            self.timer.start()

    def open_door(self):
        logger.debug("automatic open door")
        self.motor.open_door()
        # wait at least max_time + delta, if not, next automatic_control
        # should send command to motor if sensor is not reached
        time.sleep(self.motor.open_timeout + 10)
        self.automatic_control(first=False)

    def close_door(self):
        logger.debug("automatic close door")
        self.motor.close_door()
        time.sleep(self.motor.open_timeout + 10)
        self.automatic_control(first=False)

