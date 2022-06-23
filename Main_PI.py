print("Importing packages...")
import json
import threading
from cv2 import imwrite
from RaspberryUtils import raspberryUtils
from TCPServer import TCPServer
import time
from CCmds import CCmds, Cmd2Bytes
from LogPrinter import logPrinter
from multiprocessing import Process
from CarMove import carMovement
from CameraControl import camera
from AutoMByTrace import flowTrace
from AvoidObstacle import obstacleAvoid
from FireDetection import model
from VideoCapturer import Videocapturer
from GetTemHum import temhum


def log(*args):
    logPrinter.log("MainApp_PI", *args)

class Controller:
    def onConnect(self, client):
        log("Client Connected:", client.getpeername())

    def onDisconnect(self):
        log("Client Disconnected.")

    def onMsgReceived(self, client, msg):
        log("Msg received:", msg, client.getpeername())
        msgs = msg
        for msg in msgs:
            if msg & CCmds.MODE_CONTROL:
                if msg & CCmds.MODE_MANUAL_CONTROL:
                    log("Control Command Received: MODE_MANUAL_CONTROL")
                    if flowTrace.isrun:
                        flowTrace.stop()
                    if obstacleAvoid.isrun:
                        obstacleAvoid.stop()
                    carMovement.stop()
                elif msg & CCmds.MODE_AUTO_WIRE:
                    log("Control Command Received: MODE_AUTO_WIRE")
                    if obstacleAvoid.isrun:
                        obstacleAvoid.stop()
                    if not flowTrace.isrun:
                        flowTrace.start()
                elif msg & CCmds.MODE_AUTO_MOVE:
                    log("Control Command Received: MODE_AUTO_MOVE")
                    if flowTrace.isrun:
                        flowTrace.stop()
                    if not obstacleAvoid.isrun:
                        obstacleAvoid.start()
            elif msg & CCmds.MOVE_CONTROL:
                if msg & CCmds.MOVE_STOP:
                    log("Control Command Received: MOVE_STOP")
                    carMovement.stop()
                elif msg & CCmds.MOVE_FORWARD:
                    log("Control Command Received: MOVE_FORWARD")
                    carMovement.run()
                elif msg & CCmds.MOVE_BACK:
                    log("Control Command Received: MOVE_BACK")
                    carMovement.back()
                elif msg & CCmds.MOVE_LEFT:
                    log("Control Command Received: MOVE_LEFT")
                    carMovement.left()
                elif msg & CCmds.MOVE_RIGHT:
                    log("Control Command Received: MOVE_RIGHT")
                    carMovement.right()
            elif msg & CCmds.CAMERA_CONTROL:
                if msg & CCmds.CAMERA_UP:
                    log("Control Command Received: CAMERA_UP")
                    camera.UpBack()
                elif msg & CCmds.CAMERA_DOWN:
                    log("Control Command Received: CAMERA_DOWN")
                    camera.UpFront()
                elif msg & CCmds.CAMERA_LEFT:
                    log("Control Command Received: CAMERA_LEFT")
                    camera.DownLeft()
                elif msg & CCmds.CAMERA_RIGHT:
                    log("Control Command Received: CAMERA_RIGHT")
                    camera.DownRight()
            elif msg & CCmds.PING:
                log("Control Command Received: PING")
                client.send(Cmd2Bytes(CCmds.PING))

def initTcpServer():
    tcpserver = TCPServer(maxConnections=1)
    tcpserver.addOnConnectListener(controller.onConnect)
    tcpserver.addOnDisconnectListener(controller.onDisconnect)
    tcpserver.addOnMessageReceivedListener(controller.onMsgReceived)
    tcpserver.start()
    return tcpserver

def VideoProcessing(img):
    st = time.time()
    imgOut, hasFire = model.detect(img)
    log(f"FireDetection Result ({(time.time()-st)*1000} ms):", hasFire)
    if hasFire:
        imwrite('/usr/local/share/mjpg-streamer/www/fire.jpg', imgOut)
        # os.system("mv fire.jpg /usr/local/share/mjpg-streamer/www/fire.jpg")
        raspberryUtils.BeepSync(0.2, t=3)

def videoProcess():
    vc = Videocapturer("http://127.0.0.1:8080/?action=stream")
    vc.onFrameCapturedCallback = VideoProcessing
    vc.start()
    while True:
        time.sleep(5)

def tempThread():
    while True:
        time.sleep(5)
        temperature, humidity = temhum.getTemHum()
        if temperature == None:
            continue
        with open("/usr/local/share/mjpg-streamer/www/temp.json", 'w') as f:
            f.write(json.dumps({
                'temp': temperature,
                'humi': humidity
            }))

if __name__ == "__main__":
    try:
        logPrinter.SavetoFile = False
        controller = Controller()
        log("Starting TCP Server...")
        tcpserver = initTcpServer()
        log("Starting FireDetection Process...")
        videoP = Process(target=videoProcess)
        videoP.start()
        log("Starting DHT11 Thread...")
        tThread = threading.Thread(target=tempThread, daemon=True)
        tThread.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Program exitted gracefully.")
        if tcpserver.so != None:
            tcpserver.so.close()
        if videoP.is_alive():
            videoP.kill()
    