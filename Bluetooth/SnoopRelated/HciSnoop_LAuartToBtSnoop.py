# https://fte.com/webhelpii/bpa600/Content/Technical_Information/BT_Snoop_File_Format.htm
import sys
import csv
import BtSnoop

######  def get_snoop_pkt_idx_from_LA_data(info):
######      data = info[5]
######      readIdx = info[3]
######      
######      #print(readIdx, len(data))
######      if(readIdx == len(data)):
######          info[1] = 0x02
######          info[2] = 0xFFFFFFFF
######          info[4] = -1
######          return info
######      elif(readIdx > len(data)):
######          print("DEBUG, get_snoop_pkt_idx_from_LA_data")
######          exit()
######      
######      T = data[readIdx][0]
######      T = float(T)
######      readData = data[readIdx][1]
######      pktLen = -1
######      
######      if(readData == "0x01"): #HCI command
######          pktLen = int(data[readIdx + 3][1],16) +4
######      elif(readData == "0x02" or readData == "0x02"): #ACL data
######          pktLen = (int(data[readIdx + 4][1],16)<<8) + (int(data[readIdx + 3][1],16)) +5
######      elif(readData == "0x04"): #HCI event
######          pktLen = int(data[readIdx + 2][1],16) +3
######      
######  #    elif(readData == "0x05"): #ISO data
######      
######      info[1] = True
######      info[2] = T
######      info[4] = pktLen
######      #print(pktLen)
######      return info
######  
######  def get_snoop_pkt_data_from_LA_data(info):
######      ret = ""
######      for i in range(0,info[4]):
######          readData = (info[5][info[3]+i][1]).replace("0x","")
######          ret = ret + readData + " "
######          #print(info[5][info[3]+i][1])
######      return ret
######  
######  def get_base_time(readInfo, n):
######      minT = 0xFFFFFFFF
######  
######      for i in range(0,n):
######          t = float(readInfo[i][5][1][0])
######          if(t < minT):
######              minT = t
######      return minT
######   
######  def get_earlist_packet_idx(readInfo):
######      minT = 0xFFFFFFFF
######      minIdx = 0
######      
######      for i in range(0,len(readInfo)):
######          idx = readInfo[i][3]
######          t = readInfo[i][2] #float(readInfo[i][5][idx][0])
######          
######          #print(idx,t, readInfo[i][2])
######          if(t < minT):
######              minT = t
######              minIdx = i
######      #print(minIdx)
######      return minIdx

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
            return
        else:
            if(self.data[0][self.rdIdx][1] == "0x01"): #HCI command
                self.pktLen = int(self.data[0][self.rdIdx + 3][1],16) +4
            elif(self.data[0][self.rdIdx][1] == "0x02"): #HCI command
                self.pktLen = (int(self.data[0][self.rdIdx + 4][1],16) << 8) + (int(self.data[0][self.rdIdx + 3][1],16)) + 5 
            elif(self.data[0][self.rdIdx][1] == "0x04"): #HCI event
                self.pktLen = (int(self.data[0][self.rdIdx + 2][1],16)) + 3
            elif(self.data[0][self.rdIdx][1] == "0x05"): #ISO Event
                self.pktLen = (int(self.data[0][self.rdIdx + 2][1],16)) + 3 ## CHICHE DEBUG HERE
                
            self.pktIdx = self.rdIdx
            self.rdIdx = self.rdIdx = self.rdIdx = self.rdIdx + self.pktLen
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
            if(self.h2cNode.readFlag == True and self.c2hNode.readFlag == True):
                t_h2c = float(self.h2cNode.data[0][self.h2cNode.rdIdx][0])
                t_c2h = float(self.c2hNode.data[0][self.c2hNode.rdIdx][0])            
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
                    readData = (self.h2cNode.data[0][self.h2cNode.rdIdx + i][1]).replace("0x","")
                    ret = ret + readData + " "
                t_us = BtSnoop.convert_time2timeStr(float(self.h2cNode.data[0][self.h2cNode.rdIdx][0]) - self.Tbase)  
                self.h2cNode.readFlag = False
            elif(processState == 0x01):
                for i in range(0, self.c2hNode.pktLen):
                    readData = (self.c2hNode.data[0][self.c2hNode.rdIdx + i][1]).replace("0x","")
                    ret = ret + readData + " "
                t_us = BtSnoop.convert_time2timeStr(float(self.c2hNode.data[0][self.c2hNode.rdIdx][0]) - self.Tbase)
                self.c2hNode.readFlag = False
            
            print(ret, "\n")
            writeData = ret.strip()
            length = int((len(writeData) + 1) / 3)
            hciData = BtSnoop.get_BTsnoop_PktHeader(length)
            if(processState == 0x00):
                if(writeData[0:2] == "01"):    #command
                    hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x01)
                elif(writeData[0:2] == "02"):    #ACL
                    hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x02)
                elif(writeData[0:2] == "05"):    #ISO_ACL
                    hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x05)
            elif(processState == 0x00):
                if(writeData[0:2] == "04"):        #event
                    hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x04)
                elif(writeData[0:2] == "02"):      #ACL
                    hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x02)
                elif(writeData[0:2] == "05"):      #ISO_Data
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
        count += 1
        if(count >= 10):
            break
       
        
    
 
 #   while(True):
 #       endLoopCount = 0x0
 #       for i in range(0,n):
 #           if(readInfo[i][1] == 0x00):
 #               readInfo[i] = get_snoop_pkt_idx_from_LA_data(readInfo[i])   #Check
 #           
 #           if(readInfo[i][1] == 0x02):
 #               endLoopCount = endLoopCount +1
 #       
 #       if(endLoopCount == n):
 #           break;
 #
 #       minTidx = get_earlist_packet_idx(readInfo)
 #       
 #       #record packet to snoop()        
 #       writeData = get_snoop_pkt_data_from_LA_data(readInfo[minTidx]).strip()
 #       t_us = BtSnoop.convert_time2timeStr(readInfo[minTidx][2] - Tbase) #readInfo[minTidx][2]
 #       print(readInfo[minTidx][2] - Tbase, "\t\t", writeData)
 #       
 #       length = int((len(writeData) + 1) / 3)
 #       hciData = BtSnoop.get_BTsnoop_PktHeader(length)
 #       
 #       if(minTidx == 0): #Host -> controller
 #           if(writeData[0:2] == "01"):    #command
 #               hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x01)
 #           elif(writeData[0:2] == "02"):    #ACL
 #               hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x02)
 #           elif(writeData[0:2] == "05"):    #ISO_ACL
 #               hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x05)
 #           else:
 #               print("DEBUG")
 #       else:
 #           #length = len(readData)
 #           #hciData = BtSnoop.get_BTsnoop_PktHeader(length)
 #               
 #           if(writeData[0:2] == "04"):        #event
 #               hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x04)
 #           elif(writeData[0:2] == "02"):      #ACL
 #               hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x02)
 #           elif(writeData[0:2] == "05"):      #ISO_Data
 #               hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x05)
 #           else:
 #               print("Rx format error")
 #               #print("XXX: ", readData[0:2], hciData)
 #               exit()    
 #           
 #       BtSnoop.write_data_into_hci(hciData, f)
 #      
 #       readInfo[minTidx][1] = False
 #       readInfo[minTidx][2] = 999999
 #       readInfo[minTidx][3] = readInfo[minTidx][3] + readInfo[minTidx][4]
 #       #exit()
 #   
 #   f.close()


#    infoH2C = InfoHead().init()
#    infoH2C.fileName = sys.argv[0 + 2]
#    infoH2C.direction = 0x00    #Host to controller
#    print(infoH2C.direction, infoH2C.fileName)
#    readInfo = []
#    n = len(sys.argv) - 2
#    #FileName / Read flag / T / index / len / data
#    #skip first row
#    for i in range(0,n):
#        temp = [sys.argv[i+2],0,0,1,0]
#        
#        with open(sys.argv[i+2]) as f:
#            csv_data = [row for row in csv.reader(f)]
#            temp.append(csv_data)
#            f.close()
#        readInfo.append(temp)
#    Tbase = get_base_time(readInfo,n)
#    
#    f = open(sys.argv[1], "wb") 
#    txData = BtSnoop.get_BTsnoop_Header()
#    BtSnoop.write_data_into_hci(txData, f)
#
#    #Find the first time    
#    #Kingst format
#    
#    while(True):
#        endLoopCount = 0x0
#        for i in range(0,n):
#            if(readInfo[i][1] == 0x00):
#                readInfo[i] = get_snoop_pkt_idx_from_LA_data(readInfo[i])   #Check
#            
#            if(readInfo[i][1] == 0x02):
#                endLoopCount = endLoopCount +1
#        
#        if(endLoopCount == n):
#            break;
#
#        minTidx = get_earlist_packet_idx(readInfo)
#        
#        #record packet to snoop()        
#        writeData = get_snoop_pkt_data_from_LA_data(readInfo[minTidx]).strip()
#        t_us = BtSnoop.convert_time2timeStr(readInfo[minTidx][2] - Tbase) #readInfo[minTidx][2]
#        print(readInfo[minTidx][2] - Tbase, "\t\t", writeData)
#        
#        length = int((len(writeData) + 1) / 3)
#        hciData = BtSnoop.get_BTsnoop_PktHeader(length)
#        
#        if(minTidx == 0): #Host -> controller
#            if(writeData[0:2] == "01"):    #command
#                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x01)
#            elif(writeData[0:2] == "02"):    #ACL
#                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x02)
#            elif(writeData[0:2] == "05"):    #ISO_ACL
#                hciData = BtSnoop.get_BTsnoop_TxPkt(hciData, writeData, t_us, 0x05)
#            else:
#                print("DEBUG")
#        else:
#            #length = len(readData)
#            #hciData = BtSnoop.get_BTsnoop_PktHeader(length)
#                
#            if(writeData[0:2] == "04"):        #event
#                hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x04)
#            elif(writeData[0:2] == "02"):      #ACL
#                hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x02)
#            elif(writeData[0:2] == "05"):      #ISO_Data
#                hciData = BtSnoop.get_BTsnoop_RxPkt(hciData,writeData,t_us,0x05)
#            else:
#                print("Rx format error")
#                #print("XXX: ", readData[0:2], hciData)
#                exit()    
#            
#        BtSnoop.write_data_into_hci(hciData, f)
#       
#        readInfo[minTidx][1] = False
#        readInfo[minTidx][2] = 999999
#        readInfo[minTidx][3] = readInfo[minTidx][3] + readInfo[minTidx][4]
#        #exit()
#    
#    f.close()
    

#    scriptFile.close()
    
if __name__ == "__main__":
    main()   