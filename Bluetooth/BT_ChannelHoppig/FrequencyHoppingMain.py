# A STUDY OF BLUETOOTH FREQUENCY HOPPING SEQUENCE: MODELING AND A PRACTICAL ATTACK
import sys
import BtHoppingSeqCore
import BtHoppingSeqVerify

BasicFreqHoppingTab = []
AfhFreqHoppingTab = []
VERIFY = False

def main():
    global BasicFreqHoppingTab, AfhFreqHoppingTab
    # print("Frequency Hopping Type:")
    # 0x00: Basic
    # 0x01: AFH
    # 0x10: BLE legacy, TBD
    # 0x11: BLE CSA#2, TBD
    f = [] 
    if(VERIFY):
        #verifyMode = int(sys.argv[1]);
        verifyMode = 0x00
        verifyMaxSet = BtHoppingSeqVerify.get_maximum_verify_set()
        f_golden = BtHoppingSeqVerify.get_verify_pattern() 
        #[startClk, masterAddr, numOfTicks, mode, hoppingMap] = BtHoppingSeqVerify.getVerfy_info(verifyMode)
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

    while(True):
        if(VERIFY):
            [startClk, masterAddr, numOfTicks, mode, hoppingMap] = BtHoppingSeqVerify.getVerfy_info(verifyMode)
            f = []
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
            status = BtHoppingSeqVerify.result_check(f, f_golden[verifyMode], verifyMode)
            if(status == True):
                verifyMode += 1;
                if(verifyMode >= BtHoppingSeqVerify.get_maximum_verify_set()):
                    break;
            else:
                break;
        else:
            #Print Result
            for i in range(0,len(f)):
                print("Clock:\t", hex(startClk+i*2) ,"\tFreq:\t",f[i])
                
    
if __name__ == "__main__":
    main()  