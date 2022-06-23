import RPi.GPIO as GPIO
import time
from CarMove import carMovement
import threading
from RaspberryUtils import raspberryUtils
from DestoryThread import destory

class ObstacleAvoid():
    def __init__(self) -> None:
        self.Left = 12
        self.Right = 17
        self.platform = 23
        self.shot = 0
        self.get = 1
        self.car = carMovement
        self.isrun = False
        self.thread=None
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.Left, GPIO.IN)
        GPIO.setup(self.Right, GPIO.IN)
        GPIO.setup(self.shot, GPIO.IN)
        GPIO.setup(self.get, GPIO.OUT)
        GPIO.setup(self.platform, GPIO.OUT)
        self.pwm_servo = GPIO.PWM(self.platform, 25)
        self.pwm_servo.start(0)

    def Distance_test(self):
        GPIO.output(self.get, GPIO.HIGH)
        time.sleep(0.000015)
        GPIO.output(self.get, GPIO.LOW)
        while not GPIO.input(self.shot):
            pass
        t1 = time.time()
        while GPIO.input(self.shot):
            pass
        t2 = time.time()
        #print("distance is %d " % (((t2 - t1)* 340 / 2) * 100))
        return ((t2 - t1) * 340 / 2) * 100

    def servo_appointed_detection(self, pos):
        self.pwm_servo.ChangeDutyCycle(2.5 + 10 * pos/180)

    def align(self):
        val = []
        for i in range(-30, 50, 15):
            self.servo_appointed_detection(i)
            val.append(self.Distance_test())
            time.sleep(0.5)
        if val.index(max(val)) > 10:
            self.car.right()
            time.sleep(1.5)
            self.car.stop()
        else:
            self.car.left()
            time.sleep(1.5)
            self.car.stop()

    def run(self):
        raspberryUtils.BeepSync(0.1, 3)
        while self.isrun:
            i = 10
            while i > 0:
                LValue = GPIO.input(self.Left)
                RValue = GPIO.input(self.Right)
                if LValue == 0 and RValue == 0:
                    self.align()
                if LValue == 0:
                    k = 0.1
                    while True:
                        LValue = GPIO.input(self.Left)
                        if LValue == 1:
                            break
                        self.car.right()
                        time.sleep(k)
                        k += 0.05
                        self.car.stop()
                if RValue == 0:
                    k = 0.1
                    while True:
                        RValue = GPIO.input(self.Right)
                        if RValue == 1:
                            break
                        self.car.left()
                        time.sleep(k)
                        k += 0.05
                        self.car.stop()
                self.car.run()
                time.sleep(0.5)
                self.car.stop()
                i -= 1

    def start(self):
        self.isrun = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.isrun:
            destory.stop_thread(self.thread)
            self.car.stop()
        self.isrun = False
        raspberryUtils.BeepSync(1)


obstacleAvoid = ObstacleAvoid()
if __name__ == '__main__':
    test = ObstacleAvoid()
    test.start()
    time.sleep(100)
    test.stop()
