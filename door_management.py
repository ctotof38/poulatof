# --------------------------------------------------
# software develop for Raspberry Pi
# It use gpiozero. If not installed or another platform, use
# sgpiozero to simulate mechanism
#
# manage a button to activate/deactivate Wifi : long press to activate
# manage a button to manually open/close door or stop it
#     long press to stop it
#     short press toggle
# manage LED
#     blink to indicate look for a Wifi network
#     blink quickly because no Wifi found
#     off if not connected
#     on if connected
# manage a motor forward and backward : forward to open door
# manage two sensors (like button) to stop door when opened or closed
#
# read a configuration file which contains the GPIO to use, the position (lon, lat)
# the script to used to stop/start Wifi, a security time to close door after sunset + this time
# --------------------------------------------------
import sys

if not sys.version_info.major == 3:
    print("Python 3.x or higher is required.")
    sys.exit(1)

import logging
import json
import argparse
from signal import pause
from elements.advanced_elements import AdvancedButton
from elements.advanced_elements import AdvancedLed
from elements.advanced_elements import AdvancedMotor
from elements.wifi_management import WifiManagement
from elements.automatic_door import AutomaticControl
import threading

RASPBERRY = True
try:
    import gpiozero
except ModuleNotFoundError:
    from simulator.sgpiozero import GpioUi
    RASPBERRY = False


def wifi_deactivated(state):
    logger.debug("wifi deactivated: " + str(state))
    if state == 0:
        if wifi_led:
            wifi_led.off()


def deactivate_wifi():
    if wifi_management:
        logger.debug("deactivate WIFI")
        wifi_management.stop_wifi(wifi_deactivated)


# get result of start wifi script
def wifi_activated(state):
    logger.debug("wifi activated: " + str(state))
    if state == 2:
        if wifi_led:
            wifi_led.on()
    else:
        if wifi_led:
            wifi_led.off()
            wifi_led.blink(0.1, 5, deactivate_wifi)


# blink led if wifi is looking for network
def activate_wifi():
    if wifi_management:
        logger.debug("activate WIFI")
        if wifi_management.start_wifi(wifi_activated):
            if wifi_led:
                wifi_led.blink(0.3)


# return True if motor is activate
# False if no motor or can't activate it
def toggle_door():
    if motor:
        if not motor.reverse_door():
            if not motor.open_door():
                return motor.close_door()
        return True
    return False


# return True if motor was active and stopped
def stop_door():
    if motor:
        return motor.stop()
    return False


def read_config_file(file):
    with open(file, 'r') as f:
        line = f.read()
        try:
            return json.loads(line)
        except ValueError:
            logging.error(line, sys.exc_info())

    return None


# read log_level from configuration file. Default is WARN
def set_logging_level(config):
    try:
        conf = config['log_level']
        if 'debug' in conf:
            logging.basicConfig(level=logging.DEBUG,
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        elif 'info' in conf:
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        elif 'warning' in conf:
            logging.basicConfig(level=logging.WARNING,
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        elif 'error' in conf:
            logging.basicConfig(level=logging.ERROR,
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    except (KeyError, TypeError):
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


default_config_file = "chicken.json"
wifi_timeout = 20
configuration = None

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help=u'configuration file, default is chicken.json')
    parameters = parser.parse_args()

    try:
        if parameters.config:
            configuration = read_config_file(parameters.config)
        else:
            configuration = read_config_file(default_config_file)
    except FileNotFoundError:
        print("can't find configuration file, try option -h !")
        exit(1)

    set_logging_level(configuration)
    logger = logging.getLogger('main')

    logger.debug("start door management on Raspberry: " + str(RASPBERRY))

    try:
        # just read mandatory fields to generate error if they are forgotten
        no_used = configuration['longitude']
        no_used = configuration['latitude']
    except KeyError:
        logger.warning("Be careful, use default position of Eiffel tower")
        configuration['longitude'] = "2.294270"
        configuration['latitude'] = "48.858823"

    if not RASPBERRY:
        app = GpioUi()

    wifi_button = None
    wifi_led = None
    motor_button = None
    motor = None
    door_closed = None
    door_opened = None
    wifi_management = None
    try:
        if configuration['wifi_button_gpio']:
            wifi_button = AdvancedButton(configuration['wifi_button_gpio'], deactivate_wifi, activate_wifi)
            try:
                if configuration['wifi_script'] and configuration['wifi_interface']:
                    try:
                        timeout = configuration['wifi_timeout']
                    except KeyError:
                        timeout = 20
                    wifi_management = WifiManagement(configuration['wifi_script'], configuration['wifi_interface'],
                                                     timeout_wifi_connected=timeout)
            except KeyError:
                logger.error("if Wifi button, need wifi script and interface")
                exit(1)
            except FileNotFoundError:
                logger.error("if Wifi button, wifi script need to be executable")
                exit(1)

    except KeyError:
        pass

    try:
        if configuration['wifi_led_gpio']:
            wifi_led = AdvancedLed(configuration['wifi_led_gpio'])
    except KeyError:
        pass

    try:
        if configuration['motor_button_gpio']:
            motor_button = AdvancedButton(configuration['motor_button_gpio'], toggle_door, stop_door)
    except KeyError:
        pass

    try:
        try:
            timeout = configuration['motor_timeout']
        except KeyError:
            timeout = 20

        if configuration['motor_forward_gpio'] and configuration['motor_backward_gpio']:
            motor = AdvancedMotor(forward=configuration['motor_forward_gpio'],
                                  backward=configuration['motor_backward_gpio'], max_time=timeout)
    except KeyError:
        logger.error("Need at least motor GPIO")
        exit(1)

    try:
        if configuration['door_closed_gpio'] and motor:
            motor.set_close_sensor(configuration['door_closed_gpio'])
    except KeyError:
        pass

    try:
        if configuration['door_opened_gpio'] and motor:
            motor.set_open_sensor(configuration['door_opened_gpio'])
    except KeyError:
        pass

    control = AutomaticControl(configuration, motor)
    control.automatic_control()

    try:
        wifi_state = configuration['wifi_at_startup']
        if not wifi_state:
            deactivate_wifi()
    except KeyError:
        pass

    try:
        if RASPBERRY:
            pause()
        else:
            app.show_ui()
    except (KeyboardInterrupt, SystemExit):
        for thread in threading.enumerate():
            logger.debug(thread.name)

        control.timer.cancel()
