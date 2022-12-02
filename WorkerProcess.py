import socket
from Worker import Worker
import subprocess

IP = "127.0.0.1"
PORT = 58044
SERVER_IP = "127.0.0.1"
SERVER_PORT = 27410

aworker = Worker()

aworker.setIp(IP)
aworker.setServer(SERVER_IP, SERVER_PORT)



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((SERVER_IP, SERVER_PORT))
    print("connecting with ", SERVER_IP)
    s.sendall("1+8\n".encode('utf-8'))