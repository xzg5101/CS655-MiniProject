
import asyncio
from Server import Server
from Environment import DEBUG, SERVER_IP, REQUEST_PORT, WORKER_PORT

# run this file to start a user process on a node
# Must run before all worker nodes

serverIP = SERVER_IP

if DEBUG == 1:
    serverIP = '127.0.0.1'

aServer = Server(serverIP, WORKER_PORT, REQUEST_PORT)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.create_task(aServer.run_wkr_server())
loop.create_task(aServer.run_req_server())
loop.run_forever()

