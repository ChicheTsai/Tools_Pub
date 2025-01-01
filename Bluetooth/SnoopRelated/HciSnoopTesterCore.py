import sys
import serial
import serial.tools.list_ports as port_list
import time
import math
import multiprocessing as mp
import BtSnoop
#import HciSnoopTesterCore
import signal
import threading

class DEV_NODE:
    def __init__(self, baudRate, port, serialInfo, f, loopCount, loopCmd, handlerState, gRxBuf):
        self.port = port
        self.baudRate = baudRate
        self.serialInfo = serialInfo
        self.f = f
        self.loopCount = loopCount  
        self.loopCmd = loopCmd 
        self.handlerState = handlerState
        self.gTxBuf = []
        self.gRxBuf = gRxBuf
        self.gRxData = []
        self.gRxCompBuf = []
        self.gPollingTime = 0
        self.trxState = 0

class LOOP_NODE:
    def __init__(self,  loopCount, loopCmd):
        self.loopCount = loopCount  
        self.loopCmd = loopCmd 

class VAR_NODE:
    def __init__(self):
        self.var = []
        for i in range(0,40):
            self.var.append("")

class THREAD_SET:
    def __init__(self):
        self.scriptFile = ""
        self.startTxEvent = [];
        self.startRxEvent = [];
        self.startRxCheckEvent = [];
#====== Global variables =====
gDevNode = {}
gLoopInfo = {}
lineCount   = 0;
gHandlerState = 0x00
gVariable = VAR_NODE()
AutoRx = 0x0
event = THREAD_SET()

#======= Configurations ======
HCI_SNOOP_ENABLE    = True
SIMULATION_DISABLE  = True
RX_COMPARE_ENABLE   = True
LABEL_SHOWING       = True
TRX_DATA_SHOWING    = True
TOOL_DEBUG          = False

#======= Parameters =======================
def closeSerialPort():
    global gDevNode
    for k in gDevNode.keys():
        ser = gDevNode[k].serialInfo
        ser.close()

def closeSnoopFile():
    global gDevNode
    for k in gDevNode.keys():
        gDevNode[k].f.close()
        

def debugPrint(debugSwitch, output):
    if(debugSwitch == True):
        print(output)

def Get_Parameter(lineStr):
    lineStr = lineStr[2:].replace("=","")
    lineStr = lineStr.replace("0X","")
    lineStr = lineStr.strip()
    return lineStr        

def Parameter_Replace(lineStr):
    global gVariable

    for i in range(0,10):
        X = "Y" + str(i)
        lineStr = lineStr.replace(X, gVariable.var[i])
        X = "Z" + str(i)
        lineStr = lineStr.replace(X, gVariable.var[10 + i])
        X = "R" + str(i)
        lineStr = lineStr.replace(X, gVariable.var[20 + i])
        X = "T" + str(i)
        lineStr = lineStr.replace(X, gVariable.var[30 + i])
    return lineStr    

def close_all_logs():
    if(HCI_SNOOP_ENABLE):
        for k in gDevNode.keys():
            gDevNode[k].f.close()

def is_dataInRxBufEnough(dataBuf):
    #print(dataBuf)
    pktLen = 0xFFFF
    if(int( dataBuf[0],16) == 0x04):
        if(len(dataBuf) >= 3):
            pktLen = int( dataBuf[2],16) + 3
    elif(int( dataBuf[0],16) == 0x02):
        if(len(dataBuf) >= 5):
            pktLen = (int( dataBuf[4],16)<<8)  + int( dataBuf[3],16) + 5
    elif(int( dataBuf[0],16) == 0x05):
        if(len(dataBuf) >= 5):
            pktLen = (int( dataBuf[4],16)<<8)  + int( dataBuf[3],16) + 5

    if(len(dataBuf) >= pktLen):
        return True
    else:
        return False
                
def get_rxData_from_rxBuffer(port):
    global SIMULATION_DISABLE
    global gDevNode
    
    ser = gDevNode[port].serialInfo
    keepRx = False
    timeStamp0 = time.perf_counter() #time.time()
        
    while(1):
        byteInBuffer = ser.in_waiting
        timeStamp1 = time.perf_counter()
        if((byteInBuffer != 0 or gDevNode[port].gRxBuf != [])):
            rx = ((ser.read(byteInBuffer)).hex()).upper()
            for i in range(0, len(rx), 2):
                gDevNode[port].gRxBuf.append( rx[i:i+2] )
                
            if(is_dataInRxBufEnough(gDevNode[port].gRxBuf)):
                timeStamp1 = time.perf_counter()
                break
            
        elif(timeStamp1 > gDevNode[port].gPollingTime):
            return ""
    try:
        #paraLen = int(gRxBuf[port][2],16)
        #retBuf = (gRxBuf[port][0:paraLen + 3])
        #gRxBuf[port] = gRxBuf[port][paraLen + 3 : ]
        
        if(int( gDevNode[port].gRxBuf[0],16) == 0x04):
            paraLen = int( gDevNode[port].gRxBuf[2],16)
            retBuf = ( gDevNode[port].gRxBuf[0:paraLen + 3] )
            gDevNode[port].gRxBuf = gDevNode[port].gRxBuf[paraLen + 3 : ]
        elif(int( gDevNode[port].gRxBuf[0],16) == 0x02):
            paraLen = (int( gDevNode[port].gRxBuf[4],16)<<8)  + int( gDevNode[port].gRxBuf[3],16)
            retBuf = ( gDevNode[port].gRxBuf[0:paraLen + 5] )
            gDevNode[port].gRxBuf = gDevNode[port].gRxBuf[paraLen + 5 : ]   
        elif(int( gDevNode[port].gRxBuf[0],16) == 0x05):
            paraLen = (int( gDevNode[port].gRxBuf[4],16)<<8)  + int( gDevNode[port].gRxBuf[3],16)
            
            #retBuf = ( gDevNode[port].gRxBuf[0:paraLen + 5] )
            #gDevNode[port].gRxBuf = gDevNode[port].gRxBuf[paraLen + 5 : ]                 
            
            timeStamp = int( gDevNode[port].gRxBuf[2],16) & 0x40
    
            if(timeStamp):
                #paraLen = paraLen + 5 + 4
                retBuf = ( gDevNode[port].gRxBuf[0:paraLen +5] )
                gDevNode[port].gRxBuf = gDevNode[port].gRxBuf[paraLen+5 : ] 
                #print("Renew")
            else:
                #paraLen = paraLen + 5
                retBuf = ( gDevNode[port].gRxBuf[0:paraLen+5] )
                gDevNode[port].gRxBuf = gDevNode[port].gRxBuf[paraLen+5 : ] 
                print("paraLen1: ",paraLen)
            
        return retBuf
    except:
        debugPrint(True, "Data received from queue error")
        print(byteInBuffer)
        print(gDevNode[port].gRxBuf)
        print(rx)
        print(len(rx))
        print(gDevNode[port].gRxBuf[0])
        exit()

def compare_rx_data(rx, golden):
    global gVariable;

#    print("compare_rx_data start")
    ret = True
    if(RX_COMPARE_ENABLE):        
        rx = rx.split()
        golden = golden.split()
        if(len(golden) != len(rx)):
            ret = False
        else:
            for i in range(0, len(rx)):
                #print(rx[i], golden[i], rx[i] != golden[i], golden[i][0], golden[i][1])
                if(rx[i] != golden[i]):
                    if(golden[i] != "??" and golden[i][0] != "R"):
                        ret = False
                        break
                    elif(golden[i][0] == "R"):
                        X = int(golden[i][1])
                        gVariable.var[20 + X] = rx[i]

#    print("compare_rx_data end")
    return ret  
    
def recordingRxData2Snoop(port, readData, t_us):
    global gDevNode
    
    readData_ = " ".join(str(x) for x in readData)
    debugPrint(False, str(readData))
            
    if(HCI_SNOOP_ENABLE):
        length = len(readData)
        debugPrint(False, length)
            
        hciData = BtSnoop.get_BTsnoop_PktHeader(length)
                
        if(readData[0] == "04"):        #event
            hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,readData_,t_us,0x04)
        elif(readData[0] == "02"):      #ACL
            hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,readData_,t_us,0x02)
        elif(readData[0] == "05"):      #ISO_Data
            hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,readData_,t_us,0x05)
        else:
            debugPrint(True, "Rx format error")
            print("XXX: ", readData[0:2], hciData)
            exit()    
            
        #hciData = bytes.fromhex(hciData)
        #print("recordingRxData2Snoop", port, gDevNode[port].f )
        BtSnoop.write_data_into_hci(hciData, gDevNode[port].f)
    
def isLineFilterIn(line, devStr):
    #print("isLineFilterIn\t",line, devStr)
    if(devStr == "SERIAL"):
        #print("True. SERIAL")
        return True
    else:
        filterStrTx =  devStr.replace("DEV","TX")
        filterStrRx =  devStr.replace("DEV","RX")
        
        if(("TX" in line) and (filterStrTx not in line)):
            #print("False.\t",filterStrTx, filterStrRx, line)
            return False
        elif(("RX" in line) and (filterStrRx not in line)):
            #print("False.\t",filterStrTx, filterStrRx, line)
            return False
    #print("True.\t",filterStrTx, filterStrRx, line)
    return True

def scriptLineHandler(line, devStr):
    global HCI_SNOOP_ENABLE, SIMULATION_DISABLE, RX_COMPARE_ENABLE, LABEL_SHOWING, TRX_DATA_SHOWING
    global gVariable
    global gDevNode, gLoopInfo
    global gHandlerState
    global AutoRx
    global event
    #global script
    
    ret = 0x00
    
    t = time.perf_counter() #time.time()
    t_us = BtSnoop.convert_time2timeStr(t);
    line = line.strip()
    
    if(devStr == "SERIAL"):
        if(line[0:2] == "TX"):
            port = line[0:3].replace("TX","DEV")
        elif(line[0:2] == "RX"):
            port = line[0:3].replace("RX","DEV")
        elif(line[0:6] == "WAITRX"):
            port = line[0:7].replace("WAITRX","DEV")
        else:
            port = "DEAD_PORT"
    else:
        port = devStr
    #print("scriptLineHandler: ",line, devStr)
    
#===================================================================================#    
    if(line[0:7] == "ENDLOOP"):
        #if(gDevNode[port].handlerState != 0x01):
        if(gHandlerState != 0x01):
        
            debugPrint(True, "\tLoop format error")
            exit()
            
        #gDevNode[port].handlerState = 0x00
        gHandlerState = 0x00
        
        for cnt in range(gLoopInfo[0].loopCount):
            for cmdCnt in range(0, len(gLoopInfo[0].loopCmd)):
                debugPrint(False, "\t" + gLoopInfo[0].loopCmd[cmdCnt] )
                #print("EXE: ",loopCmd[cmdCnt])
                if(devStr == "SERIAL"):
                    scriptLineHandler(gLoopInfo[0].loopCmd[cmdCnt], "SERIAL")
                else:
                    scriptLineHandler(gLoopInfo[0].loopCmd[cmdCnt], port)
        gLoopInfo[0].loopCount = 0;
        gLoopInfo[0].loopCmd = []        
        
        debugPrint(False, "ENDLOOP")

    elif(line[0:5] == "LOOP:"):                     #Start collecting cmds
        #if(gDevNode[port].handlerState != 0x0):
        if(gHandlerState != 0x0):
            debugPrint(True, "\tLoop format error")
            exit()
        
        gHandlerState = 0x01
        #debugPrint(False,str(gDevNode[port].loopCount))
        gLoopInfo[0].loopCmd = []
        gLoopInfo[0].loopCount = int(line[5:].strip())
#===================================================================================#
    elif(gHandlerState == 0x01):      #collecting cmds
        debugPrint(False, "\t" + line)
        gLoopInfo[0].loopCmd.append(line)
#===================================================================================#
    elif(line[0:8] == "WAIT_MS:"):
        delay_ms = line[8:]
        delay_ms = delay_ms.strip()
        debugPrint(True, "Delay "+ str(delay_ms) +"ms")
        
        currentTime = startTime = time.perf_counter()
        delayInSec = float(delay_ms) / 1000
        while(currentTime - startTime < delayInSec):
            currentTime = time.perf_counter()
#===================================================================================#
    elif("POLLING:" in line[0:8]):
        #gPollingTime
        polling_ms = line[8:]
        polling_ms = polling_ms.strip()
        #keysInTab = gDevNode.keys()
                
        currentTime = startTime = time.perf_counter()
        pollingInSec = float(polling_ms) / 1000     #Now, it was converted as second
        
        
        if(pollingInSec >= 60):
            debugPrint(True, "Polling "+ str(pollingInSec) +"ms")
            debugPrint(True, "\tstartTime "+ str(startTime) +"ms")

        for k in gDevNode.keys():
            gDevNode[k].trxState = gDevNode[k].trxState | 0x04
            gDevNode[k].gRxCompBuf = []
            gDevNode[k].gPollingTime = pollingInSec + startTime            
            event.startRxEvent.set()
        
            while True:
                if((gDevNode[k].trxState & 0x04) == 0x00):
                    break

       #print(currentTime, startTime)
#===================================================================================#   
    elif "TX" == line[0:2]:
        line = Parameter_Replace(line)
        if(line[5:7] != "05"):
            debugPrint(TRX_DATA_SHOWING, line)
        else:
            debugPrint(TRX_DATA_SHOWING, "ISO_DATA_OUT")
        
        #if(devStr == "SERIAL"):
        #    port = line[0:3].replace("TX","DEV")
            
        txData = line[4:len(line)+1].strip()
        
        if(HCI_SNOOP_ENABLE):
            length = int((len(txData) + 1) / 3)
            hciData = BtSnoop.get_BTsnoop_PktHeader(length)
            
            if(txData[0:2] == "01"):        #command
                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, txData, t_us, 0x01)
            elif(txData[0:2] == "02"):      #ACL
                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, txData, t_us, 0x02)
            elif(txData[0:2] == "05"):      #ISO_ACL
                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, txData, t_us, 0x05)
            else:
                print("scriptLineHandler, Tx ,DEBUG")
            BtSnoop.write_data_into_hci(hciData, gDevNode[port].f)
        
        gDevNode[port].gTxBuf.append(txData)
        gDevNode[port].trxState = gDevNode[port].trxState | 0x01
        event.startTxEvent.set()
        while True:
            if((gDevNode[port].trxState & 0x01) == 0x00):
                break
            
#        if(AutoRx != 0x00):
#            #print("POLLING: " + str(AutoRx))
#            scriptLineHandler("POLLING: " + str(AutoRx), devStr)
#===================================================================================#            
    elif "RX" == line[0:2] or "WAITRX" == line[0:6]:
        idx0 = line.find("RX")
        idx1 = line.find(":")
        waitRxFlag = ((line.find("WAITRX")) != -1)

        #if(devStr == "SERIAL"):
        #    port = "DEV" + line[idx0+2:idx1]   
        #print(devStr, port)
        compData = line[idx1+1:len(line) + 1].strip()
        compData = compData.strip()
        #print("compData ", compData)
        
        rxByteLen = int(compData[6:8],16)

        idx2 = line.find("_")
        #print("idx2", idx2) #DEBUG
        if(idx2 != -1):
            polling_ms = line[idx2 + 1: idx1]
            polling_ms = polling_ms.strip()
            startTime = time.perf_counter()
            pollingInSec = float(polling_ms) / 1000     #Now, it was converted as second
            gDevNode[port].trxState = gDevNode[port].trxState | 0x02 | 0x04
        else:
            startTime = 0
            pollingInSec = 0
            
            if(waitRxFlag):
                gDevNode[port].trxState = gDevNode[port].trxState | 0x02 | 0x04
            else:
                gDevNode[port].trxState = gDevNode[port].trxState | 0x02
        
        gDevNode[port].gRxCompBuf = compData
        event.startRxEvent.set()
        while True:
            if((gDevNode[port].trxState & 0x06) == 0x00):
                break
            elif(gDevNode[port].trxState & 0x80):
                break

    elif "SET_INCREASE:" == line[0:13]:
        parIdxStart = line.find("(")
        parIdxStop = line.find(")")
        valIdxStart = line[parIdxStart+1:].find("(") + parIdxStart + 1
        valIdxStop = line[parIdxStop+1:].find(")") + parIdxStop + 1
        str1 = line[parIdxStart+1 : parIdxStop]
        str2 = line[valIdxStart+1 : valIdxStop]

        breakFlag = False
        c = 0
        while True:
            idx_1 = str1.find(",")
            idx_2 = str2.find(",")
            if(idx_1 != -1):
                para = str1[:idx_1].strip()
                str1 = str1[idx_1+1:]
            else:
                para = str1.strip()

            if(idx_2 != -1):
                val = str2[:idx_2].strip()
                str2 = str2[idx_2+1:]
                
                #print(para, val )
            else:
                val = str2.strip()
                #print(para, val )
                breakFlag = True
            
            if(para[0] == "Y"):
                pos = 0
            elif(para[0] == "Z"):
                pos = 10   
            elif(para[0] == "R"):
                pos = 20
            elif(para[0] == "T"):
                pos = 30
            
            pos += (int(para[1],16))
            val = int(gVariable.var[pos],16) + int(val,16)

            if(val >= 0x100):
                c = 1
                val -= 0x100
            else:
                c = 0
            #print(pos, val, hex(val)[2:])
            gVariable.var[pos] = hex(val)[2:].upper().zfill(2)

            if(breakFlag):
                break
        

    elif "PRINT:" == line[0:6]:
        debugPrint(LABEL_SHOWING, line[6:].strip())
#===================================================================================#
    elif "END" == line[0:3]:        
        for k in gDevNode.keys():
            while True:
                if((gDevNode[k].trxState & 0x0F) == 0x00):
                    gDevNode[k].trxState |= 0x80
                    break    
                    
        print(gVariable.var[30:40])
        return 0xDEAD

#================ Functions for Threads =========================#
def UART_StartTx():
    global event, gDevNode
    
    while True:
        event.startTxEvent.wait()             
        event.startTxEvent.clear()
        
        for k in gDevNode.keys():
            while (gDevNode[k].gTxBuf != []):
                txData = bytes.fromhex(gDevNode[k].gTxBuf[0])
                gDevNode[k].gTxBuf.pop(0)
                ser = gDevNode[k].serialInfo
                ser.write(txData)
        
            gDevNode[k].trxState = gDevNode[k].trxState & ~(0x01)

def UART_StartRx():
    global event, gDevNode
    while True:
        event.startRxEvent.wait()             
        event.startRxEvent.clear()

        for k in gDevNode.keys():
            port = k

            #print("UART_StartRx: ",gDevNode[port].trxState)
            startTime = time.perf_counter()
            while(1):
                readData = get_rxData_from_rxBuffer(port)
                currentTime = time.perf_counter()
                
                #print(gDevNode[port].gPollingTime, currentTime)
                if(gDevNode[port].trxState & 0x04):
                    if(readData == ""):                    
                        if(currentTime < gDevNode[port].gPollingTime):
                            continue
                        else:
                            gDevNode[port].trxState &= ~(0x04)
                            break
                    else:
                        break
                elif(gDevNode[port].trxState & 0x02):
                    if(readData == ""):
                        if(currentTime - startTime > 5):
                            break
                        else:
                            continue
                    break
                    
            t = time.perf_counter() #time.time()
            t_us = BtSnoop.convert_time2timeStr(t);
                
            #readData_ = " ".join(str(x) for x in readData)
            
            if(readData != ""):
                recordingRxData2Snoop(port, readData, t_us)
                gDevNode[port].gRxData = readData
                event.startRxCheckEvent.set()            

def UART_RxCompare():    
    global event, gDevNode
    while True:
        event.startRxCheckEvent.wait()             
        event.startRxCheckEvent.clear()
        
        for k in gDevNode.keys():
            port = k
            #print("UART_RxCompare Start", gDevNode[port].trxState)
            
            readData_ = " ".join(str(x) for x in gDevNode[port].gRxData)
            
            if(gDevNode[port].trxState & 0x02):
                result = compare_rx_data(readData_, gDevNode[port].gRxCompBuf)
            else:
                result = False
            
            #print(result, gDevNode[port].trxState)
            portIdx = port.replace("DEV","")
            if(result == True):
                gDevNode[port].trxState &= ~(0x02 | 0x04)
                debugPrint(True, "RX" + portIdx + ": " + readData_)
            elif(gDevNode[port].trxState & 0x04 ):  #keep receving
                debugPrint(True, "RX" + portIdx + ": " + readData_)
                
                if(gDevNode[port].trxState & 0x02):
                    event.startRxEvent.set()
                else:
                    currentTime = time.perf_counter()
                    if(currentTime < gDevNode[port].gPollingTime):
                        event.startRxEvent.set()
                    else:
                        gDevNode[port].trxState &= ~(0x04)
                
            elif(gDevNode[port].trxState & 0x02 ):  #keep receving
                gDevNode[port].trxState &= ~(0x02)
                gDevNode[port].trxState |= 0x80
                debugPrint(True, "!!!!! COMPARE FAILED !!!!!")
                debugPrint(True, "Golden: " + gDevNode[port].gRxCompBuf)
                debugPrint(True, "Rx    : " + readData_)
            
            
def mainThread_Fn():      
    global event

    while(True):
        # Get next line from file
        line = event.scriptFile.readline()
        
        # if line is empty
        # end of file is reached
        if not line:
            break
        
#        lineCount += 1
        line = line.strip()   
        line = line.upper()   
        
        #if(isLineFilterIn(line, devStr)):
        #    #print("mainHadler, ", devStr, line)
        ret = scriptLineHandler(line, "SERIAL")
        
        if(ret == 0xDEAD):
            return
    
    
def mainHadler(script, idx, devStr, inPort, inBaudRate, paras):
    global gDevNode, gLoopInfo, event
    event.scriptFile  = open(script, 'r')
    event.scriptFile.seek(idx)
    
    gLoopInfo[0] = LOOP_NODE(loopCount = 0x00, loopCmd = [])
    timePofix = time.strftime("%Y%m%d%H%M%S", time.localtime())
    
    for k in gDevNode.keys():
        gDevNode[k].serialInfo = serial.Serial(gDevNode[k].port, gDevNode[k].baudRate, timeout= (0.001 /gDevNode[k].baudRate))
        ser = gDevNode[k].serialInfo
        ser.setRTS(True)
        ser.close()
        ser.open()
        ser.setRTS(True)
    
        if(HCI_SNOOP_ENABLE):
            newName = script.replace(".txt", "_"+ k+ "_" + timePofix + ".cfa")
            f = open(newName, "wb") 
            gDevNode[k].f = f
    
            txData = BtSnoop.get_BTsnoop_Header()
            BtSnoop.write_data_into_hci(txData, gDevNode[k].f)
    
        gDevNode[k].trxState = 0x00
        event.startTxEvent = threading.Event()
        event.startRxEvent = threading.Event()
        event.startRxCheckEvent = threading.Event()
        
        mainThread  = threading.Thread(target=mainThread_Fn)
        mainThread.start()
        uartStartTx = threading.Thread(target=UART_StartTx)
        uartStartTx.start()
        uartStartRx = threading.Thread(target=UART_StartRx)
        uartStartRx.start()
        uartRxCompare = threading.Thread(target=UART_RxCompare)
        uartRxCompare.start()
        while True:
            if(gDevNode[k].trxState & 0x80):
                break     
    
def TesterInitHandler(script, line):
    global HCI_SNOOP_ENABLE, SIMULATION_DISABLE
    global gVariable
    global AutoRx
    global gDevNode
    
    if( TOOL_DEBUG ):
        print("TestHadler0: ", line) 
        return
    
##===================================================================================#
    if line[0:8] == "AUTO_RX:":
        line = line[8:].replace("=","")
        AutoRx = int(line.strip())
        if(AutoRx == 0):
            print("AutoRx is disabled")
        else:    
            print("AutoRx ", AutoRx, "ms")
    elif (line[0:1] == "Y" or line[0:1] == "Z" or line[0:1] == "T") and (line[1:2] >= "0" and line[1:2] <= "9"):
        pos = 0
        if (line[0:1] == "Z"):
            pos = 10
        elif (line[0:1] == "T"):
            pos = 30
        pos = pos + (ord(line[1:2]) - ord("0"))
        gVariable.var[pos] = Get_Parameter(line)
#===================================================================================#
    elif(line[0:3] == "DEV"): #"DEV" in line:
        if "COM" in line:
            tab = line.split()
            
            dev = tab[0][0:len(tab[0])-1]
            port = tab[1]   #line[idx:idx + len(line) + 1]
            baudRate = int(tab[2])
            
            debugPrint(True, dev)
            debugPrint(True, port)
            
            gDevNode[dev] = DEV_NODE(port = port, 
                                     baudRate = baudRate,
                                     serialInfo = 0x00, 
                                     f = 0x00, 
                                     loopCount = 0x00, 
                                     loopCmd = [], 
                                     handlerState = 0x00, 
                                     gRxBuf = [])
             
def TesterInit(script, scriptFile):
    localState = 0x00
    ret = [0]
    while True:
        # Get next line from file
        line = scriptFile.readline()
        
        # if line is empty
        # end of file is reached
        if not line:
            break
        
        line = line.strip()   
        line = line.upper()   
        
        if(line == ""):
            continue
        elif(localState == 0x00):
            if(line[0] == "{" or 
               (line.encode("utf-8") == b'\xe5\x9a\x9c\xe7\xaf\xa6')):      #Due to the format of MS's text file, I need to make a work-around here
                localState = 0x01
            elif(line[0] == "}"):
                print("Scipt format error. It may be caused by the txt format problem")
                exit()
            
        elif(line[0] == "}" and localState == 0x01):
            break
        elif(localState == 0x01):
            if(line[0:3] == "DEV"):
                ret[0] = ret[0] +1
                ret.append(line[0:4])
            TesterInitHandler(script, line)
            #scriptLineHandler(line)
    return ret
