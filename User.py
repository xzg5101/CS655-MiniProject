import hashlib
import socket
from Worker import Worker
import re

IP = 'localhost'
PORT = 50010
SERVER_IP = 'localhost'
SERVER_PORT = 50003

aWorker = Worker()

aWorker.setIp(IP)
aWorker.setServer(SERVER_IP, SERVER_PORT)

aStr = 'ABCDE'
locMd5 = hashlib.md5(aStr.encode()).hexdigest()

msg = f"cra {locMd5}"

def query():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, SERVER_PORT))
    print("connecting with ", SERVER_IP)
    s.sendall(msg.encode('utf-8'))
    data = b""
    data += s.recv(1024)
    ans = data.decode().split()
    print(f"received result [{ans[2]}], is it correct?", ans[2] == aStr)

query()