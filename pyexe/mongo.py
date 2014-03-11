#!/usr/bin/env python3

import sys
import os
from pprint import pprint
import subprocess
import datetime
import argparse

try:
  # pymongo 2.4+
  from pymongo.mongo_client import MongoClient
except ImportError:
  from pymongo import Connection as MongoClient
import pymongo.cursor

from cli import repl

host = 'localhost'
port = 27017
db = 'test'

import locale
locale.setlocale(locale.LC_ALL, '')
del locale

env = os.environ.copy()
if env['TERM'].find('256') != -1:
  env['TERM'] = env['TERM'].split('-', 1)[0]

def displayfunc(value):
  if value is None:
    v['_'] = None
    return

  if isinstance(value, pymongo.cursor.Cursor):
    p = subprocess.Popen(['colorless', '-l', 'python'], stdin=subprocess.PIPE,
                        universal_newlines=True, env=env)
    value = list(value)
    pprint(value, stream=p.stdin)
    p.stdin.close()
    p.wait()
  else:
    pprint(value)
  v['_'] = value

def main(kwargs):
  global db, conn
  conn = MongoClient(host=host, port=port, **kwargs)
  db = conn[db]

  rc = os.path.expanduser('~/.mongorc.py')
  if os.path.isfile(rc):
    exec(compile(open(rc, 'rb').read(), '.mongorc.py', 'exec'))

  global v
  v = globals().copy()
  v.update(locals())
  v['_'] = None
  del v['repl'], v['kwargs'], v['main'], v['host'], v['port']
  del v['displayfunc'], v['subprocess'], v['env']
  del v['__name__'], v['__cached__'], v['__doc__'], v['__file__'], v['__package__']
  del v['rc'], v['argparse']
  sys.displayhook = displayfunc

  repl(
    v, os.path.expanduser('~/.mongo_history'),
    banner = 'Python MongoDB console',
  )

if __name__ == '__main__':
  try:
    import setproctitle
    setproctitle.setproctitle('mongo.py')
    del setproctitle
  except ImportError:
    pass

  parser = argparse.ArgumentParser(description='MongoDB Shell in Python')
  parser.add_argument('--slaveok', action='store_true')
  parser.add_argument('dburl', nargs='?', default=None,
                      help='the database to use instead of localhost\'s test')
  args = parser.parse_args()

  kwargs = {}
  if args.dburl:
    dburl = args.dburl
    if '/' in dburl:
      host, db = dburl.split('/', 1)
      if ':' in host:
        host, port = host.split(':', 1)
        port = int(port)
    else:
      db = dburl
  if args.slaveok:
    kwargs['slave_okay'] = True

  main(kwargs)
