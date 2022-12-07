import hashlib
import datetime
import asyncio
import socket
from contextlib import closing
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
    port = None
    registered = None   # bool
 
    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.registered = False
        self.port = self.find_free_port()

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

            if (i-num1)%((num2-num1)//10) == 0:
                self.printf(f"checked {i-num1} strings,  {num2 - i} strings left to check")      
            aStr = self.numToStr(i)
            locMd5 = hashlib.md5(aStr.encode()).hexdigest()
            if locMd5 == result:
                return aStr
            i += 1
            
        return 'NOT_FOUND'

    def getStatusCode(self, rep)->int:
        msgKeys = rep.split()
        if self.verify_msg(msgKeys):
            return int(msgKeys[-1])
        return 0


    def handle_work_req(self, req:str)->str:
        msgKeys = req.split()
        #if not self.verify_msg(msgKeys):
            #return STATUS.NOT_ALLOWED
        if msgKeys[0] == 'wrk':
            self.printf(f"recieved crack job")
            jid, shardNo, md5, start, end = msgKeys[1], msgKeys[2], msgKeys[3], int(msgKeys[4]), int(msgKeys[5])
            self.printf(f"job summary: {jid} {shardNo} {md5} {start} {end}")
            ans = self.crack(start, end, md5)
            self.printf(f"worker find it? [{ans}]")
            return self.makeMsg(ACTION.ANSWER, self.id, f"{jid} {shardNo} {ans}")
        elif msgKeys[0] == 'rmv':
            wid, wip, wp = msgKeys[1], msgKeys[2], msgKeys[3]
            return STATUS.OK
        elif msgKeys[0] == 'ans':
            wid, ans = msgKeys[1], msgKeys[2]
            return STATUS.OK
        elif msgKeys[0] == 'che':
            return STATUS.OK
        else:
            return STATUS.NOT_ALLOWED

    def find_free_port(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    # async functions
    async def handle_work(self, reader, writer):
        request = (await reader.read(255)).decode('utf8')
        self.printf(f"received [{request}]")
        response = self.handle_work_req(request)
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
        s.close()

    async def run_service(self):
        s = await asyncio.start_server(self.handle_work, self.ip, self.port)
        self.printf(f"establish worker on {self.ip}:{self.port}")
        async with s:
            await s.serve_forever()

