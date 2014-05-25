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
define("lump", type=bool, default=False)
define("dead", type=bool, default=False)
define("year", type=int, default=2014)

template_context = {"pid": os.getpid()}

pass_map = {
    "config",
    "input/schedule",
    "input/match",
    "input/pits",
    "input/actions",
    "view/stats"
}

number_pages = {
    "view/match",
    "view/robot"
}

re_map = {
    "": "index",
    "view": "view/index",
    "input": "input/index",
}


class TemplateHandler(web.RequestHandler):

    def get(self, path):
        self.set_header(
            "Cache-control", "no-store, no-cache, must-revalidate, max-age=0")
        for key in number_pages:
            if path == key:
                self.render(
                    "static/{}-index.html".format(path), **template_context)
            if path.startswith(key + "/"):
                u = path.lstrip(key + "/")
                if SocketHandler.engine.page_exists("/" + key, u):
                    self.render(
                        "static/{}.html".format(key), page=u, **template_context)
                    return
                raise web.HTTPError(404)

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
                print("\033[1;35m[Pull]\033[0m Page \"{}\"; Key \"{}\"; Value \"{}\"".format(
                    self.path, key, val))
            SocketHandler.engine.receive(self.path, key, val)

    def on_close(self):
        SocketHandler.connections[self.path].remove(self)

    @staticmethod
    def send(page, key, val):
        if options.loud:
            print("\033[1;33m[Push]\033[0m Page \"{}\"; Key \"{}\"; Value \"{}\"".format(
                page, key, val))

        if page in SocketHandler.connections:
            for x in SocketHandler.connections[page]:
                x.write_pair(key, val)


class Accelerator():

    def __init__(self, lump, dead):
        if dead:
            self.none()
        else:
            if lump:
                self.lumped()
            else:
                self.split()

    def split(self):
        self.stylesheet = "<link rel='stylesheet' href='/theme.css'>"
        self.pushpull = "<script src='/js/pushpull.js'></script>"
        self.auto = "<script src='/js/auto.js'></script>"

    def open(self, path):
        with open("static" + path) as f:
            return f.read()

    def taglock(self, tag, path):
        return "<{0}>{1}</{0}>".format(tag, self.open(path))

    def lumped(self):
        self.stylesheet = self.taglock("style", "/theme.css")
        self.pushpull = self.taglock("script", "/js/pushpull.js")
        self.auto = self.taglock("script", "/js/auto.js")

    def none(self):
        self.stylesheet = ""
        self.pushpull = "<script>push=pull=unpull=function(){}</script>"
        self.auto = ""


def main():
    engine = Engine(options.year, options.datadir, SocketHandler.send)
    template_context["engine"] = engine
    SocketHandler.engine = engine
    template_context["accel"] = Accelerator(options.lump, options.dead)

    app = web.Application([
        ("/socket", SocketHandler),
        ("/(favicon.ico)", web.StaticFileHandler,  {"path": "static"}),
        ("/(.*\.js)", web.StaticFileHandler,  {"path": "static"}),
        ("/(theme.css)", web.StaticFileHandler,  {"path": "static"}),
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
                # os.kill(old_pid,signal.SIGINT) # does not work??
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
