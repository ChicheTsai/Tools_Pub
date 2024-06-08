# https://www.796t.com/content/1546603272.html
from Crypto.Cipher import AES

#import os
import random
import base64


def bytesToHexString(bs):
    return ''.join(['%02X ' % b for b in bs])

def hexStringTobytes(str):
    str = str.replace(" ", "")
    return bytes.fromhex(str)

def RPAresolver(k, mac):
    r = mac[0:6]                              #prand, 24bit
    return RPAgenerator(k,r)

def RPAgenerator(k, r):
    hexstr_key = hexStringTobytes(k)
    plaintext = '00000000000000000000000000'+ r
    
    hexstr_plaintext = hexStringTobytes(plaintext)
    cryptor = AES.new(hexstr_key,AES.MODE_ECB)
    ciphertext = cryptor.encrypt(hexstr_plaintext)
    # print(bytesToHexString(ciphertext))
    cryptor_prand = bytesToHexString(ciphertext)[39:].replace(" ", "")  #hash
    rpa = r + cryptor_prand
    return rpa