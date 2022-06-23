import RPi.GPIO as GPIO
import time


class RaspberryUtils:
    def __init__(self):
        self.PIN_BEEP = 8
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN_BEEP, GPIO.OUT, initial=1)

    def __del__(self):
        GPIO.cleanup()

    def BeepSync(self, duration, t=1):
        while t>0:
            t -= 1
            GPIO.output(self.PIN_BEEP, 0)
            time.sleep(duration)
            GPIO.output(self.PIN_BEEP, 1)
            time.sleep(duration)


raspberryUtils = RaspberryUtils()


class MusicPlayer:
    def __init__(self):
        # [60, 71]       1    1#   2    2#   3    4    4#   5    5#   6    6#   7
        self.FREQ_LOW = [262, 277, 294, 311, 330, 349, 370, 392, 415, 440, 466, 494]
        # [72, 83]       1    1#   2    2#   3    4    4#   5    5#   6    6#   7
        self.FREQ_MID = [523, 554, 587, 622, 659, 698, 740, 784, 831, 880, 932, 988]
        # [84, 95]       1      1#    2     2#    3     4     4#    5     5#    6     6#    7
        self.FREQ_HIGH = [1046, 1109, 1175, 1245, 1318, 1397, 1480, 1568, 1661, 1760, 1865, 1976]
        self.PIN_SPEAKER = 25
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN_SPEAKER, GPIO.OUT, initial=0)
        self.pwm = GPIO.PWM(self.PIN_SPEAKER, 1)
        self.pwm.ChangeDutyCycle(0)
        self.pwm.start(0)
    
    def __startPwm(self):
        self.pwm.ChangeDutyCycle(50)
    
    def __stopPwm(self):
        self.pwm.ChangeDutyCycle(0)
    
    def playNote(self, note, duration):
        freq = -1
        if 60 <= note <= 71:
            freq = self.FREQ_LOW[note-60]
        elif 72 <= note <= 83:
            freq = self.FREQ_MID[note-72]
        elif 84 <= note <= 95:
            freq = self.FREQ_HIGH[note-84]
        if freq != -1:
            self.pwm.ChangeFrequency(freq)
            self.pwm.ChangeDutyCycle(30)
        time.sleep(duration)
        self.pwm.ChangeDutyCycle(0)

    def testSound(self):
        for note in self.FREQ_LOW:
            self.__startPwm()
            self.pwm.ChangeFrequency(note)
            time.sleep(0.2)
            self.__stopPwm()
            time.sleep(0.2)

        for note in self.FREQ_MID:
            self.__startPwm()
            self.pwm.ChangeFrequency(note)
            time.sleep(0.2)
            self.__stopPwm()
            time.sleep(0.2)

        for note in self.FREQ_HIGH:
            self.__startPwm()
            self.pwm.ChangeFrequency(note)
            time.sleep(0.2)
            self.__stopPwm()
            time.sleep(0.2)

musicPlayer = MusicPlayer()
if __name__ == "__main__":
    try:
        f = open('music.csv', "r")
        lines = f.readlines()
        for line in lines:
            note, duration = line.split(',')
            musicPlayer.playNote(int(note), float(duration))
        f.close()
    except KeyboardInterrupt:
        musicPlayer.pwm.ChangeDutyCycle(0)
        GPIO.cleanup()
