import socket
from Worker import Worker
import asyncio
from Environment import DEBUG, SERVER_IP, WORKER_PORT

IP = '127.0.0.1'
PORT = 50006
servreIP = SERVER_IP


if DEBUG == 1: 
    servreIP = '127.0.0.1'

aWorker = Worker()

aWorker.setIp(IP)
aWorker.setServer(servreIP, WORKER_PORT)
msg = f"reg {aWorker.id} {aWorker.ip} {PORT}"


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
#loop = asyncio.get_event_loop()
loop.create_task(aWorker.run_service())
loop.create_task(aWorker.reg())
loop.run_forever()
