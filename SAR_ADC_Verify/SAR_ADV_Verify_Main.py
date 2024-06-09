import sys
import numpy as np
import matplotlib.pyplot as plt
import random

FAKE_DATA = True
reslosion = 12
vcc = 3.3
vIn_max = 3.6
vIn_min = -0.3

def main():
    LSB = vcc / (2**reslosion);
    vTransition = []        
    for i in range(1, 2**reslosion):
        vTemp = LSB * (i - 0.5) #+ 0.3 * LSB * random.random();
        vTransition.append(vTemp)
    #print(vTransition)
    #plt.plot(vTransition)
    #plt.show()

    if(FAKE_DATA):        
        signalTimeDiff = 1/(400*1000)
        s = np.linspace(start = vIn_min, stop = vIn_max , num = (int)(1 / signalTimeDiff))
        #plt.plot(s)
        #plt.show()
        #print( np.shape(s)[0] )
        
        k = 0
        cnt = 0
        quantizedData = []
        vTransitionFake = []
        for i in range(1, 2**reslosion):
            vTemp = LSB * (i - 0.5) + 0.4 * LSB * random.random();
            vTransitionFake.append(vTemp)
        
        
        while(cnt < np.shape(s)[0]):
                
            if(k == len(vTransitionFake)):
                quantizedData.append(k)
                cnt += 1
            elif(s[cnt] <= vTransitionFake[k]):
                quantizedData.append(k)
                cnt += 1
            else:
                #print("Test0", k)
                k += 1

        #plt.plot(quantizedData)
        #plt.show()
    else:
        #get external data
        exit("TBD")

    dataStat = []
    codeWidth = []
    dnl = []
    inl = []
    for i in range(0, 2**reslosion):
        dataStat.append(0);
        codeWidth.append(0); 
        dnl.append(0)
        inl.append(0)

    dataTotalPoint = 0
    for i in range(0, len(quantizedData)):
        dataStat[quantizedData[i]] += 1
        dataTotalPoint += 1
    
    point2VoltageFactor = (vIn_max - vIn_min) / dataTotalPoint
        
    
    temp = 0    #unit: points
    for i in range(1, len(dataStat)-1):
        temp += dataStat[i]
    lsb_pnt = temp / ((2**reslosion) - 2)
    fsr_pnt = temp + 2 * lsb_pnt

    vOffset = ((dataStat[0] - 0.5 * lsb_pnt) * point2VoltageFactor + vIn_min) -  0 ##vTransition[0]
    #print(dataStat[0],  (dataStat[0] - 0.5 * lsb_pnt), (dataStat[0] - 0.5 * lsb_pnt) * point2VoltageFactor, vTransition[0])
    
    gainErrorVoltage = (fsr_pnt * point2VoltageFactor / vcc -1) * 100

    print("LSB(v)")
    print("\tIdeal(v): ", LSB)
    print("\tDUT(v)  : ", lsb_pnt * point2VoltageFactor)
    print("\tDiff ratio(%)  : ", 100 * (lsb_pnt * point2VoltageFactor / LSB) -100 )
    print("FSR(v)")
    print("\tIdeal(v): ", vcc)
    print("\tDUT(v)  : ", fsr_pnt * point2VoltageFactor)
    print("Voffset(v):\n\t", vOffset)
    print("Gain Error Voltage(%):\n\t", gainErrorVoltage)
    
    for i in range(1, len(codeWidth)-1):
        codeWidth[i] = dataStat[i]# - dataStat[i-1];
        dnl[i] = (codeWidth[i] / lsb_pnt) - 1
        inl[i] = inl[i-1] + dnl[i]/2; 

    #print(dataStat)
    #print(lsb_pnt, temp)
    #print(codeWidth)
    #print(dnl)
    #print(inl)

    plt.plot(dnl)
    #plt.plot(inl)
    plt.grid(True)
    plt.xlim((0, (2**reslosion) -1))
    plt.show()
        
        

if __name__ == "__main__":
    main()      
    