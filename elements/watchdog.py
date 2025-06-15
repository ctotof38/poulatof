import threading
import logging
import systemd.daemon
from .email_sender import EmailSender

logger = logging.getLogger('watch_dog')


RASPBERRY_TEMP = "/sys/class/thermal/thermal_zone0/temp"
WARNING_TEMPERATURE = 50
ALERT_TEMPERATURE = 70
ERROR_TEMPERATURE = 80


def get_cpu_temperature_sysfile(logger):
    try:
        with open(RASPBERRY_TEMP, "r") as f:
            temp_str = f.read().strip()
            temp_milli_celsius = int(temp_str)
            return temp_milli_celsius / 1000.0
    except FileNotFoundError:
        logger.error(f"file not found: {RASPBERRY_TEMP}")
        return None
    except Exception as e:
        logger.error(f"can't read temperature: {e}")
        return None

class WatchDog:
    def __init__(self, delay=600, email: EmailSender = None):
        self.running = True
        self.delay = delay
        self.email = email
        self.warning = False
        self.alert = False
        self.error = False
        logger.debug(f"start watchdog, delay: {self.delay} seconds")
        self.send()

    def send(self):
        """send regularly a signal to systemd
        """
        systemd.daemon.notify('WATCHDOG=1')
        self.__check_temperature()

        if self.running:
            # send signal each <delay> seconds
            timer = threading.Timer(self.delay, self.send)
            logger.debug(f"next watchdog in {self.delay} seconds")
            timer.start()

    def stop(self):
        self.running = False

    def __check_temperature(self):
        """check temperature and send email according to its level
        """
        temperature = get_cpu_temperature_sysfile(logger)
        logger.debug(f"temperature: {temperature}")
        if temperature > ERROR_TEMPERATURE:
            if not self.error and self.email is not None:
                self.email.send_message(f"temperature is two high: {temperature}", "ERROR temperature")
            self.error = True
        elif temperature > ALERT_TEMPERATURE:
            if not self.alert and self.email is not None:
                self.email.send_message(f"temperature: {temperature}", "alert temperature")
            self.alert = True
        elif temperature > WARNING_TEMPERATURE:
            if not self.warning and self.email is not None:
                self.email.send_message(f"temperature: {temperature}", "warning temperature")
            self.warning = True
            self.alert = False
        else:
            self.warning = False
            self.alert = False
            self.error = False
            
