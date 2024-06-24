# https://fte.com/webhelpii/bpa600/Content/Technical_Information/BT_Snoop_File_Format.htm
import sys
import csv
import BtSnoop

class InfoSubHead():
    def __init__(self, fileName, direction, csvFile):
        self.fileName = fileName
        self.direction = direction
        self.csvFile = csvFile
        self.data = []
        self.rdIdx = 0
        self.headIdx = 0;
        self.readFlag = False;
        self.pktIdx = 0
        self.pktLen = 0

    def getTopIdx(self):
        if(self.direction == 0x01):
            for i in range(0, len(self.data[0])):
                if(self.data[0][i + 0][1] != "0x04"):
                    continue;
                if(self.data[0][i + 1][1] != "0x0E"):
                    continue;                       
                if(self.data[0][i + 2][1] != "0x04"):
                    continue;                
                if(self.data[0][i + 3][1] != "0x01"):
                    continue;                                   
                if(self.data[0][i + 4][1] != "0x03"):
                    continue;                
                if(self.data[0][i + 5][1] != "0x0C"):
                    continue;                                 
                if(self.data[0][i + 6][1] != "0x00"):
                    continue;
                self.headIdx = i;
                self.rdIdx = i

    def get_snoop_pkt_Index_from_LA_data(self):
        if(self.readFlag == True):
            #print("???")
            return
        else:
            #print("xxx: ", self.rdIdx, len(self.data[0]))
            if(self.rdIdx >= len(self.data[0])):
                self.readFlag = False
                return
            elif(self.data[0][self.rdIdx][1] == "0x01"): #HCI command
                self.pktLen = int(self.data[0][self.rdIdx + 3][1],16) +4
            elif(self.data[0][self.rdIdx][1] == "0x02"):
                self.pktLen = (int(self.data[0][self.rdIdx + 4][1],16) << 8) + (int(self.data[0][self.rdIdx + 3][1],16)) + 5 
            elif(self.data[0][self.rdIdx][1] == "0x04"): #HCI event
                self.pktLen = (int(self.data[0][self.rdIdx + 2][1],16)) + 3
            elif(self.data[0][self.rdIdx][1] == "0x05"): #ISO Event
                tbFlag = ((int(self.data[0][self.rdIdx + 2][1],16)) >> 2) & 0x01
                self.pktLen = (int(self.data[0][self.rdIdx + 4][1],16)) & 0x7F
                self.pktLen = (self.pktLen << 8) + (int(self.data[0][self.rdIdx + 3][1],16))
                if(tbFlag):
                    self.pktLen = self.pktLen + 4
                self.pktLen = self.pktLen + 5
#                print(self.rdIdx, self.pktLen, tbFlag)
            else:
                print("Error", self.rdIdx)               
                exit()
                
            self.pktIdx = self.rdIdx
            self.rdIdx = self.rdIdx + self.pktLen
            self.readFlag = True
            #print(self.pktLen)
 
class InfoHead():
    def __init__(self, fileName, h2cNode = None, c2hNode = None):
        self.fileName = fileName
        self.h2cNode = h2cNode
        self.c2hNode = c2hNode
        self.flag = 0x00
        self.Tbase = 0xFFFFFFFF
        self.f = None

    def snoopInit(self):
        self.f = open(self.fileName, "wb") 
        txData = BtSnoop.get_BTsnoop_Header()
        BtSnoop.write_data_into_hci(txData, self.f)
    
    def close(self):
        self.f.close()
        if(self.h2cNode != None):
            self.h2cNode.csvFile.close()
        if(self.c2hNode != None):
            self.c2hNode.csvFile.close()
    
    def get_base_time(self):
        if(self.h2cNode != None):
            t = float(self.h2cNode.data[0][self.h2cNode.headIdx][0])
            if(t <= self.Tbase ):
                self.Tbase = t
            #print(self.h2cNode.data[0][self.h2cNode.headIdx][0])
        if(self.c2hNode != None):
            #print(self.h2cNode.data[0][self.c2hNode.headIdx][0])
            t = float(self.c2hNode.data[0][self.c2hNode.headIdx][0])
            if(t <= self.Tbase ):
                self.Tbase = t

    def getTopIndx(self, data):
        for i in range(0, len(data) - 6):
            if(data[i + 0][1] == "0x04"):
                if(data[i + 1][1] == "0x0E" and 
                data[i + 2][1] == "0x04" and 
                data[i + 3][1] == "0x01" and  
                data[i + 4][1] == "0x03" and
                data[i + 5][1] == "0x0C" and
                data[i + 6][1] == "0x00"):
                    return 1, i, i + 7 + 1
            elif(data[i + 0][1] == "0x01"):
                if(data[i + 1][1] == "0x03" and 
                data[i + 2][1] == "0x0C" and 
                data[i + 3][1] == "0x00"):
                    return 0, i, i + 4 + 1
        return 0xFF,0,0

    def getInitInfo(self, fileName):
        csvFile = open(fileName)
        data = list(csv.reader(csvFile))
        x,y,z = self.getTopIndx(data)
        if(x == 0xFF):
            print("File format error")
            print(fileName)
            csvFile.close()
            exit()
        elif((self.flag & (1<<x) == 0x0)):
            self.flag = self.flag | (1<<x)
            node = InfoSubHead(fileName, x, csvFile)
            node.data.append(data)
            node.headIdx = y;
            node.rdIdx = y        
            if(x == 0x0):
                self.h2cNode = node
            else:
                self.c2hNode = node
        else:
            print("Direction repeated")
            print(fileName)
            csvFile.close()
            exit()

    def selectAndConvertIntoSnoop(self):
        result = True
        ret = ""
        processState = 0xFF
        
        if(self.h2cNode != None and self.c2hNode != None):
#            print(self.h2cNode.readFlag, self.c2hNode.readFlag, )
            if(self.h2cNode.readFlag == True and self.c2hNode.readFlag == True):
#                print(self.h2cNode.pktIdx, len(self.h2cNode.data[0]))
#                print(self.c2hNode.pktIdx, len(self.c2hNode.data[0]))
                t_c2h = float(self.c2hNode.data[0][self.c2hNode.pktIdx][0])                            
                t_h2c = float(self.h2cNode.data[0][self.h2cNode.pktIdx][0])
                #print(t_h2c, t_c2h)
                if(t_h2c < t_c2h):
                    processState = 0x00
                else:
                    processState = 0x01
            elif(self.h2cNode.readFlag == True):
                processState = 0x00
            elif(self.c2hNode.readFlag == True):
                processState = 0x01
            else:
                result = False
        elif(self.h2cNode != None and self.c2hNode == None):
            if(self.h2cNode.readFlag == True ):
                processState = 0x00
            else:
                result = False
        elif(self.h2cNode == None and self.c2hNode != None):
            if(self.c2hNode.readFlag == True ):   
                processState = 0x01
            else:
                result = False
        else:
            result = False
        
        if(result != False):
            if(processState == 0x00):
                for i in range(0, self.h2cNode.pktLen):
                    readData = (self.h2cNode.data[0][self.h2cNode.pktIdx + i][1]).replace("0x","")
                    ret = ret + readData + " "
                t_us = BtSnoop.convert_time2timeStr(float(self.h2cNode.data[0][self.h2cNode.pktIdx][0]) - self.Tbase)  
                self.h2cNode.readFlag = False
#                print("Test04", self.h2cNode.pktLen)
            elif(processState == 0x01):
                for i in range(0, self.c2hNode.pktLen):
                    readData = (self.c2hNode.data[0][self.c2hNode.pktIdx + i][1]).replace("0x","")
                    ret = ret + readData + " "
                t_us = BtSnoop.convert_time2timeStr(float(self.c2hNode.data[0][self.c2hNode.pktIdx][0]) - self.Tbase)
                self.c2hNode.readFlag = False
            
#            print(ret, "\n")    #CHICHE debug data
            writeData = ret.strip()
            length = int((len(writeData) + 1) / 3)
            hciData = BtSnoop.get_BTsnoop_PktHeader(length)
            if(processState == 0x00):
                if(writeData[0:2] == "01"):    #command
                    hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x01)
                elif(writeData[0:2] == "02"):    #ACL
                    hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x02)
                elif(writeData[0:2] == "05"):    #ISO_ACL
#                    print("Test 01")
#                    exit()
                    hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x05)
            elif(processState == 0x01):
                if(writeData[0:2] == "04"):        #event
                    hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x04)
                elif(writeData[0:2] == "02"):      #ACL
                    hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x02)
                elif(writeData[0:2] == "05"):      #ISO_Data
#                    print("Test 02")
                    hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x05)
            
            BtSnoop.write_data_into_hci(hciData, self.f)

        return result
    
 
def main():
    n = len(sys.argv) - 2
    infoHead = InfoHead(sys.argv[1])
    infoHead.getInitInfo(sys.argv[2])
    
    if(n == 2):
        infoHead.getInitInfo(sys.argv[3])
            
    if(infoHead.c2hNode == None and infoHead.h2cNode == None):
        exit()

    if(infoHead.h2cNode != None):
        print(infoHead.h2cNode.fileName, infoHead.h2cNode.direction, infoHead.h2cNode.headIdx, infoHead.h2cNode.rdIdx)
    if(infoHead.c2hNode != None):
        print(infoHead.c2hNode.fileName, infoHead.c2hNode.direction, infoHead.c2hNode.headIdx, infoHead.c2hNode.rdIdx)

    infoHead.get_base_time()
    infoHead.snoopInit()
    
    count = 0
    while(True):
        if(infoHead.h2cNode != None):
            infoHead.h2cNode.get_snoop_pkt_Index_from_LA_data()
 
        if(infoHead.c2hNode != None):
            infoHead.c2hNode.get_snoop_pkt_Index_from_LA_data()
        
        if(infoHead.selectAndConvertIntoSnoop() == False):
            break
    
    infoHead.close()
    
if __name__ == "__main__":
    main()   