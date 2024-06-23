# https://fte.com/webhelpii/bpa600/Content/Technical_Information/BT_Snoop_File_Format.htm
# https://www.cnblogs.com/klchang/p/7296058.html
import sys
import time
from datetime import datetime


def getCurrentYMD():
    nowTime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    dt_obj = datetime.strptime(nowTime,'%Y-%m-%d %H:%M:%S.%f')
    #print(nowTime,"\t",dt_obj,"\t",dt_obj.timestamp())
    #print(dir(dt_obj))
    newTime = str(dt_obj.year) + "-" + str(dt_obj.month) + "-" + str(dt_obj.day)
    #print(newTime)
    return newTime

def getTimeStamp(tStr):
    dt_obj = datetime.strptime(tStr,'%Y-%m-%d %H:%M:%S.%f')
    return (dt_obj.timestamp())
