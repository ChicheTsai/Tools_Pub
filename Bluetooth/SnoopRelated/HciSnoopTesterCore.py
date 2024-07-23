import sys
import serial
import serial.tools.list_ports as port_list
import time
import math
import multiprocessing as mp
import BtSnoop
#import HciSnoopTesterCore
import signal

class DEV_NODE:
    def __init__(self, baudRate, port, serialInfo, f, loopCount, loopCmd, handlerState, gRxBuf):
        self.port = port
        self.baudRate = baudRate
        self.serialInfo = serialInfo
        self.f = f
        self.loopCount = loopCount  
        self.loopCmd = loopCmd 
        self.handlerState = handlerState
        self.gRxBuf = gRxBuf

class LOOP_NODE:
    def __init__(self,  loopCount, loopCmd):
        self.loopCount = loopCount  
        self.loopCmd = loopCmd 

class VAR_NODE:
    def __init__(self):
        self.var = []
        for i in range(0,30):
            self.var.append("")

#====== Global variables =====
gDevNode = {}
gLoopInfo = {}
lineCount   = 0;
gHandlerState = 0x00
gVariable = VAR_NODE()
AutoRx = 0x0

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
                
def get_rxData_from_rxBuffer(port, pollingMode):
    global SIMULATION_DISABLE
    global gDevNode
    
    if(SIMULATION_DISABLE):
        ser = gDevNode[port].serialInfo
        keepRx = False
        timeStamp0 = time.perf_counter() #time.time()
        
        while(1):
            debugStart = time.perf_counter()
#            time.sleep(1/1000) 
            #rx = (ser.read(256*2)).hex()
#            rx = (ser.read(int(256*1.5))).hex()
#            #rx = (ser.read_all()).hex()
#            if(rx != "" or gDevNode[port].gRxBuf != []):
#                #print(rx)
#                #rx = rx.hex()
#                break
            byteInBuffer = ser.in_waiting
#            print(byteInBuffer)
            if(byteInBuffer == 0 and keepRx == True):
                keepRx = True
            elif((byteInBuffer != 0 or gDevNode[port].gRxBuf != [])):
                #print(byteInBuffer)
#                #rx = rx.hex()
                
                #print("TimingDebug: ",debugStart, time.perf_counter(),"\n")
                rx = (ser.read(byteInBuffer)).hex()
                
                rx = rx.upper()
                #print(rx,"\n\n", len(rx))
                for i in range(0, len(rx), 2):
                    gDevNode[port].gRxBuf.append( rx[i:i+2] )
                    
                if(is_dataInRxBufEnough(gDevNode[port].gRxBuf)):
                    keepRx = False
                    break
                else:
                    keepRx = True
                
              
            timeStamp1 = time.perf_counter() #time.time()

            if(pollingMode == 0x01):
                if(timeStamp1 - timeStamp0 > 0.1):
                    return ""
            else:
                if(timeStamp1 - timeStamp0 > 10):
                    return ""
                    
        #while(1):
        #    rx = (ser.read()).hex()
        #    if(rx != ""):
        #        rx = rx.upper()
        #        gRxBuf[port].append(rx)
        #    elif(gRxBuf[port] != []):
        #        break;    
        #print(port,"\t", gRxBuf[port])  
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
                    #print("paraLen0: ",paraLen)
                    #retBuf = ( gDevNode[port].gRxBuf[0:paraLen + 5] )
                    #isoLen = int(hciData[9:11],16) - 1
                    #hciData = hciData[0:9] + hex(isoLen)[2:4] + hciData[11:]
                    #hciData = hciData + " " + hciData + " 00 00 00 00" + " 00 00 00 00"  + " " + t_us + " " + txData
                    #print("Renew")
                else:
                    #paraLen = paraLen + 5
                    retBuf = ( gDevNode[port].gRxBuf[0:paraLen+5] )
                    gDevNode[port].gRxBuf = gDevNode[port].gRxBuf[paraLen+5 : ] 
                    print("paraLen1: ",paraLen)
                
                #print( gDevNode[port].gRxBuf[0:paraLen] )
                    
                #print(isoLen, hex(isoLen), timeStamp)
                
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
#    print("compare_rx_data")
    ret = True
    if(RX_COMPARE_ENABLE):        
#        debugPrint(False, golden)
        golden = str(golden).split(' ')
        rx = " ".join(str(x) for x in rx)
        rx = str(rx).split(' ')
        
        if(len(golden) != len(rx)):
            ret = False
        else:
            for i in range(len(rx)):
                if(rx[i] != golden[i]):
                    if(golden[i] != "??" and golden[i][0] != "R"):
                        ret = False
                        break

        # Update Rn here
        if(ret == True):
            for i in range(len(rx)):
                if(golden[i][0] == "R"):
                    X = int(golden[i][1])
                    gVariable.var[20 + X] = rx[i]
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
            port = "DEV1"
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
        polling_ms = line[8:]
        polling_ms = polling_ms.strip()
        keysInTab = gDevNode.keys()
                
        currentTime = startTime = time.perf_counter()
        pollingInSec = float(polling_ms) / 1000     #Now, it was converted as second
        
        if(pollingInSec >= 60):
            print(time.ctime())
            
        while(currentTime - startTime < pollingInSec):
            for i in keysInTab:
                tempSer = gDevNode[i].serialInfo
                savedTO = tempSer.timeout
                tempSer.timeout = pollingInSec
                readData = get_rxData_from_rxBuffer(i,1)
                if(readData != ""):
                    t_us = BtSnoop.convert_time2timeStr(time.perf_counter());
                    recordingRxData2Snoop(i, readData, t_us)
            
                tempSer.timeout = savedTO
                currentTime = time.perf_counter()
                if(currentTime - startTime >= pollingInSec):
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
                #print(hciData)
                #print(txData)
                #print(length)
            elif(txData[0:2] == "02"):      #ACL
                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, txData, t_us, 0x02)
            elif(txData[0:2] == "05"):      #ISO_ACL
                #print(hciData)
                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, txData, t_us, 0x05)
                #print(hciData)
                #print(txData)
                #print(length)
            else:
                print("scriptLineHandler, Tx ,DEBUG")

            #hciData = bytes.fromhex(hciData)
            #print("ooo ", gDevNode[port].f.tell())
            BtSnoop.write_data_into_hci(hciData, gDevNode[port].f)
                        
        ##ser.write(bytes([0x01,0x03,0x0C,0x00]))
        if(SIMULATION_DISABLE):
            txData = bytes.fromhex(txData)
            #ser = gComPort[port][1]
            ser = gDevNode[port].serialInfo
            ser.write(txData)  #close with simulation
            
        if(AutoRx != 0x00):
            #print("POLLING: " + str(AutoRx))
            scriptLineHandler("POLLING: " + str(AutoRx), devStr)
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
        
        rxByteLen = int(compData[6:8],16)
        
        while(1):
            readData = get_rxData_from_rxBuffer(port, 0x00)
            #print("XXX",(readData))
            if(readData == "" and waitRxFlag == 0x00):
                debugPrint(True, "=========================")
                debugPrint(True, "| Data received Timeout |")
                debugPrint(True, "=========================")
            elif(readData == "" and waitRxFlag):
                continue
            
            
            t = time.perf_counter() #time.time()
            t_us = BtSnoop.convert_time2timeStr(t);
            #print("02: ", t)
            
            readData_ = " ".join(str(x) for x in readData)
            debugPrint(False, str(readData))
            
            recordingRxData2Snoop(port, readData, t_us)
            result = compare_rx_data(readData, compData)
            if(result== True):
                debugPrint(False, "Compare pass")
                if(readData_[0:2] != "05"):
                    debugPrint(TRX_DATA_SHOWING, "RX" + line[idx0+2:idx1] + ": "+ readData_)
                    debugPrint(False, "RX" + line[idx0+2:idx1] + ": "+ readData_)
                else:
                    debugPrint(TRX_DATA_SHOWING, "ISO_DATA_IN")
                
                break;
            elif(waitRxFlag == False):
                debugPrint(True, "Compare Failed.")
                debugPrint(True, "Golden: " + compData)
                print("Rx:     ",readData)
                #debugPrint(True, "Rx:     " + readData)
                close_all_logs()
                exit()
            else:
                debugPrint(False, "Wait for comparing pass")
    elif "PRINT:" == line[0:6]:
        debugPrint(LABEL_SHOWING, line[6:])
#===================================================================================#
    elif "END" == line[0:3]:

        #handlerState = 0xFF
        #close_all_logs()
        #print("============================")
        #print("          Success           ")
        #print("============================")
        
        #gDevNode[port].handlerState = 0xFF
        return 0xFF
        
    
def mainHadler(script, idx, devStr, inPort, inBaudRate, paras):
    global gDevNode, gLoopInfo
    scriptFile  = open(script, 'r')
    scriptFile.seek(idx)
    
    gLoopInfo[0] = LOOP_NODE(loopCount = 0x00, loopCmd = [])
    
    if(SIMULATION_DISABLE):
#        if(devStr != "SERIAL"):
#            gDevNode[devStr] = DEV_NODE(port = inPort, 
#                                     baudRate = inBaudRate,
#                                     serialInfo = 0x00, 
#                                     f = 0x00, 
#                                     loopCount = 0x00, 
#                                     loopCmd = [], 
#                                     handlerState = 0x00, 
#                                     gRxBuf = [])
#
#            #print(gDevNode[devStr])                                     
#            
#            gDevNode[devStr].serialInfo = serial.Serial(gDevNode[devStr].port, gDevNode[devStr].baudRate, timeout= (0.001/inBaudRate))
#            ser = gDevNode[devStr].serialInfo
#            ser.setRTS(True)
#            ser.close()
#            ser.open()
#            ser.setRTS(True)   
#
#            refillParas(paras)
#            
#        else:
#            print("XXX")
        for k in gDevNode.keys():
            gDevNode[k].serialInfo = serial.Serial(gDevNode[k].port, gDevNode[k].baudRate, timeout= (0.001 /gDevNode[k].baudRate))
            ser = gDevNode[k].serialInfo
            ser.setRTS(True)
            ser.close()
            ser.open()
            ser.setRTS(True)
    
    if(HCI_SNOOP_ENABLE):
        timePofix = time.strftime("%Y%m%d%H%M%S", time.localtime())
#        if(devStr != "SERIAL"):
#            newName = script.replace(".txt", "_"+ devStr+ "_" +timePofix + ".cfa")
#            f = open(newName, "wb") 
#            #f = open("hci_" + port + ".log", "wb")
#            #gComPort[dev][2] = f
#            gDevNode[devStr].f = f
#    
#            txData = BtSnoop.get_BTsnoop_Header()
#            BtSnoop.write_data_into_hci(txData, gDevNode[devStr].f)
#        else:
        for k in gDevNode.keys():
            newName = script.replace(".txt", "_"+ k+ "_" + timePofix + ".cfa")
            f = open(newName, "wb") 
            gDevNode[k].f = f
    
            txData = BtSnoop.get_BTsnoop_Header()
            BtSnoop.write_data_into_hci(txData, gDevNode[k].f)
            
    while(True):
        # Get next line from file
        line = scriptFile.readline()
        
        # if line is empty
        # end of file is reached
        if not line:
            break
        
#        lineCount += 1
        line = line.strip()   
        line = line.upper()   
        
        if(isLineFilterIn(line, devStr)):
            #print("mainHadler, ", devStr, line)
            ret = scriptLineHandler(line, devStr)
        
        if(ret == 0xFF):
            return
    #return 'The pool return result: ' + str(num) + str(time.perf_counter())
    return ""       
    
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
    elif (line[0:1] == "Y" or line[0:1] == "Z") and (line[1:2] >= "0" and line[1:2] <= "9"):
        pos = 0
        if (line[0:1] == "Z"):
            pos = 10
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
            #print("TesterInitHandler", dev, gDevNode[dev])
            
#            if(SIMULATION_DISABLE):
#                #gComPort[dev] = [port, serial.Serial(port, baudRate, timeout=0.03), 0]
#                gDevNode[dev].serialInfo = serial.Serial(port, baudRate, timeout=0.03)
#                #ser = gComPort[dev][1]
#                ser = gDevNode[dev].serialInfo
#                #gRxBuf[dev] = []
#                
#                ser.setRTS(True)
#                ser.close()
#                ser.open()
#                ser.setRTS(True)
            #else:
            #    gComPort[dev] = [port, 0, 0]
                
            #if(HCI_SNOOP_ENABLE):
            #    newName = script.replace(".txt", "_"+ port+".cfa")
            #    f = open(newName, "wb") 
            #    #f = open("hci_" + port + ".log", "wb")
            #    #gComPort[dev][2] = f
            #    #gDevNode[dev].f = f
            #    
            #    txData = BtSnoop.get_BTsnoop_Header()
            #    BtSnoop.write_data_into_hci(txData, f)
      
           
    
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
