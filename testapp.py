#!/usr/bin/env python
import web
from webtools import *

web.config.debug = True
web.httpserver.runsimple = web.httpserver.runbasic
app = application(globals())

@get("/")
def index():
    return 'Welcome home'

@get("/redirect")
def redirect():
    raise web.seeother("/")

@get("/users/(.*)")
def user_profile(username):
    return 'Hello %s' % username

if __name__ == "__main__":
    app.run()