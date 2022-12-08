import datetime
import math
import asyncio
import socket
import time
from Node import Node 
from StatusCode import STATUS
from Action import ACTION
from Job import Job
from Environment import DEBUG
class Server(Node):
    numOfWorker = None  # number of workers
    workerList = []
    job = None
    reg_port = None     # int
    req_port = None     # int

    wkr_server = None
    usr_server = None

    writer_list = None

    compute_time_out = None

    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.numOfWorker = 0
        self.ip = '172.17.1.15'
        if DEBUG == 1:
            self.ip = 'localhost'
        self.wkr_port = 50002
        self.req_port = 50003
        self.compute_time_out = 17000   # 2 times the rough estimatino of a single machine loop through all strings

    def printf(self, s:str):
        print(f"{datetime.datetime.now()} Server:", s)

    def register_worker(self, workerID, workerIP, workerPort):
        if any(workerID in worker for worker in self.workerList):
            return STATUS.DUPLICATED
        self.workerList.append([workerID, workerIP, int(workerPort)])
        self.numOfWorker += 1
        self.printf(f"registered worker with id {workerID} and ip {workerIP}")
        return STATUS.OK
    
    def remove_worker(self, workerID, workerIP, workerPort):
        if not any(workerID in worker for worker in self.workerList):
            return STATUS.NOT_FOUND
        self.workerList.remove([workerID, workerIP, workerPort])
        self.numOfWorker -= 1
        self.printf(f"removed worker with id {workerID} and ip {workerIP}")
        return STATUS.OK

    def divdeJob(self, job:Job):
        # no workers
        if self.numOfWorker == 0:
            return job

        # compute job ranges
        jobWidth = math.ceil((job.end - job.start)/self.numOfWorker)
        shards = []
        shard_flags = []
        base = job.start
        for i in range(self.numOfWorker):
            shards.append([base, min(base+jobWidth, job.end)])
            shard_flags.append(False)
            base += jobWidth
        job.numOfShards = len(shards)
        job.shards = shards
        job.shard_flags = shard_flags
        return job

    def handle_worker_req(self, req:str)->str:
        msgKeys = req.split()
        if not self.verify_wrk_msg(msgKeys):
            return STATUS.NOT_ALLOWED
        if msgKeys[0] == 'reg':
            wid, wip, wp = msgKeys[1], msgKeys[2], msgKeys[3]
            return self.register_worker(wid, wip, wp)
        elif msgKeys[0] == 'rmv':
            wid, wip, wp = msgKeys[1], msgKeys[2], msgKeys[3]
            return self.remove_worker(wid, wip, wp)
        elif msgKeys[0] == 'ans':
            jid, ans, wid, shardNo= int(msgKeys[1]), msgKeys[2], int(msgKeys[3]), int(msgKeys[4])
            if self.job.id == jid:
                if self.verifyPassword(ans):
                    self.printf(f"write answer {ans} to job {jid} by {wid}")
                    self.job.answer = ans
                    self.job.solver = wid
                    self.job.solved = True
                    self.job.shard_flags[shardNo] = True
                elif ans == 'NOT_FOUND':
                    self.job.shard_flags[shardNo] = True
                

            return STATUS.OK
        
        return STATUS.NOT_ALLOWED

    def handle_user_req(self, req:str)->str:
        msgKeys = req.split()
        if not self.verify_usr_msg(msgKeys):
            return STATUS.NOT_ALLOWED
        if msgKeys[0] == 'cra':
            md5 = msgKeys[1]
            return self.solve(md5)
        return STATUS.NOT_ALLOWED
    
    def job_summary(self, job:Job)->None:
        self.printf(f"job summary:")
        self.printf(f"\tid:\t[{job.id}]")
        self.printf(f"\tmd5:\t[{job.md5}]")
        self.printf(f"\trange:\t[{job.start}] to [{job.end}]")
        self.printf(f"\tnumof shard:\t[{job.numOfShards}]")
        for i in job.shards:
            self.printf(f"\t\tshard:\t[{i}]")
        
    # async methods
    # dealing with workers
    async def handle_worker(self, reader, writer):
        request = (await reader.read(255)).decode('utf8')
        #self.printf(f"received worker msg[{request}]")
        status = self.handle_worker_req(request)
        response = self.makeMsg(ACTION.ACK, self.id, status)
        #self.printf(f"send response [{response}]")
        writer.write(response.encode('utf8'))
        await writer.drain()
        writer.close()

    async def run_wkr_server(self):
        s = await asyncio.start_server(self.handle_worker, self.ip, self.wkr_port)
        self.wkr_server = s
        self.printf(f"establish worker registration server on {self.ip}:{self.wkr_port}")
        async with s:
            await s.serve_forever()

    async def sendToWorker(self, id, wkrIP, wkrPort, act, payload)->str:
        res = b""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            #self.printf(f"sending to worker{wkrIP}:{wkrPort}")
            s.connect((wkrIP , wkrPort))
            reg_msg = self.makeMsg(act, id, payload)
            await asyncio.sleep(1)
            s.sendall(reg_msg.encode('utf-8'))
            res = b""
            res += s.recv(1024)
        data = res.decode('utf-8')
        #self.printf(f"received data [{data}]")
        if not len(data) == 0:
            return data
        else:
            return "NO_REPLY"

    async def checkWorker(self, wkrID, wkrIP, wkrPort)->bool:
        self.printf(f"check worker status {wkrIP}:{wkrPort}")
        result = await self.sendToWorker(wkrID, wkrIP, wkrPort, ACTION.CHECK, "are you alive?")
        if result != "NO_REPLY":
            return True
        return True


    async def send_shard(self, wkrID, wkrIP, wkrPort, shardNo)->bool:
        if await self.checkWorker(wkrID, wkrIP, wkrPort):
            req = await self.sendToWorker(self.job.id, wkrIP, wkrPort, ACTION.WORK, f"{shardNo} {self.job.md5} {self.job.shards[shardNo][0]} {self.job.shards[shardNo][1]}")
            self.printf(f"Sent {shardNo}th shard [{self.job.shards[shardNo][0]} {self.job.shards[shardNo][1]}] to worker[{wkrID}]")
            self.job.wkr_cnt += 1
            self.job.shard_flags[shardNo] = True
            #reqKeys = req.split()
        else:
            self.remove_worker(wkrID, wkrIP, wkrPort)
        return True

    async def solve(self, md5, start = 0, end = 380204032):
        self.job = self.divdeJob(Job(self.genId(), md5, start,end))
        #self.printf(f"create job with id {job.id}")
        shardNo = 0
        wkrIdx = 0
        solve_tasks = []

        # scan workers
        #self.printf(f"scanning current worker list")
        self.job_summary(self.job)
        shardNo = 0
        for i in self.workerList:
            wkrID, wkrIP, wkrPort = i
            loc_taks = asyncio.create_task(self.send_shard(wkrID, wkrIP, wkrPort, shardNo))
            solve_tasks.append(loc_taks)
            shardNo += 1
        
        for i in solve_tasks:
            await i

        timeout = time.time() + self.compute_time_out//self.numOfWorker
        while time.time() < timeout:
            if self.job.solved == True:
                for j in self.workerList:
                    wkrID, wkrIP, wkrPort = j
                    if int(wkrID) != self.job.solver:
                        await self.sendToWorker(self.job.id, wkrIP, wkrPort, ACTION.INTERRUPT, 'EMPTY')
                        self.printf(f"sent interrupt to worker [{wkrID}]")
                return self.job.answer
            await asyncio.sleep(0.1)
            if len(self.workerList) < 0:
                return 'NO_WORKER'

        untouched_list = []
        for i, flag in enumerate(self.job.shard_flags):
            if flag == False:
                untouched_list.append(self.job.shards[i])
        
        for i in untouched_list:
            locResult =  await self.solve(md5, i[0], i[1])
            if self.job.solved == True:
                for j in self.workerList:
                    wkrID, wkrIP, wkrPort = j
                    if int(wkrID) != self.job.solver:
                        await self.sendToWorker(self.job.id, wkrIP, wkrPort, ACTION.INTERRUPT, 'EMPTY')
                        self.printf(f"sent interrupt to worker [{wkrID}]")
                return self.job.answer
            
        return 'NOT_FOUND'
        
                
    

    # dealing with users
    async def handle_req(self, reader, writer):
        request = None
        request = (await reader.read(255)).decode('utf8')
        self.printf(f"received user msg[{request}]")
        reqKeys = request.split()
        time_before = time.time()
        ans = await self.solve(reqKeys[1])
        time_after = time.time()
        timeSpent = time_after - time_before
        self.printf(f"found answer {ans}, time elapsed [{round(timeSpent)}]")
        response = self.makeMsg(ACTION.ANSWER, self.id, ans)
        writer.write(response.encode('utf8'))
        await writer.drain()
        writer.close()

    async def run_req_server(self):
        s = await asyncio.start_server(self.handle_req, self.ip, self.req_port)
        self.usr_server = s
        self.printf(f"establish requesting handling server on {self.ip}:{self.req_port}")
        async with s:
            await s.serve_forever()
