#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

import uvicorn
from _bareasgi import Application, Static

from engine import message
from util import realpath

app = Application()
#app.http_router.add({'GET'}, '/knowledge', knowledge)
app.http_router.add({'POST'}, '/message', message)

Static(app, realpath('static'), index_filename='index.html')

port = int(os.getenv('PORT', '80'))
uvicorn.run(app, host='0.0.0.0', port=port, loop='asyncio')
