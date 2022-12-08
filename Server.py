import datetime
import math
import asyncio
import socket
from Node import Node
from StatusCode import STATUS
from Action import ACTION
from Job import Job
from http.server import HTTPServer, CGIHTTPRequestHandler
import sys
import time


class Server(Node):
    numOfWorker = None  # number of workers
    workerList = []
    jobList = []  # list of list

    reg_port = None  # int
    req_port = None  # int

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

    def printf(self, s: str):
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

    def divdeJob(self, job: Job):
        # no workers
        if self.numOfWorker == 0:
            return job

        # compute job ranges
        jobWidth = math.ceil((job.end - job.start) / self.numOfWorker)
        shards = []
        base = job.start
        for i in range(self.numOfWorker):
            shards.append([base, min(base + jobWidth, job.end)])
            base += jobWidth
        job.shards = shards
        return job

    def handle_worker_req(self, req: str) -> str:
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
            wid, ans = msgKeys[1], msgKeys[2]
            return STATUS.OK

        return STATUS.NOT_ALLOWED

    def handle_user_req(self, req: str) -> str:
        msgKeys = req.split()
        if not self.verify_usr_msg(msgKeys):
            return STATUS.NOT_ALLOWED
        if msgKeys[0] == 'cra':
            md5 = msgKeys[1]
            return self.solve(md5)
        return STATUS.NOT_ALLOWED

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

    async def sendToWorker(self, id, wkrIP, wkrPort, act, payload) -> str:
        res = b""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.printf(f"sending to worker{wkrIP}:{wkrPort}")
            s.connect((wkrIP, wkrPort))
            reg_msg = self.makeMsg(act, id, payload)
            s.sendall(reg_msg.encode('utf-8'))
            res = b""
            res += s.recv(1024)
        data = res.decode('utf-8')
        self.printf(f"received data [{data}]")
        if not len(data) == 0:
            return data
        else:
            return "NO_REPLY"

    async def checkWorker(self, wkrID, wkrIP, wkrPort) -> bool:
        result = await self.sendToWorker(wkrID, wkrIP, wkrPort, ACTION.CHECK, "are you alive?")
        if result != "NO_REPLY":
            return True
        return True

    async def sendShard(self, wkrID, wkrIP, wkrPort, jobId, shardNo, md5, start, end) -> str:
        result = await self.sendToWorker(jobId, wkrIP, wkrPort, ACTION.WORK, f"{shardNo} {md5} {start} {end}")
        return result

    async def solve(self, md5):
        job = self.divdeJob(Job(self.genId(), md5, 0, self.numCap))
        self.printf(f"create job with id {job.id}")
        self.printf(f"scanning current worker list")
        shardNo = 0
        wkrIdx = 0
        while shardNo < len(job.shards) and len(self.workerList) > 0:
            self.printf(f"Checking worker {self.workerList[wkrIdx]}")
            wkrID, wkrIP, wkrPort = self.workerList[wkrIdx]
            if await self.checkWorker(wkrID, wkrIP, wkrPort):
                self.printf(f"find alive worker [{wkrID}]")
                self.printf(
                    f"job shard summary: {wkrID} {wkrIP}, {wkrPort}, {job.id}, {shardNo}, {md5}, {job.shards[shardNo][0]}, {job.shards[shardNo][1]}")
                req = await self.sendShard(wkrID, wkrIP, wkrPort, job.id, shardNo, md5, job.shards[shardNo][0],
                                           job.shards[shardNo][1])
                reqKeys = req.split()
                if reqKeys[4] != 'NOT_FOUND':
                    return reqKeys[4]
                shardNo += 1
            else:
                self.remove_worker(wkrID, wkrIP, wkrPort)
            wkrIdx = (wkrIdx + 1) % len(self.workerList)
        return 'NOT_FOUND'

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

        # http_server

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

    async def run_req_server(self):
        server_class = HTTPServer
        handler_class = CGIHTTPRequestHandler

        s = await server_class((self.ip, self.req_port), handler_class)
        self.printf(f"establish requesting handling server on {self.ip}:{self.req_port}")
        async with s:
            try:
                s.serve_forever()
            except KeyboardInterrupt:
                print("Keyboard interrupt closing requesting handling server.")
                sys.exit(0)
