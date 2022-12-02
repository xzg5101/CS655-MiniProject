
import sys
import socket
import asyncio
from Server import Server

SERVER_IP = "127.0.0.1" #"10.10.1.1"
SERVER_REG_PORT = 27400
SERVER_REQ_PORT = 27502

aServer = Server()


async def handle_worker(reader, writer):
    request = None
    while request != 'quit':
        request = (await reader.read(255)).decode('utf8')
        response = str(eval(request)) + '\n'
        writer.write(response.encode('utf8'))
        await writer.drain()
    writer.close()

async def run_reg_server():
    s = await asyncio.start_server(handle_worker, 'localhost', SERVER_REG_PORT)
    print("establish async worker registration server on port ", SERVER_REG_PORT)
    async with s:
        await s.serve_forever()

async def handle_req(reader, writer):
    request = None
    while request != 'quit':
        request = (await reader.read(255)).decode('utf8')
        response = str(eval(request)) + '\n'
        writer.write(response.encode('utf8'))
        await writer.drain()
    writer.close()

async def run_req_server():
    s = await asyncio.start_server(handle_req, 'localhost', SERVER_REQ_PORT)
    print("establish async requesting handling server on port ", SERVER_REQ_PORT)
    async with s:
        await s.serve_forever()

loop = asyncio.get_event_loop()

loop.create_task(run_reg_server())
loop.create_task(run_req_server())
loop.run_forever()