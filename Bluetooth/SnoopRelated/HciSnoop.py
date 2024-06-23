# https://fte.com/webhelpii/bpa600/Content/Technical_Information/BT_Snoop_File_Format.htm
# https://www.rfc-editor.org/rfc/rfc1761
import math
from datetime import datetime
import DateCode


DIR_H2C = 0
DIR_C2H = 1
TYPE_DATA = 0
TYPE_CMD_EVT = 1

#============ Format part ======================#
def isValidSnoopLog(byteStream):
    #TBD
    return 1

def getFileHeader(logFile):
    return list(logFile.read(0x10))

def getPacketLen(byteStream):
    return (byteStream[4] << 24) + (byteStream[5] << 16) + (byteStream[6] << 8) + (byteStream[7])    
    
def getFrame(logFile):
    readData = list(logFile.read(24))
    #print(readData)
    try:
        recordPacketLen = getPacketLen(readData)
    except:
        return None
    #print(recordPacketLen)
    readData = readData + ( list(logFile.read(recordPacketLen)))
    #print(readData)
    return readData

def getFrameDir(byteStream):
    return byteStream[11] & 0x01
    
def getFrameType(byteStream):
    return (byteStream[11]>>1) & 0x01    

def getTimeStamp(byteStream):
    ret = 0
    for i in range(16,24):
        ret = (ret<<8) + byteStream[i]
    return ret    

#============ ACL related =======================#    
def getAclHandler(byteStream):
    return ((byteStream[25] & 0x0F) << 8) + byteStream[24];   

def is_L2capPacket(byteStream):
    return (getFrameType(byteStream) == TYPE_DATA)     
    
def getEvtHandler(byteStream):

    frameDir = getFrameDir(byteStream)
    frameType = getFrameType(byteStream)
    
    if(frameDir == DIR_C2H and frameType == TYPE_CMD_EVT):
        return ((byteStream[28] & 0x0F) << 8) + byteStream[27];
    else:
        return 0xFF    

def is_NocpEvent(byteStream):
    packetLen = getPacketLen(byteStream)
    frameDir = getFrameDir(byteStream)
    frameType = getFrameType(byteStream)

    #print(byteStream)
    #print(packetLen, frameDir, frameType, byteStream[24])

    if(packetLen != 0x07):
        #print(packetLen)
        return False
    elif(frameDir != DIR_C2H or frameType != TYPE_CMD_EVT):
        return False
    
    evtType = byteStream[24]
    if(evtType == 0x13):
        return True
    else:
        return False        

def getNocpCount(byteStream):
    return ((byteStream[30]<<8) + byteStream[29])

def is_L2capConnReq(byteStream):
    packetLen = getPacketLen(byteStream)
    if(packetLen == (0x0C + 4) and byteStream[32] == 0x02):
        return True;
    else:
        return False;

def is_L2capConnRsp(byteStream):
    packetLen = getPacketLen(byteStream)
    if(packetLen == (0x10 + 4) and byteStream[32] == 0x03):
        return True;
    else:
        return False;
        
        
#============ A2DP related =======================#   
def setAvdtpCid(cid):
    global AvdtpCid;
    AvdtpCid = cid
    #print(cid)

def is_AvdtpMedia(byteStream):  
    global AvdtpCid;
    avdtpMediaCid = (byteStream[31]<<8) + byteStream[30] 
    if(avdtpMediaCid == AvdtpCid):   #Hardcode to test
        return True
    else:
        return False
    
def is_A2dpSrcPacket(byteStream):
    packetLen = getPacketLen(byteStream)
    frameDir = getFrameDir(byteStream)
    #frameType = getFrameType(byteStream)
    
    if(packetLen == 0 or frameDir != DIR_H2C or (is_L2capPacket(byteStream) == False)):
        return False
    
    if(is_AvdtpMedia(byteStream)):
        return True
    else:
        return False      
    
def is_A2dpSnkPacket(byteStream):
    packetLen = getPacketLen(byteStream)
    frameDir = getFrameDir(byteStream)
    frameType = getFrameType(byteStream)
    
    if(packetLen == 0 or frameDir != DIR_C2H or frameType != TYPE_DATA):
        return False
    
    if(is_AvdtpMedia(byteStream)):
        return True
    else:
        return False

def is_PsmAvdtp(byteStream):  
    psm = (byteStream[37]<<8) + byteStream[36]
    if(psm == 0x19):
        return True
    else:
        return False;        

        
def convert_time2timeStr(t):
    t_s = math.floor(t)
    #t_us = math.floor( (t - t_s) * 1000000)
    #        
    #t_s = "{0:#0{1}X}".format(t_s,10)[2:]
    #t_s = t_s[:6] + " " + t_s[6:]  
    #t_s = t_s[:4] + " " + t_s[4:]  
    #t_s = t_s[:2] + " " + t_s[2:]
    #
    #t_us = "{0:#0{1}X}".format(t_us,10)[2:]
    #t_us = t_us[:6] + " " + t_us[6:]  
    #t_us = t_us[:4] + " " + t_us[4:]  
    #t_us = t_us[:2] + " " + t_us[2:]
    t_us = math.floor(t * 1000000)
    t_us = "{0:#0{1}X}".format(t_us,18)[2:]
    t_us = t_us[:14]+ " " + t_us[14:]  
    t_us = t_us[:12]+ " " + t_us[12:]  
    t_us = t_us[:10]+ " " + t_us[10:]
    t_us = t_us[:8] + " " + t_us[8:]  
    t_us = t_us[:6] + " " + t_us[6:]  
    t_us = t_us[:4] + " " + t_us[4:]
    t_us = t_us[:2] + " " + t_us[2:]  

    return t_us

def write_log(data, f):
    f.write(data)
    return

def write_Frame(data, f, t_str):
    #t = time.time()
    #t_us = convert_time2timeStr(t);
    #t_us = "00 60 67 4A B4 3A E0 00"  
    #t_us = "00 E0 3A B4 4A 67 60 00"
    tStamp = DateCode.getTimeStamp(t_str)
    t_us = convert_time2timeStr(tStamp);
    
    length = int((len(data) + 1) / 3)
    hciData = "{0:#0{1}X}".format(length,10)[2:]
    hciData = hciData[:6] + " " + hciData[6:]  
    hciData = hciData[:4] + " " + hciData[4:]  
    hciData = hciData[:2] + " " + hciData[2:]  
    
    if(data[0:2] == "01"):          #command
        #t_us = "00 00 00 00 00 00 00 00"
        #t_us = "00 60 67 4A B4 3A E0 00"  
        hciData = hciData + " " + hciData + " 00 00 00 02" + " 00 00 00 00 " +  " " + t_us + " " + data
    elif(data[0:2] == "02"):    #ACL_TX
        hciData = hciData + " " + hciData + " 00 00 00 01" + " 00 00 00 00 "  + " " + t_us + " " + data
    elif(data[0:2] == "03"):    #ACL_RX
        return  #Add code here
    elif(data[0:2] == "04"):    #event
        #t_us = "00 00 00 00 00 00 00 01"
        hciData = hciData + " " + hciData + " 00 00 00 03" + " 00 00 00 00 "  + " " + t_us + " " + data    
    
    wrData = bytes.fromhex(hciData)
    write_log(wrData, f)
    #time.sleep(0.01)
#    
    
def log_init(f):
    txData = "62 74 73 6E 6F 6F 70 00 00 00 00 01 00 00 03 EA"
    txData = bytes.fromhex(txData)
    write_log(txData, f)