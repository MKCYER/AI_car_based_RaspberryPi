import RPi.GPIO as GPIO
import time
import threading
from LogPrinter import logPrinter


def log(*args):
    logPrinter.log("CameraControl", *args)


class Camera():
    # 11 up,9 down
    # down 110 is front
    # up 20 is straight
    def __init__(self) -> None:
        self.up = 9
        self.down = 11
        self.upAngle = 30
        self.downAngle = 75
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.up, GPIO.OUT)
        GPIO.setup(self.down, GPIO.OUT)
        self.pwmUp = GPIO.PWM(self.up, 50)
        self.pwmUp.start(0)
        self.pwmDown = GPIO.PWM(self.down, 50)
        self.pwmDown.start(0)
        self.ControlUp(self.upAngle)
        self.ControlDown(self.downAngle)

    def ControlUp(self, pos):
        self.pwmUp.ChangeDutyCycle(2.5 + 10 * pos/180)
        time.sleep(0.2)
        self.pwmUp.ChangeDutyCycle(0)
        log("Up Angle", pos)

    def ControlDown(self, pos):
        self.pwmDown.ChangeDutyCycle(2.5 + 10 * pos/180)
        time.sleep(0.2)
        self.pwmDown.ChangeDutyCycle(0)
        log("Down Angle", pos)


    def UpFront(self):
        self.upAngle = max(self.upAngle-5, -15)
        self.ControlUp(self.upAngle)

    def UpBack(self):
        self.upAngle = min(self.upAngle+5, 100)
        self.ControlUp(self.upAngle)

    def DownLeft(self):
        self.downAngle = min(self.downAngle+5, 180)
        self.ControlDown(self.downAngle)

    def DownRight(self):
        self.downAngle = max(self.downAngle-5, -25)
        self.ControlDown(self.downAngle)


camera = Camera()
if __name__ == "__main__":
    while True:
        a = input()
        if a == 'e':
            break
        camera.ControlDown(float(a))
