# https://www.796t.com/content/1546603272.html
# https://segmentfault.com/a/1190000039335378
# https://stackoverflow.com/questions/65389275/modulenotfounderror-no-module-named-crypto-python-3-9-pycharm
#from Crypto.Cipher import AES
import sys
#import os
import random
#import base64
import LePRA

def main():
# ==================== Golden ==============================#
    irk = (sys.argv[1]);
    prand = (sys.argv[2]);
    if(int(irk,16) == 0x00):
        irk = hex(random.randint(2**125 -1,2**128 -1))
        irk = irk.lstrip("0x")
    else:
        irk = irk.lstrip("0x")
    
    if(int(prand,16) == 0x00):
        prand = hex(random.randint(2**20 -1,2**22 -1) + (1<<22) )
        prand = prand.lstrip("0x")
    else:
        prand = prand.lstrip("0x")

    rpaGen  = LePRA.RPAgenerator(irk, prand)
    print("IRA = 0x" + irk)
    print("PRAND = 0x" + prand)
    print("RPA = 0x" + rpaGen)
    exit()

if __name__ == "__main__":
    main()  