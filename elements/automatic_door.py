import ephem
from datetime import datetime
import threading
import time
import logging

logger = logging.getLogger('automatic_door')


class AutomaticControl:
    def __init__(self, configuration, motor):
        try:
            self.delta = configuration['security_time']
        except KeyError:
            self.delta = 1800
        self.longitude = configuration['longitude']
        self.latitude = configuration['latitude']
        self.motor = motor
        self.timer = None

    def automatic_control(self):
        observer = ephem.Observer()
        observer.lat, observer.lon = self.latitude, self.longitude
        observer.date = ephem.Date(datetime.utcnow())

        # goodbye sun
        sunset = observer.next_setting(ephem.Sun()).datetime()
        security_time = sunset.timestamp() + self.delta

        close_hour = datetime.fromtimestamp(security_time)
        open_hour = observer.next_rising(ephem.Sun()).datetime()
        today = datetime.utcnow()

        if open_hour < close_hour:
            logger.debug("next open UTC: " + str(open_hour))
            next_time = (open_hour - today).total_seconds()
            self.timer = threading.Timer(next_time, self.open_door)
            self.timer.start()
        else:
            logger.debug("next close UTC: " + str(close_hour))
            next_time = (close_hour - today).total_seconds()
            self.timer = threading.Timer(next_time, self.close_door)
            self.timer.start()

    def open_door(self):
        logger.debug("automatic open door")
        self.motor.open_door()
        time.sleep(10)
        self.automatic_control()

    def close_door(self):
        logger.debug("automatic close door")
        self.motor.close_door()
        time.sleep(10)
        self.automatic_control()


