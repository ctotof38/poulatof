import threading
import logging
import systemd.daemon
from .email_sender import EmailSender

logger = logging.getLogger('watch_dog')


RASPBERRY_TEMP = "/sys/class/thermal/thermal_zone0/temp"
WARNING_TEMPERATURE = 52
ALERT_TEMPERATURE = 70
CRITICAL_TEMPERATURE = 80


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


class TemperatureMonitor:
    def __init__(self, critical: float, alert: float, warning: float, delta: float=2):
        self.threshold_critical = critical
        self.threshold_alert = alert
        self.threshold_warning = warning
        self.delta = delta
        self.last_temperature = 0
        
    def check_temperature(self, current_temp):
        if current_temp >= self.threshold_critical:
            if current_temp >= (self.last_temperature + self.delta):
                self.last_temperature = current_temp
                result = {"message": f"Température critique atteinte: {current_temp}°C", "subject": "ERROR temperature"}
                return result
            return None
        elif current_temp >= self.threshold_alert:
            if current_temp >= (self.last_temperature + self.delta) or self.last_temperature >= self.threshold_critical:
                self.last_temperature = current_temp
                result = {"message": f"Température élevée: {current_temp}°C", "subject": "ALERT temperature"}
                return result
            return None
        elif current_temp >= self.threshold_warning:
            if current_temp >= (self.last_temperature + self.delta) or self.last_temperature >= self.threshold_alert:
                self.last_temperature = current_temp
                result = {"message": f"Température chaude: {current_temp}°C", "subject": "WARNING temperature"}
                return result
            return None
        # TODO if temp = 51.99, then warning appears only after 53.99 and not 52
        self.last_temperature = current_temp
        return None


class WatchDog:
    def __init__(self, delay=600, email: EmailSender = None):
        self.running = True
        self.delay = delay
        self.email = email
        self.monitor = TemperatureMonitor(CRITICAL_TEMPERATURE, ALERT_TEMPERATURE, WARNING_TEMPERATURE)
        logger.debug(f"start watchdog, delay: {self.delay} seconds")
        self.send()

    def send(self):
        """send regularly a signal to systemd
        """
        systemd.daemon.notify('WATCHDOG=1')
        try:
            self.__check_temperature()
        except Exception as e:
            logger.error("Error to check temperature: ", e)

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
        message = self.monitor.check_temperature(temperature)
        if message:
            self.email.send_message(f"{message['message']}", f"{message['subject']}")
        logger.debug(f"temperature: {temperature}")
