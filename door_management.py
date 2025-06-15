#!/usr/bin/env python

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


# return True if motor is activate
# False if no motor or can't activate it
def toggle_door():
    if motor:
        # reverse door only if motor is running
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


def force_open_door():
    if motor:
        return motor.open_door(True)
    return False


def force_close_door():
    if motor:
        return motor.close_door(True)
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
        http_server = ApiHttpServer(server_address, CommandRequestHandler, (open_door, close_door, force_open_door(),
                                                                            force_close_door()))


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

    try:
        server_address = ('', configuration['http_port'])
    except KeyError:
        server_address = ('', 54321)

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

    # the button to manage the motor
    try:
        if configuration['motor_button_gpio']:
            motor_button = AdvancedButton(configuration['motor_button_gpio'], toggle_door, stop_door)
            logger.info("motor button activated")
    except KeyError:
        pass

    # the motor
    try:
        open_timeout = configuration['open_timeout']
    except KeyError:
        open_timeout = 20
    try:
        close_timeout = configuration['close_timeout']
    except KeyError:
        close_timeout = 20
    try:
        motor = AdvancedMotor(forward=configuration['motor_forward_gpio'],
                              backward=configuration['motor_backward_gpio'], 
                              open_timeout=open_timeout,
                              close_timeout=close_timeout)
    except KeyError:
        logger.error("Need at least motor GPIO")
        exit(1)

    # the close door sensor
    try:
        if motor:
            motor.set_close_sensor(configuration['door_closed_gpio'])
            logger.info("close door sensor activated")
    except KeyError:
        pass

    # the open door sensor
    try:
        if motor:
            motor.set_open_sensor(configuration['door_opened_gpio'])
            logger.info("open door sensor activated")
    except KeyError:
        pass

    # fake ephemeris, simulate ephemeris each milliseconds if set in configuration file
    try:
        if configuration['fake_ephemeris']:
            fake_ephemeris = configuration['fake_ephemeris']
    except KeyError:
        fake_ephemeris = None

    # prepare email sender if configuration is done. It will be used each time wifi is activated
    # if there is log to send
    email = EmailSender(configuration, logger)

    control = AutomaticControl(configuration, motor, fake_ephemeris)
    control.automatic_control()

    '''
    def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080, token='votre_token_secret'):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class, token=token)
    '''
    try:
        http_server = ApiHttpServer(server_address, CommandRequestHandler, (configuration['http_token'], open_door, close_door,
                                                                           force_open_door(), force_close_door()))
    except KeyError:
        logger.error('No http_token, so no http server !')

    try:
        watch_time = configuration['watch_dog']
    except KeyError:
        watch_time = 300
    watchdog = WatchDog(watch_time, email)

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
