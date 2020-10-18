import tkinter as tk
import threading
import time


# button simulation
class Button:
    def __init__(self, gpio):
        self.gpio = gpio
        self.when_pressed = None
        self.when_released = None
        self.is_pressed = False
        ui = GpioUi()
        ui.add_button(self)

    # method used by tkinter
    def press_action(self, event):
        self.is_pressed = True
        if self.when_pressed:
            self.when_pressed()

    # method used by tkinter
    def release_action(self, event):
        self.is_pressed = False
        if self.when_released:
            self.when_released()


class CheckButton:
    def __init__(self, gpio, name=None):
        self.gpio = gpio
        self.name = name
        self.when_pressed = None
        self.is_pressed = False
        ui = GpioUi()
        self.checkbutton_state = ui.add_checkbutton(self)

    # call by tkinter
    def button_updated(self, *args):
        self.is_pressed = self.checkbutton_state.get()
        if self.when_pressed:
            if self.is_pressed:
                self.when_pressed()
        return False


# motor simulation
class Motor:
    def __init__(self, forward, backward):
        self.gpio_forward = forward
        self.gpio_backward = backward
        self.is_active = False
        self.direction = False
        self.motor = None
        ui = GpioUi()
        self.widget_motor = ui.add_motor(self)

    # open door
    def forward(self):
        self.direction = True
        self.is_active = True
        if self.motor:
            self.motor.stop()
        self.motor = MotorRunning(self.widget_motor, self.direction)
        self.motor.start()

    # close door
    def backward(self):
        self.direction = False
        self.is_active = True
        if self.motor:
            self.motor.stop()
        self.motor = MotorRunning(self.widget_motor, self.direction)
        self.motor.start()

    def reverse(self):
        if self.is_active:
            if self.motor:
                self.motor.stop()
            self.direction = not self.direction
            self.motor = MotorRunning(self.widget_motor, self.direction)
            self.motor.start()

    def stop(self):
        self.direction = 0
        self.is_active = False
        if self.motor:
            self.motor.stop()


class LED:
    def __init__(self, gpio):
        self.gpio = gpio
        self.is_lit = False
        ui = GpioUi()
        self.canvas = ui.add_led(self)
        self.led = self.canvas.find_all()[0]

    def on(self):
        self.is_lit = True
        self.canvas.itemconfig(self.led, fill="yellow")

    def off(self):
        self.is_lit = False
        self.canvas.itemconfig(self.led, fill="grey")

    def toggle(self):
        if self.is_lit:
            self.off()
        else:
            self.on()


# class which change color of arc to simulate movement
# open_door :
#    True = forward, so open, choose green color
#    False = backward, so close, choose red color
class MotorRunning (threading.Thread):
    def __init__(self, canvas, open_door):
        super().__init__()
        self.canvas = canvas
        self.open_door = open_door
        self.active = False
        elements = self.canvas.find_withtag("motor")
        for element in elements:
            self.canvas.itemconfig(element, fill="white")

    def run(self):
        if self.active:
            self.stop()
        self.active = True
        elements = self.canvas.find_withtag("motor")
        color = "green"
        if not self.open_door:
            color = "red"
            elements = elements[::-1]

        ui = GpioUi()
        if self.open_door:
            if ui.instance.close_sensor:
                ui.instance.close_sensor.deselect()
        else:
            if ui.instance.open_sensor:
                ui.instance.open_sensor.deselect()

        previous = None
        while self.active:
            for element in elements:
                if self.active:
                    if previous:
                        self.canvas.itemconfig(previous, fill="white")
                    self.canvas.itemconfig(element, fill=color)
                    previous = element
                    time.sleep(0.3)

    def stop(self):
        self.active = False
        self.join(2)
        elements = self.canvas.find_withtag("motor")
        for element in elements:
            self.canvas.itemconfig(element, fill="white")


class GpioUi(tk.Tk):
    class __GpioUi(tk.Tk):
        def __init__(self):
            self.root = tk.Tk.__init__(self)
            self.protocol("WM_DELETE_WINDOW", self.close_windows)
            self.title("Simulator")
            self.geometry("{}x{}+{}+{}".format(100, 200, 100, 100))
            self.motor = None
            self.open_sensor = None
            self.close_sensor = None

            self.frame = tk.Frame(self, width=150)

        def close_windows(self):
            self.destroy()

    instance = None

    def __init__(self):
        if not GpioUi.instance:
            GpioUi.instance = GpioUi.__GpioUi()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def add_button(self, button):
        widget_button = tk.Button(self.instance.frame, text=str(button.gpio))
        widget_button.bind('<ButtonPress-1>', button.press_action)
        widget_button.bind('<ButtonRelease-1>', button.release_action)
        widget_button.pack()

    def add_motor(self, motor):
        self.instance.motor = motor
        canvas = tk.Canvas(self.instance.frame, width=80, heigh=50, borderwidth=0, highlightthickness=0)
        # set tag to arc to simulate motor
        create_arc(canvas, 25, 25, 20, start=0, end=45, fill="white", tags="motor")
        create_arc(canvas, 25, 25, 20, start=45, end=90, fill="white", tags="motor")
        create_arc(canvas, 25, 25, 20, start=90, end=135, fill="white", tags="motor")
        create_arc(canvas, 25, 25, 20, start=135, end=180, fill="white", tags="motor")
        create_arc(canvas, 25, 25, 20, start=180, end=225, fill="white", tags="motor")
        create_arc(canvas, 25, 25, 20, start=225, end=270, fill="white", tags="motor")
        create_arc(canvas, 25, 25, 20, start=270, end=315, fill="white", tags="motor")
        create_arc(canvas, 25, 25, 20, start=315, end=360, fill="white", tags="motor")

        canvas.create_polygon(60, 20, 80, 20, 70, 10, 60, 20, fill="green", outline="green")
        canvas.create_polygon(60, 30, 80, 30, 70, 40, 60, 30, fill="red", outline="red")

        canvas.pack()
        return canvas

    def add_led(self, led):
        canvas = tk.Canvas(self.instance.frame, width=30, heigh=30, borderwidth=0, highlightthickness=0)
        circle = create_circle(canvas, 13, 13, 10, outline="black", width=2)
        canvas.itemconfig(circle, fill="grey")
        canvas.pack()
        return canvas

    def add_checkbutton(self, checkbutton):
        var = tk.IntVar()
        name = checkbutton.name
        if not name:
            name = str(checkbutton.gpio)
        widget_checkbutton = tk.Checkbutton(self.instance.frame, text=name, variable=var)
        if name:
            if "close" in name:
                self.instance.close_sensor = widget_checkbutton
            else:
                self.instance.open_sensor = widget_checkbutton
        var.trace("w", checkbutton.button_updated)
        widget_checkbutton.pack()
        return var

    def show_ui(self):
        self.instance.frame.pack()
        self.instance.mainloop()


# x and y are center
# r is the radius
def create_circle(canvas, x, y, r, **kwargs):
    return canvas.create_oval(x-r, y-r, x+r, y+r, **kwargs)


def create_arc(canvas, x, y, r, **kwargs):
    if "start" in kwargs and "end" in kwargs:
           kwargs["extent"] = kwargs["end"] - kwargs["start"]
           del kwargs["end"]
    return canvas.create_arc(x-r, y-r, x+r, y+r, **kwargs)