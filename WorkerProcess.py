import socket
from Worker import Worker
import subprocess

IP = 'localhost'
PORT = 50006
SERVER_IP = 'localhost'
SERVER_PORT = 50002

aWorker = Worker()

aWorker.setIp(IP)
aWorker.setServer(SERVER_IP, SERVER_PORT)

msg = f"reg {aWorker.id} {aWorker.ip} {PORT}"


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((SERVER_IP, SERVER_PORT))
    print("connecting with ", SERVER_IP)
    s.sendall(msg.encode('utf-8'))
    data = b""
    data += s.recv(1024)
    aWorker.printf(f"received data [{data.decode('utf-8')}]")