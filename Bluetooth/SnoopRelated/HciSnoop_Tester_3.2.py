# https://fte.com/webhelpii/bpa600/Content/Technical_Information/BT_Snoop_File_Format.htm
import sys
import serial
import serial.tools.list_ports as port_list
import multiprocessing as mp
#import BtSnoop
import HciSnoopTesterCore
import signal

#===================================================================================# 
scriptFile = []
def GetSerialPortInfo():
    ports = list(port_list.comports())    
    return ports      
        
def getMode():
    return 0x01

def close_handler():
    global scriptFile
    HciSnoopTesterCore.closeSnoopFile()
    HciSnoopTesterCore.closeSerialPort();
    
def signal_handler(signal, frame):
    global scriptFile
    print('You pressed Ctrl+C!')
    close_handler()
    exit()

def main():
    scriptTab = []
    serialModeSelection = getMode()
 
    cpuCount = mp.cpu_count()
    print("CPU count: ",cpuCount )

    scriptTab.append(sys.argv[1]);
    signal.signal(signal.SIGINT, signal_handler)

    if(serialModeSelection == 0x01):
        script = scriptTab[0]
        scriptFile.append( open(script, 'r'))
    
        result = HciSnoopTesterCore.TesterInit(script,scriptFile[0])
        seekIdx = scriptFile[0].tell()
        scriptFile[0].close()

        HciSnoopTesterCore.mainHadler(script, seekIdx, "SERIAL", 0 , 0, []) #HciSnoopTesterCore.gDevNode
        close_handler()

    print("=====================")
    print("|      Finished     |")
    print("=====================")


    
if __name__ == "__main__":
    main()   