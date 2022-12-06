import cgi, cgitb
import socket

server_IP = ""
server_port = 10000
interface_IP = ""
interface_port = 10000

print("Content-type: text/html")

print("""
    <head>
    <title>MD5 Cracker</title>
    </head>
    <form method = "post"><br>
    <p>
      <b>Please enter a 5-character password (a-z, A-Z):</b><input type = "text" name = "password"><br><br>
      <b>Please select number of workers (1-8):</b><select name="dropdown">
      <option value=1>1</option>
      <option value=2>2</option>
      <option value=3>3</option>
      <option value=4>4</option>
      <option value=5>5</option>
      <option value=6>6</option>
      <option value=7>7</option>
      <option value=8>8</option>
      </select>
      <input type="submit" value="submit"/>
    </p>
    </form>""")

cgi_form = cgi.FieldStorage()


def run_interface(form, s_ip, s_port, i_ip, i_port):
    password = form.getvalue('password')
    if form.getvalue('dropdown'):
        worker_num = form.getvalue('dropdown')
    else:
        worker_num = None
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((s_ip, s_port))
    s.sendall(f"User password: {password} Number of workers: {worker_num}".encode('utf-8'))
    s.close()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((i_ip, i_port))
    s.listen()
    connection, address = s.accept()
    ans = b""
    while True:
        data = connection.recv(1024)
        if len(data) == 0:
            break
        ans += data
    s.close()
    print(f"User password is: {ans}")
    return ans.decode('utf-8')


if __name__ == '__main__':
    result = run_interface(cgi_form, server_IP, server_port, interface_IP, interface_port)
