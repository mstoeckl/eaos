#!/usr/bin/env python3

from tornado.options import options, define, parse_command_line
from tornado import web, websocket
import tornado.ioloop
import tornado.httpserver
import os
from collections import defaultdict

define("port", type=int, default=8888)

template_context = {"pid":os.getpid()}

class ConfigHandler(web.RequestHandler):
    def get(self):
        self.render("static/config", pid=os.getpid())

class StaticTemplateHandler(web.RequestHandler):
    def get(self, path):
        # check real file name:
        # if folder, use 1
        # if js, use other
        print(path)
        self.render("static/index".format(path), **template_context)

class ReceiveHandler(web.RequestHandler):
    def post(self):
        key = self.get_argument("key", "???")
        value = self.get_argument("value", "???")
        print(key, "=>", value)

# todo: convert into engine
pagelist = defaultdict(list)

class Interface():
    def __init__(self, push):
        self.push = push
        # default callback is echo
        self.callback = lambda x:self.push(x[0],x[1])
    def pull(self,callback):
        self.callback = callback

class SocketHandler(websocket.WebSocketHandler):
    path = None
    interface = None
    def write_pair(self, key, val):
        self.write_message("{}={}".format(key, val))
    def on_message(self, message):
        print(message)
        if self.path is None:
            self.path = message
            self.interface = Interface(self.write_pair)
            pagelist[self.path].append(self.interface)
        else:
            for x in pagelist[self.path]:
                x.callback(message.split("="))

    def on_close(self):
        pagelist[self.path].remove(self.interface)
    def open(self):
        pass

def main():
    parse_command_line()
    app = web.Application(
    [
        ("/socket", SocketHandler),



        ("/config", ConfigHandler),
        ("/push", ReceiveHandler),
        ("/index", web.ErrorHandler, {"status_code":404}),
        ("/()", StaticTemplateHandler),
        ("/view()", web.StaticFileHandler, {"path":"static/view/index"}),
        ("/input()", web.StaticFileHandler, {"path":"static/input/index"}),


        ("/(.*)", web.StaticFileHandler,  {"path": "static"})
    ])
    server = tornado.httpserver.HTTPServer(app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    import time,signal
    class SingletonScript():
        it = "pid.txt"
        def __enter__(self):
            if os.path.exists(self.it):
                old_pid = int(open(self.it).read())
                #os.kill(old_pid,signal.SIGINT) # does not work??
                os.system("kill -2 {}".format(old_pid))
            open(self.it,"w").write(str(os.getpid()))
            time.sleep(0.5)
        def __exit__(self, _, __, ___):
            os.remove(self.it)

    try:
        with SingletonScript():
            main()
    except KeyboardInterrupt:
        pass

