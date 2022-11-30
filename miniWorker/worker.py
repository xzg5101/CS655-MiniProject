import hashlib
import math

# worker class that can do all computing functions a worker node needs 
class Worker:
    ip = None
    serverIp = None
    start = None # int
    end = None # int
    numCap = None
    passwordLen = 5
    alList = [ 
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", \
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", \
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", \
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

    def __init__(self):
        self.numCap = int(math.pow(len(self.alList), self.passwordLen)-1)   # max number a string can be after converting to position

    # set methods
    def setIp(self, ip):
        self.ip = ip
    
    def setServerIp(self, serverIp):
        self.ip = serverIp

    def updateRange(self, start, end):
        self.start = start
        self.end = end

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

    # imput a range and a md5 hash, check if any string in the range will have same hash as input
    def crack(self, num1, num2, result)->str:
        i = num1
        while i < num2:        
            aStr = self.numToStr(i)
            locMd5 = hashlib.md5(aStr.encode()).hexdigest()
            if locMd5 == result:
                return aStr
            i += 1
            
        return "NOTFOUND"