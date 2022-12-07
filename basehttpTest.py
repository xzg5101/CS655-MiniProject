from http.server import BaseHTTPRequestHandler, HTTPServer
import functools


class test:
    def show(self):
        return b"aaaa"

class http_server:
    def __init__(self, t1):
        handler_partial = functools.partial(Handler, t1=t1)
        server = HTTPServer(('', 8080), handler_partial)
        server.serve_forever()

class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, t1=None, **kwargs):
        # Assign before super().__init__ because init is what triggers parsing the request
        self.t1 = t1
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(self.t1.show())
        return

class main:
    def __init__(self):
        self.t1 = test()
        self.server = http_server(self.t1)

if __name__ == '__main__':
    m = main()