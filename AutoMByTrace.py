from email.errors import NonPrintableDefect
import RPi.GPIO as GPIO
import time
from CarMove import carMovement
import threading
from RaspberryUtils import raspberryUtils
from DestoryThread import destory


class FlowTrance():
    def __init__(self) -> None:
        self.Pl = 3
        self.Pml = 5
        self.Pmr = 4
        self.Pr = 18
        self.car = carMovement
        self.isrun = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.Pl, GPIO.IN)
        GPIO.setup(self.Pml, GPIO.IN)
        GPIO.setup(self.Pmr, GPIO.IN)
        GPIO.setup(self.Pr, GPIO.IN)

    def run(self):
        raspberryUtils.BeepSync(0.1, 2)
        #0 is black
        perml=None
        permr=None
        while self.isrun:
            i = 10
            while i > 0:
                PlValue = GPIO.input(self.Pl)
                PmlValue = GPIO.input(self.Pml)
                PmrValue = GPIO.input(self.Pmr)
                PrValue = GPIO.input(self.Pr)
                if PlValue == 0 and PrValue == 0:
                    self.car.run()
                    time.sleep(0.5)
                    self.car.stop()
                    i -= 1
                    continue
                if PlValue == 0:
                    if perml==1 or permr==1:
                        while True:
                            PmlValue = GPIO.input(self.Pml)
                            PmrValue = GPIO.input(self.Pmr)
                            if PmlValue == 0 or PmrValue == 0:
                                break
                            self.car.fleft()
                            time.sleep(0.05)
                            self.car.stop()
                    else:
                        while True:
                            PmlValue = GPIO.input(self.Pml)
                            PmrValue = GPIO.input(self.Pmr)
                            if PmlValue == 0 or PmrValue == 0:
                                break
                            self.car.left()
                            time.sleep(0.05)
                            self.car.stop()
                if PrValue == 0:
                    if perml==1 or permr==1:
                        while True:
                            PmlValue = GPIO.input(self.Pml)
                            PmrValue = GPIO.input(self.Pmr)
                            if PmlValue == 0 or PmrValue == 0:
                                break
                            self.car.fright()
                            time.sleep(0.05)
                            self.car.stop()
                    else:
                        while True:
                            PmlValue = GPIO.input(self.Pml)
                            PmrValue = GPIO.input(self.Pmr)
                            if PmlValue == 0 or PmrValue == 0:
                                break
                            self.car.right()
                            time.sleep(0.05)
                            self.car.stop()
                self.car.run()
                time.sleep(0.5)
                self.car.stop()
                perml=PmlValue
                permr=PmrValue
                i -= 1

    def stop(self):
        if self.isrun:
            destory.stop_thread(self.thread)
            self.car.stop()
        self.isrun = False
        raspberryUtils.BeepSync(1)

    def start(self):
        self.isrun = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()


flowTrace = FlowTrance()
if __name__=="__main__":
    flowTrace.start()
    while True:
        time.sleep(1)
    
