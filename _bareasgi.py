import bareasgi as _bareasgi
from bareasgi import *
from bareasgi_static import add_static_file_provider as Static

def json_response(data, status=200, headers={}):
  headers = [] # FIXME
  return _bareasgi.json_response(status, headers, data)

def text_response(text, status=200, headers={}):
  headers = []
  return _bareasgi.text_response(status, headers, text)
