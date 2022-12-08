import hashlib
import datetime
import asyncio
import socket
from contextlib import closing
import time
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
    shard = None
    compute_time_out = None

 
    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.registered = False
        self.port = self.find_free_port()
        self.compute_time_out = 17000

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
    
    def shard_summary(self, shard: Shard)->None:
        self.printf(f"shard summary:")
        self.printf(f"\tid:\t[{shard.jid}]")
        self.printf(f"\tmd5:\t[{shard.md5}]")
        self.printf(f"\trange:\t[{shard.start}] to [{shard.end}]")
        self.printf(f"\tshard number:\t[{shard.shardNo}]")


    # imput a range and a md5 hash, check if any string in the range will have same hash as input
    async def crack(self, num1:int, num2:int, result:str)->str:
        #self.updateRange(num1, num2)
        self.printf(f"job {self.shard.jid} begins")
        i = num1

        print_step = (num2-num1)//10
        check_step = (num2-num1)//100

        while i < num2:
            if self.shard.stop == True:
                    self.printf(f"job {self.shard.jid} terminated, {num2 - i} strings unchecked")
                    return 'INTERRUPTED'
            if (i-num1)%print_step == 0:
                self.printf(f"tried {i-num1} strings, {num2 - i} left")
            if (i-num1)%check_step == 0:
                await asyncio.sleep(0.1)         
            aStr = self.numToStr(i)
            locMd5 = hashlib.md5(aStr.encode()).hexdigest()
            if locMd5 == result:
                self.shard.answer = aStr
                self.shard.checked = True
                self.printf(f"answer found to be [{aStr}]")
                return aStr
            i += 1
        self.shard.checked = True
        return 'NOT_FOUND'

    def getStatusCode(self, rep)->int:
        msgKeys = rep.split()
        if self.verify_msg(msgKeys):
            return int(msgKeys[-1])
        return 0

    async def do_work(self, md5, start, end):
        answer = self.crack(start, end, md5)
        return answer



    def find_free_port(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    # async functions
    async def handle_work(self, reader, writer):
        request = (await reader.read(255)).decode('utf8')
        #self.printf(f"received [{request}]")
        msgKeys = request.split()

        if msgKeys[0] == ACTION.WORK:
            self.printf(f"recieved job shard")
            jid, shardNo, md5, start, end = int(msgKeys[1]), msgKeys[2], msgKeys[3], int(msgKeys[4]), int(msgKeys[5])
            #self.printf(f"job summary: {jid} {shardNo} {md5} {start} {end}")
            
            self.shard = Shard(jid, shardNo, start, end, md5)
            self.shard_summary(self.shard)

            response = self.makeMsg(ACTION.ACK, jid, STATUS.OK)
            writer.write(response.encode('utf8'))
            await writer.drain()
            writer.close()            
            task = asyncio.create_task(self.crack(start, end, md5))
            task

            timeout = time.time() + self.compute_time_out//(self.numCap//(self.shard.end - self.shard.start))
            while time.time()<timeout:
                await asyncio.sleep(1)
                #self.printf(f"checking job status")
                if self.shard.jid == jid and self.shard.answer != None:
                    await self.send_to_server(ACTION.ANSWER, jid, f"{self.shard.answer} {self.id} {shardNo}")
                    self.printf(f"sent answer [{self.shard.answer}] to server") 
                    return
            await self.send_to_server(ACTION.ANSWER, jid, f"TIME_OUT {self.id} {shardNo}")
            self.printf(f"job timeout")          
                

        elif msgKeys[0] == ACTION.INTERRUPT:
            self.printf(f"received an interrupt signal")
            jid = int(msgKeys[1])
            if self.shard.jid == jid:
                    self.shard.stop = True
     
            response = self.makeMsg(ACTION.ACK, self.id, STATUS.OK)
            #self.printf(f"send response [{response}]")
            writer.write(response.encode('utf8'))
            await writer.drain()
            writer.close()
        else:
            response = self.makeMsg(ACTION.ACK, self.id, STATUS.OK)
            #self.printf(f"send response [{response}]")
            writer.write(response.encode('utf8'))
            await writer.drain()
            writer.close()
    
    async def reg(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serverIp, self.serverPort))
        
        reg_msg = self.makeMsg(ACTION.REGISTER, self.id, f"{self.ip} {self.port}")
        s.sendall(reg_msg.encode('utf-8'))
        data = b""
        data += s.recv(1024)
        self.printf("registered with "+ self.serverIp)
        #self.printf(f"received data [{data.decode('utf-8')}]")
        s.close()

    async def send_to_server(self, act, id, payload):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serverIp, self.serverPort))
        msg = self.makeMsg(act, id, payload)
        #self.printf(f"sending to server {msg}")
        s.sendall(msg.encode('utf-8'))
        data = b""
        data += s.recv(1024)
        #self.printf(f"received data [{data.decode('utf-8')}]")
        s.close()

    async def run_service(self):
        s = await asyncio.start_server(self.handle_work, self.ip, self.port)
        self.printf(f"establish worker on {self.ip}:{self.port}")
        async with s:
            await s.serve_forever()

