import socket
from Worker import Worker
import asyncio
from Environment import DEBUG

IP = '127.0.0.1'
PORT = 50006
SERVER_IP = '172.17.1.15'
SERVER_PORT = 50002


if DEBUG == 1:
    IP = 'localhost'
    PORT = 50006
    SERVER_IP = 'localhost'
    SERVER_PORT = 50002

aWorker = Worker()

aWorker.setIp(IP)
aWorker.setServer(SERVER_IP, SERVER_PORT)
msg = f"reg {aWorker.id} {aWorker.ip} {PORT}"


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
#loop = asyncio.get_event_loop()
loop.create_task(aWorker.run_service())
loop.create_task(aWorker.reg())
loop.run_forever()
