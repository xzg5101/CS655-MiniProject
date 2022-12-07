import socket
import subprocess
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


print("socket return", get_ip_address())

print("subprocess return", subprocess.getoutput("hostname -I").split()[0])