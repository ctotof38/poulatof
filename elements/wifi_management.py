import threading
import subprocess
import os
import logging

logger = logging.getLogger('wifi_management')


# manage Wifi script to start and stop interface and look for network
class WifiManagement:
    def __init__(self, wifi_script, interface=None, timeout_wifi_connected=20):
        if not os.access(wifi_script, os.X_OK):
            raise FileNotFoundError
        self.wifi_script = wifi_script
        self.interface = interface
        self.command = None
        self.timeout = timeout_wifi_connected
        # call by check wifi
        self.current_callback = None
        self.return_code_expected = 2

    def stop_wifi(self, callback=None,):
        if not self.command or not self.command.is_alive():
            self.current_callback = callback
            self.return_code_expected = 0
            if self.interface:
                action = [self.wifi_script, "-d", "-n", self.interface]
            else:
                action = [self.wifi_script, "-d"]
            self.command = ScriptAction(action, self.check_wifi, timeout=self.timeout)
            self.command.start()
            return True
        return False

    # the start command memorise callback, and set check_wifi callback, which will use the memorized callback
    def start_wifi(self, callback=None):
        logger.debug("start_wifi")
        if not self.command or not self.command.is_alive():
            self.current_callback = callback
            self.return_code_expected = 2
            if self.interface:
                action = [self.wifi_script, "-a", "-n", self.interface]
            else:
                action = [self.wifi_script, "-a"]
            self.command = ScriptAction(action, self.check_wifi, timeout=self.timeout)
            self.command.start()
            return True
        return False

    # call start_callback if exists
    #   255 if start is incorrect
    #   0 if wifi down
    #   1 if wifi up but not connected
    #   2 if wifi up and connected
    def check_wifi(self, return_code):
        logger.debug("check_wifi : " + str(return_code))
        if return_code != 0:
            if self.current_callback:
                self.current_callback(255)
            return 255

        if self.interface:
            action = [self.wifi_script, "-c", "-n", self.interface, "-t", str(self.timeout), "-r",
                      str(self.return_code_expected)]
        else:
            action = [self.wifi_script, "-c", "-t", str(self.timeout), "-r", str(self.return_code_expected)]
        command = ScriptAction(action, self.current_callback)
        command.start()
        self.current_callback = None


# launch script
# call callback if exists with return code
# optional timeout, default=90 seconds
#    if timeout reached, return code is 255
class ScriptAction (threading.Thread):
    def __init__(self, command, callback=None, timeout=90):
        super().__init__()
        self.command = command
        self.callback = callback
        self.timeout = timeout

    def run(self):
        try:
            logger.debug(str(self.command))
            result = subprocess.run(self.command, timeout=self.timeout)
            if self.callback:
                self.callback(result.returncode)
        except subprocess.TimeoutExpired:
            logger.debug("command expired")
            if self.callback:
                self.callback(255)

