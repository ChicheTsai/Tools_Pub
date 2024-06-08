# A STUDY OF BLUETOOTH FREQUENCY HOPPING SEQUENCE: MODELING AND A PRACTICAL ATTACK
import sys
import BtHoppingSeqCore

BasicFreqHoppingTab = []
AfhFreqHoppingTab = []
VERIFY = True

def main():
    global BasicFreqHoppingTab, AfhFreqHoppingTab
    # print("Frequency Hopping Type:")
    # 0x00: Basic
    # 0x01: AFH
    # 0x10: BLE legacy, TBD
    # 0x11: BLE CSA#2, TBD
    f = [] 
    if(VERIFY):
        verifyMode = int(sys.argv[1]);
        f_golden = BtHoppingSeqCore.get_verify_pattern() 
        [startClk, masterAddr, numOfTicks, mode, hoppingMap] = BtHoppingSeqCore.getVerfy_info(verifyMode)
    else:
        mode = int(sys.argv[1],16);
        if(mode & 0x10 == 0x00):    #BT cases
            if(len(sys.argv) == 0x06):
                masterAddr = int(sys.argv[2],16);
                startClk =   int(sys.argv[3],16);
                if(mode & 0x01 == 0x00):    #BT basic
                    hoppingMap = 0x7FFFFFFFFFFFFFFFFFFF
                else:   #AFH cases
                    hoppingMap = int(sys.argv[4],16);
                numOfTicks = int(sys.argv[5]);
            else:
                print("Please determine the number of input parameters")
                exit()
        else:   #Ble cases
            if(mode & 0x01 == 0x00):    #BLE CSA#1
                lastUnmappedChannl = int(sys.argv[2],16);
                hopInc             =   int(sys.argv[3],16);
                hoppingMap         = int(sys.argv[4],16);
            else:                       #BLE CSA#2
                masterAddr = int(sys.argv[2],16);
                startClk =   int(sys.argv[3],16);
                hoppingMap = int(sys.argv[4],16);
                numOfTicks = int(sys.argv[5]);

    #print(mode, masterAddr, startClk, numOfTicks)
    
    if(mode & 0x10 == 0x00):    #BT cases
        BasicFreqHoppingTab = BtHoppingSeqCore.getBTfreqHoppingBasic()
        if(mode & 0x01 == 0x01): 
            AfhFreqHoppingTab = BtHoppingSeqCore.getBTfreqHoppingAfh(hoppingMap)
            #print(len(AfhFreqHoppingTab))
            #print((AfhFreqHoppingTab))
    else:
        LeFreqHoppingTabCSA1 = BtHoppingSeqCore.getBLEfreqHoppingCSA1(hoppingMap)
       
    for i in range(0,numOfTicks, 2):
        #mode = int(input())
        if(mode & 0x10 == 0x00):    #BT cases
            if(mode & 0x01 == 0x00): 
                # BT, basic channel hopping
                #masterAddr = input("BD address: 0x")
                #startClk = input("Start clock: 0x")        
                result = BtHoppingSeqCore.BasicChannelHopping(masterAddr, startClk + i)
                f.append(BasicFreqHoppingTab[result[0]])
            else: 
                # BT, AFH channel hopping
                result = BtHoppingSeqCore.AFHChannelHopping(masterAddr, startClk + i,hoppingMap)
                f.append(AfhFreqHoppingTab[result[0]])
        else:                        #BLE cases
            if(mode & 0x01 == 0x00): #CSA#1
                result = BtHoppingSeqCore.BleChannelHoppingCsa1(lastUnmappedChannl, hopInc, hoppingMap)
                f.append(LeFreqHoppingTabCSA1[result[0]])
    
    if(VERIFY):
        if(len(f) != len(f_golden[verifyMode])):
            print("Length failed\t", len(f), len(f_golden[verifyMode]) )
        else:
            for i in range(0,len(f)):
                if(f[i] != f_golden[verifyMode][i]):
                    print("Failed\t", i)
                    print(f)
                    print(f_golden[verifyMode])
                    return
        print("verifyMode ",verifyMode, " is pass")
        #print(f)
    else:
        for i in range(0,len(f)):
            print("Clock:\t", hex(startClk+i*2) ,"\tFreq:\t",f[i])
                
    
if __name__ == "__main__":
    main()  