import hashlib
from http.server import BaseHTTPRequestHandler
import post
from Server import *


class Resquest(BaseHTTPRequestHandler, Server, Node):
    timeout = 5
    server_version = "Apache"  # 设置服务器返回的的响应头

    index_content = '''
    HTTP/ 1.x  200 ok
    Content-Type: text/html
    '''

    file = open('index.html', 'r')
    content = file.read()
    file.close()

    # def __init__(self, server, *args):
    #     self.server = server
    #     BaseHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")  # 设置服务器响应头
        self.send_header("test1", "This is test!")  # 设置服务器响应头
        self.end_headers()
        self.wfile.write(self.content.encode())  # 里面需要传入二进制数据，用encode()函数转换为二进制数据   #设置响应body，即前端页面要展示的数据

    def do_POST(self):
        # 获取post提交的数据
        datas = self.rfile.read(int(self.headers['content-length']))  # 固定格式，获取表单提交的数据
        # datas = urllib.unquote(datas).decode("utf-8", 'ignore')

        self.send_response(200)
        self.send_header("Content-type", "text/html")  # 设置post时服务器的响应头
        self.send_header("test", "This is post!")
        self.end_headers()


        values = str(datas).split("&")
        md5 = values[0].split("=")[-1]
        worker = values[1].split("=")[-1]
        hashMD5 = hashlib.md5(md5.encode()).hexdigest()
        res = Server().test(hashMD5)
        # postCon = post.writeFile(md5, hashMD5, worker)
        postCon = post.writeFile(md5, hashMD5, res)
        self.wfile.write(postCon.encode())  # 提交post数据时，服务器跳转并展示的页面内容

# if __name__ == '__main__':
#     host = ('localhost', 8888)
#     server = Server()
#     # rqst = Resquest(server)
#     server = HTTPServer(host, Resquest)
#     print("Starting server, listen at: %s:%s" % host)
#     server.serve_forever()