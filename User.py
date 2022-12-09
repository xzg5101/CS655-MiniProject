import hashlib
import socket
from Environment import DEBUG, SERVER_IP, REQUEST_PORT
from Worker import Worker
from Node import Node
import time

IP = '127.0.0.1'
PORT = 50010
serverIP = SERVER_IP

# Test code for the program. Not part of the fucntional code
# remove this file does not influence the function

if DEBUG == 1:
    serverIP = '127.0.0.1'

aNode = Node()

print("Please enter a string of length 5 only contains [a-zA-Z]:")
aInput = input()

while not aNode.verifyPassword(aInput):
    print(f"Input format is wrong [{aInput}], please re-enter")
    aInput = input()

locMd5 = hashlib.md5(aInput.encode()).hexdigest()

msg = f"cra {locMd5}"

def query():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serverIP, REQUEST_PORT))
    print("connecting with ", SERVER_IP)

    time1 = time.time()
    s.sendall(msg.encode('utf-8'))
    data = b""
    data += s.recv(1024)
    time2 = time.time()
    ans = data.decode().split()
    print(f"received result [{ans[2]}], is it correct?", ans[2] == aInput)
    print(f"Server spent [{ans[3]}] seconds, user waited [{time2-time1}] seconds")

query()