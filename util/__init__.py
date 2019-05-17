import os
from platform import python_version_tuple as get_pyversion
from statistics import mean as _mean, StatisticsError


pyversion = tuple(int(e) for e in get_pyversion())
if pyversion >= (3, 6, 0):
  OrderedDict = dict
else:
  from collections import OrderedDict

__dir__ = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')

def realpath(path):
  return os.path.join(__dir__, path)

def new(cls, *args, **kw):
  if not isinstance(cls, type):
    cls = type(cls)
  return cls(*args, **kw)

from .set import Set, OrderedSet
from .list import Tuple, List
from .url import URL
from .priority_queue import PriorityQueue

def attach(target):
  def deco(func):
    setattr(target, func.__name__, func)
    return func
  return deco

def mixin(target):
  exclude = { '__module__', '__dict__', '__weakref__', '__doc__', '__new__' }
  def deco(cls):
    for name, attr in cls.__dict__.items():
      if name in exclude:
        continue
      setattr(target, name, attr)
    return cls
  return deco

from requests import Request, Session
_session = Session()

@mixin(Request)
class _Request:
  def __call__(self, params=None, json=None):
    req = self.prepare()
    if params:
      req.prepare_url(req.url, params)
    if json:
      req.prepare_body(None, self.files, json)
    return _session.send(req)

class Prefix:
  def __init__(self, prefix):
    self.prefix = prefix

  def __contains__(self, item):
    return item.startswith(self.prefix)

  def __str__(self):
    return self.prefix

  def __getitem__(self, item):
    if item in self:
      return self.prefix
    return item

def mean(data, default=None):
  try:
    return _mean(data)
  except StatisticsError:
    return default

def casefold(self):
  return str(self).casefold()
