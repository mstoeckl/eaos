#!/usr/bin/env python3

from tornado.options import options, define, parse_command_line
from tornado import web
import tornado.ioloop
import tornado.httpserver
import os

define("port", type=int, default=8078)

class ConfigHandler(web.RequestHandler):
    def get(self):
        self.render("static/config", pid=os.getpid())

def main():
    parse_command_line()
    app = web.Application(
    [
        # TODO: produce a "folderhandler" that filters out the index path,
        # and links the /view index properly
        ("/config", ConfigHandler),
        ("/()", web.StaticFileHandler, {"path":"static/index"}),
        ("/view()", web.StaticFileHandler, {"path":"static/view/index"}),
        ("/input()", web.StaticFileHandler, {"path":"static/input/index"}),
        ("/index", web.ErrorHandler, {"status_code":404}),
        ("/(.*)", web.StaticFileHandler, {"path": "static"})
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

