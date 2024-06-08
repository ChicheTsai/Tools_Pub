import wexpect 
import time

child = ""
TIMEOUT = 10

def waitString(string):
    print("WAIT:", string)
    child.expect(string)
    
    if(string != child.after):
        print("It did not receive: ", string)
    
def writeString(string):
    child.sendline(string)
    
def waitSecond(sec):
    time.sleep(sec)

def AppStart():
    global child
    cmd = "exe2.exe"
    child = wexpect.spawn(cmd, timeout = TIMEOUT) 
    
    waitString("AAAA")
    waitSecond(1)
    writeString("1")
    waitSecond(2)
    waitString("BBBBB")
    writeString("2")
    waitString("CCCCC")
    writeString("1")
    
    child.close()
    
if __name__ == '__main__':
    AppStart()