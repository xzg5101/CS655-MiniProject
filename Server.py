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

    def __init__(self, ip, wkr_port, req_port):
        self.setNumCap()
        self.id = self.genId()
        self.numOfWorker = 0
        self.ip = ip
        self.wkr_port = wkr_port
        self.req_port = req_port
        self.compute_time_out = 17000   # 2 times the rough estimatino of a single machine loop through all strings

    def printf(self, s:str):
        print(f"{datetime.datetime.now()} Server:", s)

    # put a new worker in list
    def register_worker(self, workerID, workerIP, workerPort):
        if [workerID, workerIP, workerPort] in self.workerList:
            return STATUS.DUPLICATED
        self.workerList.append([workerID, workerIP, int(workerPort)])
        self.numOfWorker += 1
        self.printf(f"registered worker with id {workerID} and ip {workerIP}")
        return STATUS.OK
    
    # remove a worker from list
    def remove_worker(self, workerID, workerIP, workerPort):
        if not [workerID, workerIP, workerPort] in self.workerList:
            return STATUS.NOT_FOUND
        self.workerList.remove([workerID, workerIP, workerPort])
        self.numOfWorker -= 1
        self.printf(f"removed worker with id {workerID} and ip {workerIP}")
        return STATUS.OK

    # input a job, divide based on current worker number
    def divide_job(self, job:Job):
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

    # input a request, return the status
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
                    self.printf(f"worker {wid} found nothing in its shard")
                    self.job.shard_flags[shardNo] = True
            return STATUS.OK
        return STATUS.NOT_ALLOWED
    
    # print a job summary
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
        status = self.handle_worker_req(request)
        response = self.makeMsg(ACTION.ACK, self.id, status)
        writer.write(response.encode('utf8'))
        await writer.drain()
        writer.close()

    # start the woker register server
    # this server take care of new register workers
    async def run_wkr_server(self):
        s = await asyncio.start_server(self.handle_worker, self.ip, self.wkr_port)
        self.wkr_server = s
        self.printf(f"establish worker registration server on {self.ip}:{self.wkr_port}")
        async with s:
            await s.serve_forever()

    # send a message to server
    async def send_to_worker(self, id, wkrID, wkrIP, wkrPort, act, payload)->str:
        res = b""
        data = ""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((wkrIP , wkrPort))
            reg_msg = self.makeMsg(act, id, payload)
            await asyncio.sleep(1)
            s.sendall(reg_msg.encode('utf-8'))
            res = b""
            res += s.recv(1024)
            data = res.decode('utf-8')
        except:
             self.remove_worker(wkrID, wkrIP, wkrPort)
        finally:
            s.close()
        if not len(data) == 0:
            return data
        else:
            return "NO_REPLY"

    # check if a worker is alive.  if the worker failed the check, remove the worker
    async def check_worker(self, wkrID, wkrIP, wkrPort)->bool:
        self.printf(f"check worker status {wkrIP}:{wkrPort}")
        result = ""
        status = False
        try:
            result = await self.send_to_worker(wkrID, wkrID, wkrIP, wkrPort, ACTION.CHECK, "are you alive?")
        except:
            self.remove_worker(wkrID, wkrIP, wkrPort)
            self.printf(f"worker is gone {wkrID}, deleted")
            status = False
        
        self.printf(f"worker {wkrID} status {result}")
        status = True
        return status


    # call sent to wkr and send a shard of job to a worker
   
    async def send_shard(self, wkrID, wkrIP, wkrPort, shardNo)->bool:
        if await self.check_worker(wkrID, wkrIP, wkrPort):
            req = await self.send_to_worker(self.job.id, wkrID, wkrIP, wkrPort, ACTION.WORK, f"{shardNo} {self.job.md5} {self.job.shards[shardNo][0]} {self.job.shards[shardNo][1]}")
            self.printf(f"Sent {shardNo}th shard [{self.job.shards[shardNo][0]} {self.job.shards[shardNo][1]}] to worker[{wkrID}]")
            self.job.wkr_cnt += 1

        else:
            self.remove_worker(wkrID, wkrIP, wkrPort)
        return True

    # tell all workers to start the new job. does not return the answer
    async def solve(self, md5, start = 0, end = 380204032):
        self.job = self.divide_job(Job(self.genId(), md5, start,end))
        shardNo = 0
        wkrIdx = 0
        solve_tasks = []

        self.job_summary(self.job)
        shardNo = 0
        for i in self.workerList:
            wkrID, wkrIP, wkrPort = i
            loc_taks = asyncio.create_task(self.send_shard(wkrID, wkrIP, wkrPort, shardNo))
            solve_tasks.append(loc_taks)
            shardNo += 1
        
        for i in solve_tasks:
            await i

    # send a interrupt signal to all slow bird
    async def stop_workers(self)->None:
        for j in self.workerList:
            wkrID, wkrIP, wkrPort = j
            if self.job != None and int(wkrID) == self.job.solver:
                continue
            await self.send_to_worker(self.job.id, wkrID, wkrIP, wkrPort, ACTION.INTERRUPT, 'EMPTY')
            self.printf(f"sent interrupt to worker [{wkrID}]")
    
    # call this to solve a MD5. Return the answer
    async def get_answer(self, md5:str, start = 0, end = 380204032)->str:
        self.job = None
        solve_task = asyncio.create_task(self.solve(md5, start, end))
        solve_task
        timeout = time.time() + self.compute_time_out//self.numOfWorker
        while time.time() < timeout:
            if self.job != None:
                if self.job.solved == True:
                    final_answer = self.job.answer
                    stop_task = asyncio.create_task(self.stop_workers())
                    stop_task
                    return final_answer
                if self.job.scanned():
                    self.printf(f"all scanned")
                    return 'NOT_FOUND'
            await asyncio.sleep(0.1)

        # if some worker dead in progress of working 
        shard_flags = self.job.shard_flags
        shards = self.job.shards
        for i, flag in enumerate(shard_flags):
            if flag == False:
                result = await self.get_answer(md5, shards[i][0], shards[i][1])
                if self.verifyPassword(result):
                    stop_task = asyncio.create_task(self.stop_workers())
                    stop_task
                    return result

        stop_task = asyncio.create_task(self.stop_workers())
        stop_task
        return 'NOT_FOUND'


    # dealing with users
    async def handle_req(self, reader, writer):
        request = None
        request = (await reader.read(255)).decode('utf8')
        self.printf(f"received user msg[{request}]")
        reqKeys = request.split()
        time_before = time.time()
        ans = await self.get_answer(reqKeys[1])
        time_after = time.time()
        timeSpent = time_after - time_before
        self.printf(f"found answer {ans}, time elapsed [{round(timeSpent)}]")
        response = self.makeMsg(ACTION.ANSWER, self.id, f"{ans} {timeSpent}")
        writer.write(response.encode('utf8'))
        await writer.drain()
        writer.close()

    # run a server that accept user requests
    async def run_req_server(self):
        s = await asyncio.start_server(self.handle_req, self.ip, self.req_port)
        self.usr_server = s
        self.printf(f"establish requesting handling server on {self.ip}:{self.req_port}")
        async with s:
            await s.serve_forever()
