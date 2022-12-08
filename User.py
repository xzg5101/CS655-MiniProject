import hashlib
import socket
from Environment import DEBUG, SERVER_IP, REQUEST_PORT
from Worker import Worker

IP = '127.0.0.1'
PORT = 50010
serverIP = SERVER_IP



if DEBUG == 1:
    serverIP = '127.0.0.1'


aStr = 'AAAAc'
locMd5 = hashlib.md5(aStr.encode()).hexdigest()

msg = f"cra {locMd5}"

def query():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serverIP, REQUEST_PORT))
    print("connecting with ", SERVER_IP)
    s.sendall(msg.encode('utf-8'))
    data = b""
    data += s.recv(1024)
    ans = data.decode().split()
    print(f"received result [{ans[2]}], is it correct?", ans[2] == aStr)
    print(f"spent [{ans[3]}] seconds")

query()