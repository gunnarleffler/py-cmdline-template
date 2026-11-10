#!/usr/bin/env python3
"""A small CLI template: file/stdin input and stderr logging."""

import argparse
import csv
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import tomllib
from contextlib import ExitStack, closing, contextmanager
from functools import reduce
from pathlib import Path

import requests
import yaml
from dateutil import parser as dateparser
from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
config_dir = current_dir.parent / 'config'


def loadConfig(path=None):
  """Load .env explicitly; existing environment variables take precedence."""
  load_dotenv(path or current_dir / '.env')
  return {'db_user': os.getenv('DB_USER')}


# Configuration: CLI value > environment > default (call loadConfig separately).
def configValue(cli_value, env_name, default=None):
  """Return a value; environment values remain strings for caller conversion."""
  return cli_value if cli_value is not None else os.getenv(env_name, default)


def readTOML(path):
  with open(path, 'rb') as source:
    return tomllib.load(source)


# Filesystem and subprocess recipes
@contextmanager
def atomicWriter(path, *, binary=False):
  """Replace a file only on success; parent directory must already exist.

  Uses a sibling temp file. Replacement adopts its permissions, not the original's.
  """
  path = Path(path)
  options = {} if binary else {'encoding': 'utf-8', 'newline': ''}
  with tempfile.NamedTemporaryFile(
    mode='wb' if binary else 'w', dir=path.parent, delete=False, **options
  ) as target:
    temporary = Path(target.name)
    try:
      yield target
      target.close()  # Close before replacement, including on Windows.
      temporary.replace(path)
    finally:
      target.close()
      temporary.unlink(missing_ok=True)


def atomicWrite(path, text):
  with atomicWriter(path) as target:
    target.write(text)


def findFiles(directory, pattern='*', *, recursive=False):
  """Yield matching files as Paths; filesystem errors propagate."""
  root = Path(directory)
  matches = root.rglob(pattern) if recursive else root.glob(pattern)
  return (path for path in matches if path.is_file())


def runCommand(command, *, timeout=30, cwd=None):
  """Return CompletedProcess with stdout/stderr; raise on failure or timeout.

  Pass an argument list, e.g. ['git', 'status', '--short']; never shell syntax.
  """
  if isinstance(command, (str, bytes)):
    raise TypeError('Pass a list of arguments, not a shell command string')
  return subprocess.run(
    command, capture_output=True, text=True, check=True, timeout=timeout, cwd=cwd
  )


# File helpers
def readFile(path):
  return Path(path).read_text(encoding='utf-8')


def readCSV(path):
  with open(path, encoding='utf-8', newline='') as source:
    return list(csv.reader(source))


def readCSVdict(path):
  with open(path, encoding='utf-8', newline='') as source:
    return list(csv.DictReader(source))


def writeCSVdict(data, path):
  if not data:
    raise ValueError('At least one row is needed to determine CSV columns')
  with open(path, 'w', encoding='utf-8', newline='') as target:
    writer = csv.DictWriter(target, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)


def readJSON(path):
  with open(path, encoding='utf-8') as source:
    return json.load(source)


# Ordinary dictionaries preserve insertion order in modern Python.
readOrderedJSON = readJSON


def writePrettyJSON(data, path):
  with open(path, 'w', encoding='utf-8') as target:
    json.dump(data, target, sort_keys=True, indent=2, ensure_ascii=False)
    target.write('\n')


def readYAML(path):
  with open(path, encoding='utf-8') as source:
    return yaml.safe_load(source)


def writeYAML(data, path):
  with open(path, 'w', encoding='utf-8') as target:
    yaml.safe_dump(data, target, allow_unicode=True, default_flow_style=False)


# SQLite helpers: caller creates the COMMENTS table and supplies a database path.
def _columns(names):
  names = list(names)
  if not names or any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', n) for n in names):
    raise ValueError('Expected simple SQL column names')
  return ','.join(f'"{name}"' for name in names)


def writeToDB(fdata, dbpath):
  columns = _columns(fdata)
  placeholders = ','.join('?' for _ in fdata)
  with closing(sqlite3.connect(dbpath)) as connection, connection:
    connection.execute(
      f'INSERT INTO COMMENTS ({columns}) VALUES ({placeholders})',
      list(fdata.values()),
    )


def getFromDB(fkeys, sortkeys=False, id=None, *, dbpath):
  columns = _columns(sorted(fkeys) if sortkeys else fkeys)
  query = f'SELECT {columns} FROM COMMENTS'
  parameters = ()
  if id is not None:
    query += ' WHERE id = ?'
    parameters = (id,)
  with closing(sqlite3.connect(dbpath)) as connection:
    return connection.execute(query, parameters).fetchall()


# HTTP and date parsing
def getWithRequests(url='https://httpbin.org/post', payload=None):
  """POST example; return the response text and propagate HTTP/network errors."""
  if payload is None:
    payload = {'key1': 'value1', 'key2': 'value2'}
  with requests.post(url, data=payload, timeout=30) as response:
    response.raise_for_status()
    return response.text


def _authHeaders(token_env):
  token = os.environ[token_env] if token_env else None
  return {'Authorization': f'Bearer {token}'} if token else {}


def getJSON(url, params=None, *, token_env=None):
  """GET query parameters; return decoded JSON. Optional env var holds bearer token."""
  with requests.get(
    url, params=params, headers=_authHeaders(token_env), timeout=30
  ) as response:
    response.raise_for_status()
    return response.json()


def postJSON(url, data, *, token_env=None):
  """POST JSON; return decoded JSON. HTTP/network/JSON errors propagate."""
  with requests.post(
    url, json=data, headers=_authHeaders(token_env), timeout=30
  ) as response:
    response.raise_for_status()
    return response.json()


def downloadFile(url, path, *, token_env=None):
  """Stream a download to an atomic output file; return its Path."""
  with requests.get(
    url, headers=_authHeaders(token_env), stream=True, timeout=30
  ) as response:
    response.raise_for_status()
    with atomicWriter(path, binary=True) as target:
      for chunk in response.iter_content(chunk_size=64 * 1024):
        target.write(chunk)
  return Path(path)


def parseDate(value):
  try:
    return dateparser.parse(value, fuzzy=True)
  except ValueError, TypeError, OverflowError:
    return None


# Small language examples
class Shape:
  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.description = 'This shape has not been described yet'
    self.author = 'Nobody has claimed to make this shape yet'

  def area(self):
    return self.x * self.y


def comprehension():
  text = 'Hello 12345 World'
  return {
    'squares': [x**2 for x in range(10)],
    'numbers': [x for x in text if x.isdigit()],
    'letters': [x for x in text if x.isalpha()],
  }


def functional():
  values = [5, 7, 22, 97, 54, 62, 77, 23, 73, 61]
  return {
    'odds': list(filter(lambda x: x % 2 != 0, values)),
    'doubles': list(map(lambda x: x * 2, values)),
    'sum': reduce(lambda x, y: x + y, values),
  }


# Optional subcommand pattern; separate from the default file-processing CLI.
def subcommandParser():
  parser = argparse.ArgumentParser(description='Subcommand recipe')
  commands = parser.add_subparsers(dest='command', required=True)
  listing = commands.add_parser('list', help='List matching files')
  listing.add_argument('directory', type=Path)
  listing.add_argument('--pattern', default='*')
  # args = subcommandParser().parse_args(['list', '.', '--pattern', '*.py'])
  # Dispatch with: if args.command == 'list': ...
  return parser


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('-f', '--filename', type=Path, help='Input file (default: stdin)')
  parser.add_argument(
    '-v', '--verbose', action='store_true', help='Enable debug logging'
  )
  parser.add_argument('-o', '--output', type=Path, help='Output file (default: stdout)')
  parser.add_argument(
    '--dry-run', action='store_true', help='Describe work without writing'
  )
  filters = parser.add_mutually_exclusive_group()
  filters.add_argument(
    '--include',
    action='append',
    default=[],
    metavar='TEXT',
    help='Keep lines containing TEXT; repeat for alternatives',
  )
  filters.add_argument(
    '--exclude',
    action='append',
    default=[],
    metavar='TEXT',
    help='Drop lines containing TEXT; repeat for alternatives',
  )
  args = parser.parse_args(argv)
  if args.filename and args.output and args.filename.resolve() == args.output.resolve():
    parser.error('Input and output must be different files')
  logging.basicConfig(
    level=logging.DEBUG if args.verbose else logging.INFO,
    format='%(levelname)s: %(message)s',
  )
  if args.dry_run:
    logging.info(
      'Would read %s and write %s', args.filename or 'stdin', args.output or 'stdout'
    )
    return 0
  try:
    with ExitStack() as stack:
      source = (
        stack.enter_context(args.filename.open(encoding='utf-8'))
        if args.filename
        else sys.stdin
      )
      target = (
        stack.enter_context(atomicWriter(args.output)) if args.output else sys.stdout
      )
      logging.debug('Reading %s', args.filename or 'stdin')
      for line in source:
        if args.include and not any(text in line for text in args.include):
          continue
        if any(text in line for text in args.exclude):
          continue
        target.write(line)
      target.flush()
  except BrokenPipeError:
    # Prevent another broken-pipe error when Python flushes stdout at shutdown.
    sys.stdout = open(os.devnull, 'w')
    return 0
  except KeyboardInterrupt:
    logging.error('Interrupted')
    return 130
  except (OSError, UnicodeError) as error:
    logging.error('%s', error)
    return 1
  return 0


if __name__ == '__main__':
  raise SystemExit(main())
