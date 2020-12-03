# --------------------------------------------------
# software develop for Raspberry Pi
# It use gpiozero. If not installed or another platform, use
# sgpiozero to simulate mechanism
#
# manage a button to activate/deactivate Wifi : long press to activate
# manage a button to manually open/close door or stop it
#     quickly 3 press to stop it
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

from elements.logger import Logger
import json
import argparse
from signal import pause
from datetime import datetime
import threading
import os
import os.path
import subprocess
from elements.advanced_elements import AdvancedButton
from elements.advanced_elements import MasterButton
from elements.advanced_elements import AdvancedLed
from elements.advanced_elements import AdvancedMotor
from elements.wifi_management import WifiManagement
from elements.automatic_door import AutomaticControl
from elements.email_sender import EmailSender
from elements.http_server import ApiHttpServer
from elements.http_server import CommandRequestHandler
from elements.watchdog import WatchDog

RASPBERRY = True
try:
    import gpiozero
except ModuleNotFoundError:
    from simulator.sgpiozero import GpioUi
    RASPBERRY = False


# action on Wifi error
#    problem wifi, bad interface...
# in this case, save current log in flash, and reboot
# if file already exists with same date and just hour, stop software, because
# repeating problem
def wifi_error():
    logger.error("wifi error")
    saved_file = "door_error.log." + datetime.utcnow().strftime("%Y-%m-%dT%H")
    if os.path.isfile(saved_file):
        logger.error("stop process to not loop, error already occurs !")
        os._exit(1)
    # save log before reboot
    current_log = logger.get_current_log()
    with open(saved_file, 'w') as file:
        file.writelines(current_log)
    # now, reboot server
    action = ["sudo", "/sbin/shutdown", "-r", "0"]
    subprocess.run(action, timeout=60)


def wifi_deactivated(state):
    logger.debug("wifi deactivated: " + str(state))
    if state == 3:
        wifi_error()
    elif state == 0:
        stop_http_server()
        if wifi_led:
            wifi_led.off()


def deactivate_wifi():
    if wifi_management:
        logger.debug("deactivate WIFI")
        wifi_management.stop_wifi(wifi_deactivated)


# get result of start wifi script
def wifi_activated(state):
    logger.debug("wifi activated: " + str(state))
    if state == 3:
        wifi_error()
    elif state == 2:
        if wifi_led:
            wifi_led.on()
        # send current log if exists and configured
        email.send()
        start_http_server()
        if wifi_management:
            # Wifi activated maximum of time : 600 seconds
            wifi_management.stop_wifi_after_timer(callback=wifi_deactivated, timeout=600)
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


def open_door():
    if motor:
        return motor.open_door()
    return False


def close_door():
    if motor:
        return motor.close_door()
    return False


# return True if motor was active and stopped
def stop_door():
    if motor:
        return motor.stop()
    return False


def other_action():
    logger.debug("other action")


def start_http_server():
    global http_server

    if not http_server:
        # activate Http server if Wifi stay activated
        http_server = ApiHttpServer(server_address, CommandRequestHandler, (open_door, close_door))


def stop_http_server():
    global http_server

    if http_server:
        http_server.stop_server()
        http_server = None


def read_config_file(file):
    with open(file, 'r') as f:
        line = f.read()
        return json.loads(line)


default_config_file = "chicken.json"
wifi_timeout = 20
configuration = None
server_address = ('', 54321)
http_server = None

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help=u'configuration file, default is chicken.json', required=False)
    parser.add_argument('-d', '--debug', action='store_true', help=u'activate debug log', required=False)
    parameters = parser.parse_args()

    try:
        if parameters.config:
            configuration = read_config_file(parameters.config)
        else:
            configuration = read_config_file(default_config_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        print("can't find configuration file, or bad content, try option -h !")
        exit(1)

    if parameters.debug:
        configuration['log_level'] = 'debug'

    # rotate log configuration
    logger = Logger(configuration)

    if RASPBERRY:
        logger.info("start door management on Raspberry")
    else:
        logger.info("start door management on Linux")

    try:
        # just read mandatory fields to use default value if absent
        configuration['longitude']
        configuration['latitude']
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
                logger.info("Wifi button activated")
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
            logger.info("wifi Led activated")
    except KeyError:
        pass

    # the button to manage the motor
    try:
        if configuration['motor_button_gpio']:
            motor_button = MasterButton(configuration['motor_button_gpio'], toggle_door, other_action,
                                        multiple_callback=stop_door)
            logger.info("motor button activated")
    except KeyError:
        pass

    # the motor
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

    # the close door sensor
    try:
        if configuration['door_closed_gpio'] and motor:
            motor.set_close_sensor(configuration['door_closed_gpio'])
            logger.info("close door sensor activated")
    except KeyError:
        pass

    # the open door sensor
    try:
        if configuration['door_opened_gpio'] and motor:
            motor.set_open_sensor(configuration['door_opened_gpio'])
            logger.info("open door sensor activated")
    except KeyError:
        pass

    # prepare email sender if configuration is done. It will be used each time wifi is activated
    # if there is log to send
    email = EmailSender(configuration, logger)

    control = AutomaticControl(configuration, motor)
    control.automatic_control()

    try:
        wifi_state = configuration['wifi_at_startup']
        if wifi_state:
            # activate Http server if Wifi stay activated
            http_server = ApiHttpServer(server_address, CommandRequestHandler, (open_door, close_door))
        else:
            deactivate_wifi()
    except KeyError:
        pass

    watchdog = WatchDog(30)

    try:
        if RASPBERRY:
            pause()
        else:
            app.show_ui()
    except (KeyboardInterrupt, SystemExit):
        watchdog.stop()
        for thread in threading.enumerate():
            logger.debug(thread.name)

        control.timer.cancel()
