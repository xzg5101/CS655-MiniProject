import hashlib
import datetime
import asyncio
import socket
from Node import Node
from StatusCode import STATUS
from Action import ACTION

# worker class that can do all computing functions a worker node needs 
class Worker(Node):
    
    serverIp = None     # str
    serverPort = None   # int
    serverId = None     # int
    start = None        # int
    end = None          # int
    port = 50006
    registered = None   # bool
 
    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.registered = False

    def printf(self, s:str):
        print(f"{datetime.datetime.now()} Worker:", s)

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

    def getStatusCode(self, rep)->int:
        msgKeys = rep.split()
        if self.verify_msg(msgKeys):
            return int(msgKeys[-1])
        return 0


    def handle_worker_req(self, req:str)->str:
        msgKeys = req.split()
        if not self.verify_msg(msgKeys):
            return STATUS.NOT_ALLOWED
        if msgKeys[0] == 'wrk':
            wid, wip, wp = msgKeys[1], msgKeys[2], msgKeys[3]
            return self.register_worker(wid, wip, wp)
        elif msgKeys[0] == 'rmv':
            wid, wip, wp = msgKeys[1], msgKeys[2], msgKeys[3]
            return self.remove_worker(wid, wip, wp)
        elif msgKeys[0] == 'ans':
            wid, ans = msgKeys[1], msgKeys[2]
            return STATUS.OK
        else:
            return STATUS.NOT_ALLOWED

    # async functions

    async def handle_work(self, reader, writer):
        request = (await reader.read(255)).decode('utf8')
        self.printf(f"received [{request}]")
        response = self.handle_worker_req(request)
        self.printf(f"send response [{response}]")
        writer.write(response.encode('utf8'))
        await writer.drain()
        writer.close()
    
    async def reg(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serverIp, self.serverPort))
        self.printf("registering with "+ self.serverIp)
        reg_msg = self.makeMsg(ACTION.REGISTER, self.id, f"{self.ip} {self.port}")
        s.sendall(reg_msg.encode('utf-8'))
        data = b""
        data += s.recv(1024)
        self.printf(f"received data [{data.decode('utf-8')}]")

    async def run_service(self):
        s = await asyncio.start_server(self.handle_work, self.ip, self.port)
        self.printf(f"establish worker on {self.ip}:{self.port}")
        async with s:
            await s.serve_forever()

