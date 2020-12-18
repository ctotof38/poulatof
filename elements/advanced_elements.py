# --------------------------------------------------
# software develop for Raspberry Pi
# It use gpiozero and if not present, use sgpiozero which simulate this library
# --------------------------------------------------
import time
import threading
import logging

RASPBERRY = True

try:
    from gpiozero import Button
    from gpiozero import LED
    from gpiozero import Motor
except ModuleNotFoundError:
    RASPBERRY = False
    from simulator.sgpiozero import Button
    from simulator.sgpiozero import LED
    from simulator.sgpiozero import Motor
    from simulator.sgpiozero import CheckButton

logger = logging.getLogger('advanced_elements')


# class which implement Button which manage short and long press.
#   default value for short press = 100ms
#   default value for long press = 2000ms
class AdvancedButton:
    def __init__(self, gpio, short_callback, long_callback, short_press_time=100, long_press_time=2000):
        self.button = Button(gpio)
        self.press_time = 0
        self.long_press = long_press_time
        self.short_press = short_press_time
        self.short_callback = short_callback
        self.long_callback = long_callback
        self.button.when_pressed = self.pressed
        self.button.when_released = self.released

    def pressed(self):
        self.press_time = int(round(time.time() * 1000))

    def released(self):
        time_pressed = int(round(time.time() * 1000)) - self.press_time
        if time_pressed > self.long_press:
            logger.debug("long press")
            if self.long_callback:
                callback = threading.Timer(0.005, self.long_callback)
                callback.start()
        elif time_pressed > self.short_press and self.short_callback:
            logger.debug("short press")
            callback = threading.Timer(0.005, self.short_callback)
            callback.start()


# class which implement Button which manage short, long and multiple press.
#   default value for multiple press = 40ms
#   default value for short press = 160ms
#   default value for long press = 2000ms
# if multiple time < press time < short press, and multiple_number reached, then call multiple_callback if not None
# and the multiple press is not exceeded 2 seconds
class MasterButton(AdvancedButton):
    def __init__(self, gpio, short_callback, long_callback, short_press_time=160, long_press_time=2000,
                 multiple_callback=None, multiple_press_time=40, multiple_number=3):
        super().__init__(gpio, short_callback, long_callback, short_press_time, long_press_time)
        self.multiple_callback = multiple_callback
        self.multiple_press = multiple_press_time
        self.multiple_number = multiple_number
        self.current_count = 0
        self.last_release = time.time()

    def released(self):
        current_release = time.time()
        delta_release = current_release - self.last_release
        time_pressed = int(round(current_release * 1000)) - self.press_time
        self.last_release = current_release

        if self.multiple_callback and self.short_press > time_pressed > self.multiple_press:
            self.current_count += 1
            if self.current_count >= self.multiple_number and delta_release < 2:
                self.current_count = 0
                callback = threading.Timer(0.005, self.multiple_callback)
                callback.start()
        else:
            self.current_count = 0
            if time_pressed > self.long_press:
                if self.long_callback:
                    callback = threading.Timer(0.005, self.long_callback)
                    callback.start()
            elif time_pressed > self.short_press and self.short_callback:
                callback = threading.Timer(0.005, self.short_callback)
                callback.start()


# class which implement Led and add blink method
class AdvancedLed:
    def __init__(self, gpio):
        self.led = LED(gpio)
        self.blink_thread = None

    def on(self):
        if self.blink_thread:
            self.blink_thread.stop()
            self.blink_thread = None
        logger.debug("LED on")
        self.led.on()

    def off(self):
        if self.blink_thread:
            self.blink_thread.stop()
            self.blink_thread = None
        logger.debug("LED off")
        self.led.off()

    def toggle(self):
        if self.blink_thread:
            self.blink_thread.stop()
            self.blink_thread = None
        logger.debug("LED toggle")
        self.led.toggle()

    def blink(self, tempo=0.5, max_time=100, callback=None):
        if not self.blink_thread:
            logger.debug("LED blink")
            self.blink_thread = LedBlinking(self.led, tempo, max_time, callback)
            self.blink_thread.start()

    def is_lit(self):
        return self.led.is_lit


# class which manage motor to open/close dore, with auto stop on high/low sensor
# consider forward to open door (so, can't run if open_sensor is pressed)
#          and backward to close door (so, can't run if close_sensor is pressed)
# max_time is the time before the motor will be stop. It is a security
class AdvancedMotor:
    def __init__(self, forward, backward, max_time=120):
        self.motor = Motor(forward=forward, backward=backward)
        self.close_sensor = None
        self.open_sensor = None
        self.max_time = max_time
        self.timer = None

    # open door if sensor is not pressed. Return True if ok
    def open_door(self):
        if not self.is_open_sensor_pressed():
            if self.timer:
                self.timer.cancel()
            logger.info("open door")
            self.motor.forward()
            self.timer = threading.Timer(self.max_time, self.stop, args=("max time reached",))
            self.timer.start()
            return True
        return False

    # close door if sensor is not pressed. Return True if ok
    def close_door(self):
        if not self.is_close_sensor_pressed():
            if self.timer:
                self.timer.cancel()
            logger.info("close door")
            self.motor.backward()
            self.timer = threading.Timer(self.max_time, self.stop, args=("max time reached",))
            self.timer.start()
            return True
        return False

    # reverse if motor is active. Return True if ok
    def reverse_door(self):
        if self.motor.is_active:
            if self.timer:
                self.timer.cancel()
            logger.info("reverse door")
            self.motor.reverse()
            self.timer = threading.Timer(self.max_time, self.stop, args=("max time reached",))
            self.timer.start()
            return True
        return False

    # stop if motor is active. Return True if ok
    def stop(self, warning=None, message=None):
        if self.motor.is_active:
            if self.timer:
                self.timer.cancel()
            if warning:
                logger.warning("stop door: " + warning)
            else:
                if message:
                    logger.info("stop door: " + message)
                else:
                    logger.info("stop door")
            self.motor.stop()
            return True
        return False

    def is_active(self):
        return self.motor.is_active

    # check close sensor. If not present, return True
    # so, can't run backward to close the door
    def is_close_sensor_pressed(self):
        if self.close_sensor:
            return self.close_sensor.is_pressed
        return True

    # check open sensor. If not present, return True
    # so, can't run forward to open the door
    def is_open_sensor_pressed(self):
        if self.open_sensor:
            return self.open_sensor.is_pressed
        return True

    def close_sensor_pressed(self):
        logger.debug("close door is reached")
        self.stop(message="close door is reached")

    def open_sensor_pressed(self):
        logger.debug("open door is reached")
        self.stop(message="open door is reached")

    def set_close_sensor(self, gpio):
        if RASPBERRY:
            self.close_sensor = Button(gpio)
            self.close_sensor.when_pressed = self.close_sensor_pressed
        else:
            self.close_sensor = CheckButton(gpio, "close")
            self.close_sensor.when_pressed = self.close_sensor_pressed

    def set_open_sensor(self, gpio):
        if RASPBERRY:
            self.open_sensor = Button(gpio)
            self.open_sensor.when_pressed = self.open_sensor_pressed
        else:
            self.open_sensor = CheckButton(gpio, "open")
            self.open_sensor.when_pressed = self.open_sensor_pressed


# blink led during tempo, with max_time in seconds
# if set, call callback at the end of the thread
class LedBlinking (threading.Thread):
    def __init__(self, led, tempo=0.5, max_time=100, callback=None):
        super().__init__()
        self.led = led
        self.tempo = tempo
        self.active = False
        self.count = round(max_time / tempo)
        self.callback = callback

    def run(self) -> None:
        if self.active:
            return
        self.active = True
        while self.active and self.count > 0:
            self.led.toggle()
            self.count -= 1
            time.sleep(self.tempo)
        if self.callback:
            self.callback()

    def stop(self):
        self.active = False
        try:
            self.join(self.tempo * 2)
        except RuntimeError:
            # thread already stopped
            pass
