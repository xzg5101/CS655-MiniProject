import hashlib
import datetime
import asyncio
import socket
from contextlib import closing
from Node import Node
from Shard import Shard
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
    shard_list = None
 
    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.registered = False
        self.port = self.find_free_port()

        self.shard_list = []

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
    async def crack(self, jid:int, num1:int, num2:int, result:str)->str:
        #self.updateRange(num1, num2)
        self.printf(f"job {jid} begins")
        i = num1

        print_step = (num2-num1)//10
        check_step = (num2-num1)//100

        while i < num2:
            for j in self.shard_list:
                if j.jid == jid and j.stop == True:
                    self.printf(f"job {jid} terminated by stop signal, {num2 - i} strings left unchecked")
                    self.shard_list.remove(j)
                    return 'INTERRUPTED'
            if (i-num1)%print_step == 0:
                self.printf(f"tried {i-num1} strings,  {num2 - i} strings left to check")
            if (i-num1)%check_step == 0:
                await asyncio.sleep(0.1)         
            aStr = self.numToStr(i)
            locMd5 = hashlib.md5(aStr.encode()).hexdigest()
            if locMd5 == result:
                for j in self.shard_list:
                    if j.jid == jid:
                        j.answer = aStr
                        return aStr
            i += 1
            
        return 'NOT_FOUND'

    def getStatusCode(self, rep)->int:
        msgKeys = rep.split()
        if self.verify_msg(msgKeys):
            return int(msgKeys[-1])
        return 0

    async def do_work(self, md5, start, end):
        answer = self.crack(start, end, md5)
        return answer

    def handle_work_req(self, req:str)->str:
        msgKeys = req.split()
        #if not self.verify_msg(msgKeys):
            #return STATUS.NOT_ALLOWED
        if msgKeys[0] == 'wrk':
            self.printf(f"recieved crack job")
            jid, shardNo, md5, start, end = msgKeys[1], msgKeys[2], msgKeys[3], int(msgKeys[4]), int(msgKeys[5])
            self.printf(f"job summary: {jid} {shardNo} {md5} {start} {end}")
            #ans = self.crack(start, end, md5)
            #self.printf(f"worker find it? [{ans}]")
            return self.makeMsg(ACTION.ACK, self.id, f"{jid} {shardNo} {ans}")
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
        msgKeys = request.split()

        if msgKeys[0] == ACTION.WORK:
            self.printf(f"recieved crack job")
            jid, shardNo, md5, start, end = int(msgKeys[1]), msgKeys[2], msgKeys[3], int(msgKeys[4]), int(msgKeys[5])
            self.printf(f"job summary: {jid} {shardNo} {md5} {start} {end}")
            
            shard = Shard(jid, start, end, md5)
            self.shard_list.append(shard)

            response = self.makeMsg(ACTION.ACK, jid, STATUS.OK)
            writer.write(response.encode('utf8'))
            await writer.drain()
            writer.close()            
            task = asyncio.create_task(self.crack(jid, start, end, md5))
            task

            while True:
                await asyncio.sleep(1)
                #self.printf(f"checking job status")
                found = 0
                for i in self.shard_list:
                    found = 1
                    if i.jid == jid and i.answer != None:
                        await self.send_to_server(ACTION.ANSWER, jid, f"{i.answer} {self.id}")
                        self.shard_list.remove(i)
                        return
                if found == 0:
                    #self.printf(f"job answer not found")
                    return
                    
                

        elif msgKeys[0] == ACTION.INTERRUPT:
            self.printf(f"this is an interrupt signal")
            jid = int(msgKeys[1])
            for i in self.shard_list:
                if i.jid == jid:
                    i.stop = True
                    break
            response = self.makeMsg(ACTION.ACK, self.id, STATUS.OK)
            self.printf(f"send response [{response}]")
            writer.write(response.encode('utf8'))
            await writer.drain()
            writer.close()
        else:
            response = self.makeMsg(ACTION.ACK, self.id, STATUS.OK)
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

    async def send_to_server(self, act, id, payload):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serverIp, self.serverPort))
        msg = self.makeMsg(act, id, payload)
        self.printf(f"sending to server {msg}")
        s.sendall(msg.encode('utf-8'))
        data = b""
        data += s.recv(1024)
        self.printf(f"received data [{data.decode('utf-8')}]")
        s.close()

    async def run_service(self):
        s = await asyncio.start_server(self.handle_work, self.ip, self.port)
        self.printf(f"establish worker on {self.ip}:{self.port}")
        async with s:
            await s.serve_forever()

