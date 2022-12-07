import datetime
import math
import asyncio
import socket
from Node import Node 
from StatusCode import STATUS
from Action import ACTION
from Job import Job
class Server(Node):
    numOfWorker = None  # number of workers
    workerList = []
    jobList = []        # list of list

    reg_port = None     # int
    req_port = None     # int

    wkr_server = None
    usr_server = None

    writer_list = None

    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.numOfWorker = 0
        self.ip = 'localhost'
        self.wkr_port = 50002
        self.req_port = 50003
        self.writer_list = []

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
        base = job.start
        for i in range(self.numOfWorker):
            shards.append([base, min(base+jobWidth, job.end)])
            base += jobWidth
        job.numOfShards = len(shards)
        job.shards = shards
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
            jid, ans, wid = int(msgKeys[1]), msgKeys[2], int(msgKeys[3])
            for i in self.jobList:
                if i.id == jid:
                    self.printf(f"write answer {ans} to job {jid} by {wid}")
                    i.answer = ans
                    i.solver = wid
                    break
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
        self.printf(f"\t id:[{job.id}]")
        self.printf(f"\t md5:[{job.md5}]")
        self.printf(f"\t range: [{job.start}] to [{job.end}]")
        self.printf(f"\t number of shard:[{job.numOfShards}]")
        for i in job.shards:
            self.printf(f"\t\t shard:[{i}]")
        
        pass
    # async methods
    # dealing with workers
    async def handle_worker(self, reader, writer):
        request = (await reader.read(255)).decode('utf8')
        self.printf(f"received worker msg[{request}]")
        status = self.handle_worker_req(request)
        response = self.makeMsg(ACTION.ACK, self.id, status)
        self.printf(f"send response [{response}]")
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
            self.printf(f"sending to worker{wkrIP}:{wkrPort}")
            s.connect((wkrIP , wkrPort))
            reg_msg = self.makeMsg(act, id, payload)
            await asyncio.sleep(1)
            s.sendall(reg_msg.encode('utf-8'))
            res = b""
            res += s.recv(1024)
        data = res.decode('utf-8')
        self.printf(f"received data [{data}]")
        if not len(data) == 0:
            return data
        else:
            return "NO_REPLY"

    async def checkWorker(self, wkrID, wkrIP, wkrPort)->bool:
        result = await self.sendToWorker(wkrID, wkrIP, wkrPort, ACTION.CHECK, "are you alive?")
        if result != "NO_REPLY":
            return True
        return True

    async def solve_single_thread(self, md5):
        job = self.divdeJob(Job(self.genId(), md5, 0, self.numCap))
        self.printf(f"create job with id {job.id}")
        self.printf(f"scanning current worker list")
        shardNo = 0
        wkrIdx = 0
        while shardNo < len(job.shards) and len(self.workerList) > 0:
            self.printf(f"Checking worker {self.workerList[wkrIdx]}")
            wkrID, wkrIP, wkrPort = self.workerList[wkrIdx]
            result = await self.send_shard(wkrID, wkrIP, wkrPort, job.id, shardNo, md5, job.shards[shardNo][0], job.shards[shardNo][1])
            if result != 'NOT_FOUND':
                return result
            wkrIdx = (wkrIdx + 1)%len(self.workerList)
            shardNo += 1
        return 'NOT_FOUND'


    async def send_shard(self, wkrID, wkrIP, wkrPort, jobId, shardNo, md5, start, end)->bool:
        if await self.checkWorker(wkrID, wkrIP, wkrPort):
            self.printf(f"Sending shard [{start}, {end}] to worker[{wkrID}]")
            req = await self.sendToWorker(jobId, wkrIP, wkrPort, ACTION.WORK, f"{shardNo} {md5} {start} {end}")
            #reqKeys = req.split()
        return True

    # job.shards[shardNo][0], job.shards[shardNo][1]
    async def solve(self, md5):
        job = self.divdeJob(Job(self.genId(), md5, 0, self.numCap))
        self.printf(f"create job with id {job.id}")
        self.printf(f"scanning current worker list")
        self.jobList.append(job)
        shardNo = 0
        wkrIdx = 0
        solve_tasks = []

        self.job_summary(job)
        shardNo = 0
        for i in self.workerList:
            wkrID, wkrIP, wkrPort = i
            loc_taks = asyncio.create_task(self.send_shard(wkrID, wkrIP, wkrPort, job.id, shardNo, md5, job.shards[shardNo][0], job.shards[shardNo][1]))
            solve_tasks.append(loc_taks)
            shardNo += 1
        #rst_list = await asyncio.gather(*solve_tasks)
        for i in solve_tasks:
            await i
            
        while True:
            for i in self.jobList:
                if i.id == job.id:
                    if i.answer != None:
                        for j in self.workerList:
                            wkrID, wkrIP, wkrPort = j
                            self.printf(f"solver id {i.solver} this id {wkrID}, send interrupt?")
                            if wkrID != i.solver:
                                await self.sendToWorker(i.id,wkrIP, wkrPort, ACTION.INTERRUPT, 'EMPTY')
                        return i.answer
                await asyncio.sleep(0.1)
        #return 'NOT_FOUND'

    

    # dealing with users
    async def handle_req(self, reader, writer):
        request = None
        request = (await reader.read(255)).decode('utf8')
        self.printf(f"received user msg[{request}]")
        reqKeys = request.split()
        ans = await self.solve(reqKeys[1])
        response = self.makeMsg(ACTION.ANSWER, self.id, ans)
        self.printf(f"send response [{response}]")
        writer.write(response.encode('utf8'))
        await writer.drain()
        self.writer_list.append(writer)
        writer.close()

    async def run_req_server(self):
        s = await asyncio.start_server(self.handle_req, self.ip, self.req_port)
        self.usr_server = s
        self.printf(f"establish requesting handling server on {self.ip}:{self.req_port}")
        async with s:
            await s.serve_forever()
