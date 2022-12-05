import datetime
import math
import asyncio
from Node import Node 
from StatusCode import STATUS
from Action import ACTION
class Server(Node):
    numOfWorker = None  # number of workers
    workerList = []
    jobList = []        # list of list

    reg_port = None     # int
    req_port = None     # int

    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.numOfWorker = 0
        self.ip = 'localhost'
        self.wkr_port = 50002
        self.req_port = 50003

    def printf(self, s:str):
        print(f"{datetime.datetime.now()} Server:", s)

    def register_worker(self, workerID, workerIP, workerPort):
        if any(workerID in worker for worker in self.workerList):
            return STATUS.DUPLICATED
        self.workerList.append([workerID, workerIP, workerPort])
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

    def divdeJob(self):
        # no workers
        if self.numOfWorker == 0:
            return
        
        # compute job ranges
        jobWidth = math.ceil(self.numCap/self.numOfWorker)
        base = 0
        for i in range(self.numOfWorker):
            self.jobList.append([base, min(base+jobWidth, self.numCap)])
            base += jobWidth
    

    def handle_worker_req(self, req:str)->str:
        msgKeys = req.split()
        if not self.verify_msg(msgKeys):
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
        else:
            return STATUS.NOT_ALLOWED

    # async methods
    #
    async def handle_worker(self, reader, writer):

        request = (await reader.read(255)).decode('utf8')
        self.printf(f"received [{request}]")
        status = self.handle_worker_req(request)
        response = self.makeMsg(ACTION.ACK, self.id, status)
        self.printf(f"send response [{response}]")
        writer.write(response.encode('utf8'))
        await writer.drain()
        writer.close()

    async def run_wkr_server(self):
        s = await asyncio.start_server(self.handle_worker, self.ip, self.wkr_port)
        self.printf(f"establish worker registration server on {self.ip}:{self.wkr_port}")
        async with s:
            await s.serve_forever()

    async def handle_req(self, reader, writer):
        request = None
        while request != 'quit':
            request = (await reader.read(255)).decode('utf8')
            response = str(eval(request)) + '\n'
            writer.write(response.encode('utf8'))
            await writer.drain()
        writer.close()

    async def run_req_server(self):
        s = await asyncio.start_server(self.handle_req, self.ip, self.req_port)
        self.printf(f"establish requesting handling server on {self.ip}:{self.req_port}")
        async with s:
            await s.serve_forever()
