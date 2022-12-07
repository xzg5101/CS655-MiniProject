
import asyncio
from Server import Server

aServer = Server()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.create_task(aServer.run_wkr_server())
loop.create_task(aServer.run_req_server())
loop.run_forever()

