# https://fte.com/webhelpii/bpa600/Content/Technical_Information/BT_Snoop_File_Format.htm
import sys
import serial
#import serial.tools.list_ports as port_list
import time
#import math
import multiprocessing as mp
#import BtSnoop
#import HciSnoopTesterCore
import signal
import pyaudio
import sys, wave, threading, random

#======= Configurations ======
gDevNode = {}

#====== Global variables ===========================================================
handlerState = 0

#======= Classes ======
class DEV_NODE:
    def __init__(self, baudRate, port, tabFile, serialInfo, loopCount, gRxBuf):
        self.port = port
        self.baudRate = baudRate
        self.serialInfo = serialInfo
        self.loopCount = loopCount  
        self.gRxBuf = gRxBuf
        self.tabFile = open(tabFile, "r")
        filePtr = ""
        currentCmd = ""
        logFile = []
        logFileName = ""

class THREAD_SET:
    def __init__(self):
        self.startEvent = [];
        self.stopEvent = [];

class AUDIO_CONFIG:
    def __init__(self):
        self.chunk = 1024                       # 記錄聲音的樣本區塊大小
        self.sample_format = pyaudio.paInt16    # 樣本格式，可使用 paFloat32、paInt32、paInt24、paInt16、paInt8、paUInt8、paCustomFormat
        self.channels = 1                       # 聲道數量
        self.fs = 48000                         # 取樣頻率，常見值為 44100 ( CD )、48000 ( DVD )、22050、24000、12000 和 11025。
        self.fileName = ""
        self.f = []
        self.running = 0x0
        self.p = []

#===================================================================================# 
def GetSerialPortInfo():
    ports = list(port_list.comports())    
    return ports      

def GetCongigureInfo():
    try:
        configFile = open("HCI_Tester.config", 'r')
    except:
        debugPrint(True, "Congifure file can not be found")
        exit()

    retTab = {}
    while(1):
        readL = configFile.readline()
        
        if(readL == ""):
            break;
        readL = readL.split()
        retTab[readL[0]] = readL[1]
    configFile.close()
    return retTab

def isSerialModeEnable(cpuCount, devNum, serialModeEn):
    if(cpuCount < devNum or serialModeEn == True):  #Serial mode
        return True
    else:
        return False

BAUD_RATE = 115200
COMPORT = "COM22"
event = THREAD_SET()
audioConfig = AUDIO_CONFIG()


def send_txData(devNode, txData):
    ser = devNode.serialInfo  
    txData = txData.strip()  
    
    ##txData = bytearray(txData,'ascii')   
    ##txData = bytes.fromhex(txData)
    #print(txData)   
    
    tmp = []
    for c in txData:
        tmp.append(ord(c))
    tmp.append(ord("\n"))
    ser.write(bytes(tmp))


def get_rxData_into_rxBuffer(devNode):
    ser = devNode.serialInfo
    keepRx = False
    byteInBuffer = 0x1
    rx = ""
    while(byteInBuffer):
        byteInBuffer = ser.in_waiting
        if(byteInBuffer != 0):
            rx = rx + (ser.read(byteInBuffer)).hex()
    #rx = "2a2a2a2045"
    
    if(rx != ""):
        flag = True
    else:
        flag = False
    while(rx != ""):
        data = "0x" + rx[0:2]
        data = chr(int(data,16))
        #print(rx[0:2], data)
        rx = rx[2:]
        devNode.gRxBuf = devNode.gRxBuf + data
    
    #if(flag == True):
    #    print(devNode.gRxBuf)
    
    return flag

def script_cmd_Handler(devNode, cmd, line):
    if(cmd[0] != ";"):
        if(cmd[0:5] == "PAUSE" or cmd[0:5] == "pause"):
            para = cmd.split()[1]
            print("PAUSE" + para)
            time.sleep(para)
        elif(cmd[0:4] == "wait"):
            pos  = cmd.find(";")
            cmd = cmd[5:pos].strip()
            
            para = cmd.split("\"")
            para = para[1:]
            print(line, "\tWaitRx:", para)
            readData = ""
            for i in range(0,len(para)):
                checkStr = para[i];
                checkLen = len(checkStr.strip())
                
                if(checkLen != 0):
                    while(True):
                        readDataFlag = get_rxData_into_rxBuffer(devNode)
                        if(readDataFlag == True and checkStr in devNode.gRxBuf):
                            break
            devNode.logFile.write(devNode.gRxBuf)
            devNode.gRxBuf = ""
        elif(cmd[0:6] == "sendln"):
            para = cmd.split()[1]
            para = para.strip("\'")

            print(line, "\tTx:", para)
            send_txData(devNode, para)

def script_Handler(devNode):
    print(devNode.currentCmd)
    currentFile = open(devNode.currentCmd, "r")
    if(currentFile):
        devNode.serialInfo = serial.Serial(devNode.port, devNode.baudRate, timeout= (0.001/devNode.baudRate))
        ser = devNode.serialInfo
        ser.setRTS(True)
        ser.close()
        ser.open()
        ser.setRTS(True)
        
        lineCnt = 0x1
        
        while(1):
            cmd = currentFile.readline().strip()
            if(cmd ==""):
                break
            else:
                script_cmd_Handler(devNode, cmd, lineCnt)
                lineCnt = lineCnt+ 1

        #Store more data into console
        timeStamp0 = time.perf_counter() #time.time()
        timeStamp1 = timeStamp0
        
        while(timeStamp1 - timeStamp0 <= 5):
            readDataFlag = get_rxData_into_rxBuffer(devNode)
            if(readDataFlag == True):
                devNode.logFile.write(devNode.gRxBuf)
                devNode.gRxBuf = ""
            
            timeStamp1 = time.perf_counter()
        currentFile.close()
        ser.close()
#========== Audio Part ==================================================#
def Audio_recording():
    global run, name
    global audioConfig
    global run, event

    p = pyaudio.PyAudio()
    stream = p.open(format   = audioConfig.sample_format, 
                    channels = audioConfig.channels, 
                    rate     = audioConfig.fs, 
                    frames_per_buffer=audioConfig.chunk, input=True)

    wf = wave.open(audioConfig.fileName, 'wb')                      
    wf.setnchannels(audioConfig.channels)                           
    wf.setsampwidth(p.get_sample_size(audioConfig.sample_format))   
    wf.setframerate(audioConfig.fs)                                 
    
    while True:
        event.startEvent.wait()             
        event.startEvent.clear()            
        audioConfig.running = 0x02
        run = audioConfig.running           
        print('\tStart audio record')
        frames = [] 
        while(run == 0x02):
            data = stream.read(audioConfig.chunk)
            frames.append(data)
            if(len(frames) > 2):
                wrFrames = frames[0 : 2]
                wf.writeframes(b''.join(wrFrames))
                frames = frames[2 : ]
            
            run = audioConfig.running
        
        stream.stop_stream()             
        stream.close()                   
        p.terminate()
        event.stopEvent.wait()           
        event.stopEvent.clear()          
        wf.close()
        print("\tStop audio record")
        audioConfig.running = 0x00
        break

def audio_record_handler(flag):
    global event, audioConfig
    
    if(flag == True):
        timePofix = time.strftime("%Y%m%d%H%M%S", time.localtime())
        audioConfig.fileName = "Audio_Record_"+timePofix+".wav"
        audioConfig.running = 0x01
        running = audioConfig.running
        eventStart = threading.Event()   # 註冊錄音事件
        eventStop  = threading.Event()  # 註冊停止錄音事件
        event.startEvent = eventStart
        event.stopEvent = eventStop
        record = threading.Thread(target=Audio_recording)
        record.start()
        event.startEvent.set()
        while(running == 0x01):
            time.sleep(1)
            running = audioConfig.running
    else:
        audioConfig.running = 0xDEAD
        running = audioConfig.running
        event.stopEvent.set()
        while(running == 0xDEAD):
            time.sleep(1)
            running = audioConfig.running
#=========================================================#    

def table_cmd_handler(devNode):
    if(devNode.currentCmd == "power_off"):
        print("Trigger power off")
    elif(devNode.currentCmd == "power_on"):
        print("Trigger power on")
    elif(devNode.currentCmd == "record_off"):
        time.sleep(10)
        print("Trigger record off")        
        audio_record_handler(False)
    elif(devNode.currentCmd == "record_on"):
        print("Trigger record on")
        audio_record_handler(True)
    elif(devNode.currentCmd[0] != ";" and devNode.currentCmd[0].strip() != ""):
        print(devNode.currentCmd[0].strip())
        script_Handler(devNode)
    
def main():
    poolTab = []
    resTab = []     
    finalCheck = []    

    serialModeSelection = 0x01 #getMode()
 
    cpuCount = mp.cpu_count()
    print("CPU count: ",cpuCount )

    #signal.signal(signal.SIGINT, HciSnoopTesterCore.signal_handler)
    
    gDevNode = DEV_NODE(port = COMPORT,
                        tabFile = sys.argv[1],
                        baudRate = BAUD_RATE,
                        serialInfo = 0x00, 
                        loopCount = 0x00, 
                        gRxBuf = "")
                        
    timePofix = time.strftime("%Y%m%d%H%M%S", time.localtime())
    gDevNode.logFileName = COMPORT + "_" + timePofix+".log"
    gDevNode.logFile = open(gDevNode.logFileName, "w")
    
    if(gDevNode.tabFile):
        while(1):
            gDevNode.currentCmd = gDevNode.tabFile.readline().strip()
            if(gDevNode.currentCmd and (gDevNode.currentCmd != "")):
                table_cmd_handler(gDevNode)    
            elif(gDevNode.currentCmd == ""):
                break
    
    gDevNode.logFile.close()    
    exit()
    
if __name__ == "__main__":
    main()   