import hashlib

from Node import Node

# worker class that can do all computing functions a worker node needs 
class Worker(Node):
    
    serverIp = None     # str
    serverPort = None   # int
    serverId = None     # int
    start = None        # int
    end = None          # int
 
    def __init__(self):
        self.setNumCap()
        self.id = self.genId()

    # set methods
    def setIp(self, ip:str)->None:
        self.ip = ip
    
    # record server IP
    def setServer(self, serverIp:str, port: int)->None:
        self.serverIp = serverIp
        self.serverPort = port
        

    #update range of search
    def updateRange(self, start:int, end:int)->None:
        if start > end:
            start, end = end, start
        self.start = start
        self.end = end

    # imput a range and a md5 hash, check if any string in the range will have same hash as input
    def crack(self, num1:int, num2:int, result:str)->str:
        self.updateRange(num1, num2)
        i = num1
        while i < num2:        
            aStr = self.numToStr(i)
            locMd5 = hashlib.md5(aStr.encode()).hexdigest()
            if locMd5 == result:
                return aStr
            i += 1
            
        return "NOTFOUND"

