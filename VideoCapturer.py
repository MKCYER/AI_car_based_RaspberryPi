import time
import cv2
import threading
from LogPrinter import logPrinter

def log(*args):
    logPrinter.log("Videocapturer", *args)

class Videocapturer:
    def __init__(self, url=''):
        self.url = url
        self._beginCapture = False
        self._curFrame = None
        self._curFrameTaken = True
        self._frameCaptured = 0
        self._frameTaken = 0
        self._lastFrameCaptureTime = 0
        self._lastFrameTakenTime = 0
        self._notifyThreadStarted = False
        self.onFrameCapturedCallback:function = None
        self.frameFps = 0
        self.realFps = 0
        self.loss = 0
        self.__UpdateAlpha = 0.5

    def notifyThread(self):
        log("Notify thread started.")
        self._notifyThreadStarted = True
        while self._beginCapture:
            while self._curFrameTaken:
                time.sleep(0.001)
            self._curFrameTaken = True
            self._frameTaken += 1
            # log("Callback begin.")
            self.onFrameCapturedCallback(self._curFrame)
            # log("Callback end.")

            self.loss = self.loss*self.__UpdateAlpha + (1-(self._frameTaken/self._frameCaptured))*(1-self.__UpdateAlpha)
            if time.time_ns()-self._lastFrameTakenTime != 0:
                self.realFps = self.realFps*self.__UpdateAlpha + (1e9/(time.time_ns()-self._lastFrameTakenTime))*(1-self.__UpdateAlpha)
            self._lastFrameTakenTime = time.time_ns()
            # log("FPS", self.realFps)
        log("Notify thread terminated.")
        self._notifyThreadStarted = False
        

    def start(self):
        log("VideoCapturer started.")
        self._frameCaptured = 0
        self._frameTaken = 0
        self._beginCapture = True
        self.notifyer = threading.Thread(target=self.notifyThread, name='Thread_VideoNotify')
        self.notifyer.daemon = True
        self.capturer = cv2.VideoCapture(self.url)
        def read_frame():
            while self._beginCapture:
                # log("Requesting frame..")
                res, self._curFrame = self.capturer.read()
                # log("Frame captured.")

                if not res:
                    log("Frame read timeout, retry in 5s.")
                    time.sleep(5)
                    self.capturer = cv2.VideoCapture(self.url)
                    continue
                if time.time_ns()-self._lastFrameCaptureTime != 0:
                    self.frameFps = self.frameFps*self.__UpdateAlpha + (1e9/(time.time_ns()-self._lastFrameCaptureTime))*(1-self.__UpdateAlpha)
                self._lastFrameCaptureTime = time.time_ns()
                self._curFrameTaken = False
                if self._frameCaptured > 100:
                    self._frameCaptured = 0
                    self._frameTaken = 0
                self._frameCaptured += 1
                if not self._notifyThreadStarted:
                    self._notifyThreadStarted = True
                    self.notifyer.start()
        
        thread = threading.Thread(target=read_frame, name='Thread_VideoCapture')
        thread.daemon = True
        thread.start()
    
    def stop(self):
        self.beginCapture = False
        self.frameFps = 0
        self.realFps = 0
        self.loss = 0