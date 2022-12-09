import socket
from Worker import Worker
import asyncio
from Environment import DEBUG, SERVER_IP, WORKER_PORT
import subprocess

# run this file to start a user process on a node
# Must have the server running already

IP = '127.0.0.1'
PORT = 50006
servreIP = SERVER_IP
selfIP = '127.0.0.1'

if DEBUG == 1: 
    servreIP = '127.0.0.1'
else:
    selfIP = subprocess.getoutput("hostname -I").split()[0]

aWorker = Worker()

aWorker.setIp(selfIP)
aWorker.setServer(servreIP, WORKER_PORT)
msg = f"reg {aWorker.id} {aWorker.ip} {PORT}"


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.create_task(aWorker.run_service())
loop.create_task(aWorker.reg())
loop.run_forever()
