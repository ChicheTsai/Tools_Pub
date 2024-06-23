import math

def convertByteArr2HexString(byteArr):
    ret = ""
    for x in byteArr:
        x = hex(x).replace("0x","").zfill(2)
        ret = ret + " " + x
        
    return ret.strip(" ").upper() 
    
def get_BTsnoop_Header():
    return "62 74 73 6E 6F 6F 70 00 00 00 00 01 00 00 03 EA"

def getSnoopHeader(snoopFile):
    ret = snoopFile.read(16)
    ret = convertByteArr2HexString(ret)    
    return ret

def isSnoopHeaderValid(frameData):
    if(frameData[0:24] == "62 74 73 6E 6F 6F 70 00 "):
        return True
    else:
        return False

def getSnoopPktReleaseLen(data):
    data = data.split()
    ret = (int(data[4],16) << 24) + (int(data[5],16) << 16) + (int(data[6],16) << 8) + (int(data[7],16) << 0)
    return ret

def getFrameDirection(data):    
    data = data.split()
    flag = int(data[11],16)
    
    if(flag & 0x01 == 0x00):
        return 0x00
    else:
        return 0x01

def getFrameType(data):
    data = data.split()
    ret = int(data[24],16)
    
    return ret

def isFrameIsoDataOut(frameData):
    direction = getFrameDirection(frameData)
    frameType = getFrameType(frameData)
    #print(frameData)
    #print(direction, frameType, "\n")
    if(direction == 0x00 and frameType == 0x05):
        return True
    else:
        return False

def isFrameIsoDataIn(frameData):
    direction = getFrameDirection(frameData)
    frameType = getFrameType(frameData)
    #print(frameData)
    #print(direction, frameType, "\n")
    if(direction == 0x01 and frameType == 0x05):
        return True
    else:
        return False

def convertIsoIn2IsoOut(frameData):
    #change direction
    data = frameData.split()
    data[11] = format(int(data[11],16) & 0xFE, '02X')
    #print(data[11], hex(data[11]), 0x10, format(0x10, 'X'))
    #print(data)
    data = ' '.join(data)
    #print(data,"\n")
    return data
    
    
def getProcessedDataFromFrame(trxIdx, frameData):
    direction = getFrameDirection(frameData)
    if(False):
        #frameType = getFrameDirection(frameData)
        
        ret = ""
        #if(dir == 0x00):                #Host -> Controller
        #    if(frameType    == 0x01):   #Command
        #        ret = "TX"+trxIdx+": " 
        #    elif(frameType  == 0x00):    #ACL
        #    elif(frameType  == 0xFF):    #ISO
        #else:                       #Controller -> Host
        #    if(frameType    == 0x01):    #Event
        #    elif(frameType  == 0x00):    #ACL
        #    elif(frameType  == 0xFF):    #ISO

    if(direction == 0x00):
        ret = "TX"+trxIdx+": " + frameData[24*3 : ] + "\t\n"
    else:
        ret = "RX"+trxIdx+": " + frameData[24*3 : ] + "\t\n"

#    print(ret)
    return ret
    
def getFrameSnoop(snoopFile):
    seg1 = snoopFile.read(24)
    if not seg1:
        return ""
    
    seg1 = convertByteArr2HexString(seg1)
    seg2Len = getSnoopPktReleaseLen(seg1)
    #print("seg2Len ",seg2Len)
    seg2 = snoopFile.read(seg2Len)
    seg2 = convertByteArr2HexString(seg2)
    #print(seg1 + "      " + seg2)
    return seg1 + " " + seg2
    
        
def get_BTsnoop_PktHeader(length):
    hciData = "{0:#0{1}X}".format(length,10)[2:]
    hciData = hciData[:6] + " " + hciData[6:]  
    hciData = hciData[:4] + " " + hciData[4:]  
    hciData = hciData[:2] + " " + hciData[2:]
    
    return hciData

def get_BTsnoop_TxPkt(hciData, txData, t_us, conext):
    if(conext == 0x01):     #command
        hciData = hciData + " " + hciData + " 00 00 00 02" + " 00 00 00 00" +  " " + t_us + " " + txData
    elif(conext == 0x02):   #ACL
        hciData = hciData + " " + hciData + " 00 00 00 00" + " 00 00 00 00" +  " " + t_us + " " + txData
    elif(conext == 0x05):   #ISO_ACL
        timeStamp = int(txData[6:8],16) & 0x40
        
        if(timeStamp):
            #isoLen = int(hciData[9:11],16) - 1
            #hciData = hciData[0:9] + hex(isoLen)[2:4] + hciData[11:]
            hciData = hciData + " " + hciData + " 00 00 00 00" + " 00 00 00 00"  + " " + t_us + " " + txData
        else:
            #isoLen = int(hciData[9:11],16) - 1
            #hciData = hciData[0:9] + hex(isoLen)[2:4] + hciData[11:]
            hciData = hciData + " " + hciData + " 00 00 00 00" + " 00 00 00 00"  + " " + t_us + " " + txData
        #print(isoLen, hex(isoLen), timeStamp)
    return hciData

def get_BTsnoop_RxPkt(hciData, rxData, t_us, conext):
    if(conext == 0x04):    #event
        hciData = hciData + " " + hciData + " 00 00 00 03" + " 00 00 00 00"  + " " + t_us + " " + rxData
    elif(conext == 0x02):    #ACL
        hciData = hciData + " " + hciData + " 00 00 00 01" + " 00 00 00 00"  + " " + t_us + " " + rxData
    elif(conext == 0x05):   #ISO_ACL
        hciData = hciData + " " + hciData + " 00 00 00 01" + " 00 00 00 00"  + " " + t_us + " " + rxData
    
    return hciData

        
def write_data_into_hci(data, f):
    #print(data)
    #print("\n")
    data = bytes.fromhex(data)
    f.write(data)
    return

def convert_time2timeStr(t):
    t_s = math.floor(t)
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
    