import time
import random
import re
import math


# backbone class for server and worker
class Node:
    id = None       # int
    ip = None       # str
    pwPattern = '^[a-zA-Z]{5,5}$'
    md5Pattern = '^[a-z0-9]{32,32}$'
    idPattern = '^[0, 1]{58}$'
    numCap = None   # int
    passwordLen = 5
    idSize = 58
    
    # all chars that may occur
    alList = [ 
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", \
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", \
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", \
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

    acts = ["reg", "wrk", "rmv", "ans", "ack"]
    
    # max number a string can be after converting to position
    def setNumCap(self)->None:
        self.numCap = int(math.pow(len(self.alList), self.passwordLen))   


    # 58 bit snowflake id: first 46 bits: curret time accurrate to 1/10000 second, last 12 bits: random number
    def genId(self)->int:
        return (int(time.time()*10000)<<12) | random.getrandbits(12)    

    # check if a password is valid   
    def verifyPassword(self, password)->bool:
        return re.fullmatch(self.pwPattern, password) is not None

    # check if a md5 hash is valid
    def verifyMd5(self, md5:str)->bool:
        return re.fullmatch(self.md5Pattern, bin(md5)) is not None

    # check if a ID is valid
    def verifyID(self, someId):
        return someId>>self.idSize == 0

    # convert a number to its' corresponding string in the list from AAAAA to zzzzz
    def numToStr(self, num)->str:
        if num < 0 or num > self.numCap:  # 52
            return ""

        limit = ""
        while len(limit) < 5:
            limit = self.alList[(num%52)] + limit
            num = num//52

        return limit

    # convert a string to its relative postion from AAAAA to zzzzz
    def strToNum(self, s)->int:
        num = 0
        for i in range(len(s)):
            num += self.alList.index(s[i]) * math.pow(52, len(s)-1-i)
        return int(num)
    
    # make a standard format message
    def makeMsg(self, act: str, id: int, payload: str):
        return f"{act} {str(id)} {payload}"
    
    # not used
    def verify_wrk_msg(self, msgKeys)->bool:
        if len(msgKeys) < 2:
            return False
        elif not msgKeys[0] in self.acts:
            return False
        elif not self.verifyID(int(msgKeys[1])):
            return False
        return True
    
    # not used
    def verify_usr_msg(self, msgKeys)->bool:
        if len(msgKeys) > 2:
            return False
        elif not msgKeys[0] in self.acts:
            return False
        return True
