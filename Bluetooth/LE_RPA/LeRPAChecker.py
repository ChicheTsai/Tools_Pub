# https://www.796t.com/content/1546603272.html
# https://segmentfault.com/a/1190000039335378
# https://stackoverflow.com/questions/65389275/modulenotfounderror-no-module-named-crypto-python-3-9-pycharm
#from Crypto.Cipher import AES
import sys
import os
import random
#import base64
import LePRA

def main():
    key = (sys.argv[1]);
    mac = (sys.argv[2]);
    #print(key, mac)
    #key0 = '73394d5b541690565755ad35ea02b4cf'
    #mac0 = '6f8f9f4cca48'
    #print(key0, mac0)
    # ================ RPA resolving ==================
    rpaResol = LePRA.RPAresolver(key, mac)
    if( mac.upper() == rpaResol.upper()):
        print('MAC pass')
        print('mac = ' + mac)
    else:
        print('MAC fail')
        print('rxMac = '+mac, 'rpa = ' + rpaResol)     
    exit()
    
if __name__ == "__main__":
    main()  