# A STUDY OF BLUETOOTH FREQUENCY HOPPING SEQUENCE: MODELING AND A PRACTICAL ATTACK
#import sys
#import os

privateBasicFreqHoppingTab = []
privateAfhFreqHoppingTab = []
privateBleFreqHoppingCsa1Tab = []
privateBleFreqHoppingCsa2Tab = []
   
def getBit(num, idx):
    return ((num >> idx) & 0x01)

def PREMSWAP(arr, idx1, idx2):
    tmp = arr[idx1]
    arr[idx1] = arr[idx2]
    arr[idx2] = tmp
    return arr
    
def PERM(input,P):
    #convert input value to array
    inArray = [0,0,0,0,0] #[LSB...MSB]
    for i in range(0,5):
        inArray[i] = getBit(input,i)
    #P0  = {Z0,Z1}
    #P1  = {Z2,Z3}
    #P2  = {Z1,Z2}
    #P3  = {Z3,Z4}
    #P4  = {Z0,Z4}
    #P5  = {Z1,Z3}
    #P6  = {Z0,Z2}
    #P7  = {Z3,Z4}
    #P8  = {Z1,Z4}
    #P9  = {Z0,Z3}    
    #P10 = {Z2,Z4}
    #P11 = {Z1,Z3}
    #P12 = {Z0,Z3}
    #P13 = {Z1,Z2}
    
    #stage1: P13 P12
    if(getBit(P,13)):   
        inArray = PREMSWAP(inArray,1,2)
    if(getBit(P,12)):
        inArray = PREMSWAP(inArray,0,3)
    #stage2: P11 P10
    if(getBit(P,11)):
        inArray = PREMSWAP(inArray,1,3)
    if(getBit(P,10)):
        inArray = PREMSWAP(inArray,2,4)    
    #stage3: P9  P8
    if(getBit(P,9)):
        inArray = PREMSWAP(inArray,0,3)
    if(getBit(P,8)):
        inArray = PREMSWAP(inArray,1,4)
    #stage4: P7  P6
    if(getBit(P,7)):
        inArray = PREMSWAP(inArray,3,4)
    if(getBit(P,6)):
        inArray = PREMSWAP(inArray,0,2)    
    #stage5: P5  P4
    if(getBit(P,5)):
        inArray = PREMSWAP(inArray,1,3)
    if(getBit(P,4)):
        inArray = PREMSWAP(inArray,0,4)    
    #stage6: P3  P2
    if(getBit(P,3)):
        inArray = PREMSWAP(inArray,3,4)
    if(getBit(P,2)):
        inArray = PREMSWAP(inArray,1,2)    
    #stage7: P1  P0
    if(getBit(P,1)):
        inArray = PREMSWAP(inArray,2,3)
    if(getBit(P,0)):
        inArray = PREMSWAP(inArray,0,1)
    
    ret = 0
    for i in range(4,-1,-1):
        ret = (ret<<1) + inArray[i]
 
    return ret
    
    
def BasicChannelHopping(sAddr, sClk):
    #global BasicFreqHoppingTab

    sClk = sClk & 0xFFFFFFFE
    #X = CLK[6:2]
    X = (sClk & 0x7C) >> 2
    
    if((sClk & 0x02)):
        Y1 = 0x1F
        Y2 = 32
    else:
        Y1 = 0x00
        Y2 = 0x00

    A = ((sAddr & 0xF800000) >>23) ^ ((sClk & 0x3E00000) >>21) 
    B = (sAddr & 0x780000) >>19
    C = 0
    for i in range(8,-1,-2):
        C = (C << 1) + getBit(sAddr,i)
    C = C ^ ((sClk & 0x1F0000) >>16) 
    
    D = ((sAddr & 0x7FC00) >>10) ^ ((sClk & 0xFF80) >>7)
    E = 0
    for i in range(13,0,-2):
        E = (E << 1) + getBit(sAddr,i)
    F = (16 * ((sClk & 0xFFFFF80) >>7)) % 79

    P = C ^ Y1
    P = (P << 9) + D
    
    #print("sClk: ", hex(sClk))
    #print("sAddr: ", hex(sAddr))
    ##print("X:", hex(X))
    ##print("Y1:", Y1)
    ##print("Y2:", Y2)
    #print("A:", A, hex((sAddr & 0xF800000) >>23), hex((sClk & 0x3E00000) >>21) )
    #print("B:", B)
    #print("C:", C, hex((sClk & 0x1F0000) >>16))
    #print("D:", D, hex((sAddr & 0x7FC00) >>10), hex((sClk & 0xFF80) >>7))
    #print("E:", E)
    #print("F:", F, hex((sClk & 0xFFFFF80) >>7))
    
    Z_ = (X + A) % 32
    #print("Z_:", Z_)
    Z = Z_ ^ B
    #print("Z:", Z)
    Z = PERM(Z, P)
    #print("Znew:", Z)
    fidx = (Z + E + F + Y2) % 79
    
    #print(fidx, "\t",BasicFreqHoppingTab[fidx])
    
    return [fidx,Z,E,Y2]

    
def BT_NeedAfhIdxRemap(idx):
    global privateBasicFreqHoppingTab, privateAfhFreqHoppingTab
    #print("BT_NeedAfhIdxRemap")
    #print(privateBasicFreqHoppingTab)
    #print(privateAfhFreqHoppingTab)
    for i in range(0,len(privateAfhFreqHoppingTab)):
        if(privateAfhFreqHoppingTab[i] ==  privateBasicFreqHoppingTab[idx]):
            return False

    return True
    
def BT_AfhIdxRemap(idx):
    global privateBasicFreqHoppingTab, privateAfhFreqHoppingTab
    #print(BasicFreqHoppingTab[idx])
    for i in range(0,len(privateAfhFreqHoppingTab)):
        if(privateAfhFreqHoppingTab[i] ==  privateBasicFreqHoppingTab[idx]):
            return i
    
def AFHChannelHopping(sAddr, sClk,map):

    N = 0
    tempMap = map

    for i in range(0,79):
        if(tempMap & 0x01):
            N = N +1
        tempMap = tempMap >> 1
        
    F_ = (16 * ((sClk & 0xFFFFF80) >>7)) % N

    result = BasicChannelHopping(sAddr, sClk & 0xFFFFFFFC)
    #print("First result: ",result[0])
    if(BT_NeedAfhIdxRemap(result[0]) == False):
        #print("Remap is not needed ", BT_AfhIdxRemap(result[0]))
        return [BT_AfhIdxRemap(result[0])]
    else:
        #print("Remap is needed ",(result[1] + result[2] + result[3] +F_ ) % N)
        return [(result[1] + result[2] + result[3] +F_ ) % N]

def BleChannelHoppingCsa1(lastUnmappedChannl, hopInc, hoppingMap):
    global  privateBleFreqHoppingCsa1Tab
    idx = (lastUnmappedChannl + hopInc) % 0x37
    
    if(getBit(hoppingMap,idx)):
        return idx
    else:
        numUsedChanl = 0
        for i in range(0,37):
            if(getBit(hoppingMap,i)):
                numUsedChanl = numUsedChanl +1
        
        remapIdx = idx % numUsedChanl
        n = 0
        for i in range(0,37):
            if(getBit(hoppingMap,i)):
                n = n+1
            
            if(n == remapIdx):
                return remapIdx
            
    return 0xFF
        
def getBTfreqHoppingAfh(map):
    global privateBasicFreqHoppingTab, privateAfhFreqHoppingTab
    ret = []
    writeIdx = 0
    tempMap = map
    #print(hex(map))
    for i in range(0,79,2):
        if(tempMap & 0x01):
            ret.append(i)
            writeIdx = writeIdx+1
        tempMap = tempMap >>2
        
    tempMap = map >> 1  
    for i in range(1,79,2):
        if(tempMap & 0x01):
            ret.append(i)
            writeIdx = writeIdx+1
        tempMap = tempMap >>2  
    privateAfhFreqHoppingTab = ret
    return ret    
    
def getBTfreqHoppingBasic(): 
    global privateBasicFreqHoppingTab, privateAfhFreqHoppingTab
    privateBasicFreqHoppingTab = getBTfreqHoppingAfh(0x7FFFFFFFFFFFFFFFFFFF)
    return privateBasicFreqHoppingTab

def getBLEfreqHoppingCSA1(map): 
    global  privateBleFreqHoppingCsa1Tab
    ret = []
    for i in range(0,37):
        if(getBit(map,i)):
            ret.append(i)
            
    privateBleFreqHoppingCsa1Tab = ret
    return ret
    