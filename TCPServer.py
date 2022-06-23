import socket
import threading
from LogPrinter import logPrinter

def log(*args):
    logPrinter.log("TCPServer", *args)

class TCPServer():
    def __init__(self, host="0.0.0.0", port=39702, maxConnections=100):
        self.so = None
        self.host = host
        self.port = port
        self.maxConnections = maxConnections
        self.activeConnections = 0
        self.onConnectCallback = []
        self.msgReceivedCallback = []
        self.onDisconnectCallback = []
        self.connManager = None
        self.clientHandler = []

    def addOnConnectListener(self, callback):
        self.onConnectCallback.append(callback)

    def addOnMessageReceivedListener(self, callback):
        self.msgReceivedCallback.append(callback)
    
    def addOnDisconnectListener(self, callback):
        self.onDisconnectCallback.append(callback)

    def __clientHandler(self, client):
        while True:
            try:
                msg = client.recv(1024)
                if len(msg) == 0:
                    raise Exception("Client Disconnected.")
                for func in self.msgReceivedCallback:
                    func(client, msg)
            except Exception as ex:
                log(ex)
                self.activeConnections -= 1
                for func in self.onDisconnectCallback:
                    func()
                break

    def start(self):
        thread = threading.Thread(target=self.__start_socket)
        thread.daemon = True
        thread.start()

    def __start_socket(self):
        # 建立Socket连接, AF_INEF使用IPv4地址, SOCK_STREAM使用TCP协议
        self.so = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.so.bind((self.host, self.port))
        self.so.listen()
        log("Start listening on %s:%d" %(self.host, self.port))

        while True:
            conn, addr = self.so.accept()
            log("New connection accepted.")
            if self.activeConnections >= self.maxConnections:
                log(f"Drop Client: {addr}")
                conn.close()
                continue
            self.activeConnections += 1
            for func in self.onConnectCallback:
                func(conn)
            log(f"Client: {addr} connected.")

            thread = threading.Thread(target=self.__clientHandler, args=(conn,))
            thread.daemon = True
            thread.start()


if __name__ == '__main__':
    tcpsocket = TCPServer(maxConnections=1)
    tcpsocket.start()
