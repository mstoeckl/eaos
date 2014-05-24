#!/usr/bin/env python3

import os
from tornado.options import options, define, parse_command_line
from tornado import web, websocket
import tornado.ioloop
import tornado.httpserver
from collections import defaultdict
from engine import Engine

define("port", type=int, default=8888)
define("datadir", type=str, default="data")
define("loud", type=bool, default=False)

template_context = {"pid": os.getpid()}

pass_map = {
    "config",
    "input/schedule",
    "input/match",
    "input/pits",
    "input/actions",
    "view/match",
    "view/robot",
    "view/stats"
}

re_map = {
    "": "index",
    "view": "view/index",
    "input": "input/index",
}


class TemplateHandler(web.RequestHandler):
    def get(self, path):
        if path in pass_map:
            real = path
        else:
            try:
                real = re_map[path]
            except KeyError:
                raise web.HTTPError(404)

        self.render("static/{}.html".format(real), **template_context)


class SocketHandler(websocket.WebSocketHandler):
    """
    Passes incoming messages to the engine, and
    echos them back to all source page types

    Sends messages from the engine out to pages.
    """
    connections = defaultdict(list)
    engine = None

    def __init__(self, *a, **b):
        self.path = None
        super().__init__(*a, **b)

    def write_pair(self, key, val):
        self.write_message("{}={}".format(key, val))

    def on_message(self, message):
        if self.path is None:
            self.path = message
            SocketHandler.connections[self.path].append(self)
        else:
            key, val = message.split("=")
            SocketHandler.send(self.path, key, val)
            if options.loud:
                print("\033[1;35m[Pull]\033[0m Page \"{}\"; Key \"{}\"; Value \"{}\"".format(self.path,key,val))
            SocketHandler.engine.receive(self.path, key, val)

    def on_close(self):
        SocketHandler.connections[self.path].remove(self)

    @staticmethod
    def send(page, key, val):
        if options.loud:
            print("\033[1;33m[Push]\033[0m Page \"{}\"; Key \"{}\"; Value \"{}\"".format(page,key,val))

        if page in SocketHandler.connections:
            for x in SocketHandler.connections[page]:
                x.write_pair(key, val)

def main():
    engine = Engine(options.datadir, SocketHandler.send)
    template_context["engine"] = engine
    SocketHandler.engine = engine

    app = web.Application([
        ("/socket", SocketHandler),
        ("/(favicon.ico)", web.StaticFileHandler,  {"path": "static"}),
        ("/(.*\.js)", web.StaticFileHandler,  {"path": "static"}),
        ("/(.*\.css)", web.StaticFileHandler,  {"path": "static"}),
        ("/(.*)", TemplateHandler)
    ], autoescape=None)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    parse_command_line()

    import time
    import signal

    class SingletonScript():
        # a slightly cleaner solution:
        # have all processes rename themselves...
        it = "pid.txt"

        def __enter__(self):
            # go to python script location
            if os.path.exists(self.it):
                old_pid = int(open(self.it).read())
                #os.kill(old_pid,signal.SIGINT) # does not work??
                os.system("kill -2 {}".format(old_pid))
            open(self.it, "w").write(str(os.getpid()))
            time.sleep(0.5)

        def __exit__(self, _, __, ___):
            os.remove(self.it)

    try:
        with SingletonScript():
            main()
    except KeyboardInterrupt:
        pass
