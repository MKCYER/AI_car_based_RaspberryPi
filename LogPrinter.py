import time
import atexit
import datetime

class LogPrinter:
    def __init__(self):
        self.beginTime = time.time()
        self.SavetoFile = False
        self.logFile = None

    def log(self, module, *data):
        data = [str(item) for item in data]
        logData = '[%12f] %s  %s' % (time.time()-self.beginTime, module, " ".join(data))
        print(logData)
        if self.SavetoFile == True:
            if self.logFile == None:
                self.logFile = open(datetime.datetime.now().strftime("%Y-%m-%d")+".log", "w")
            self.logFile.write(logData+"\n")
            # self.logFile.flush()
            
    # def __del__(self):
    #     if self.logFile != None and not self.logFile.closed():
    #         self.logFile.close()


logPrinter = LogPrinter()
# logPrinter.log("module", logPrinter)

@atexit.register
def exit_handler():
    if logPrinter.logFile != None and not logPrinter.logFile.closed:
             logPrinter.logFile.close()
