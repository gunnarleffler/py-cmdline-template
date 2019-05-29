#!/usr/bin/env python3
#!/usr/local/bin/python3
helpstr = '''
python3 starter command line template v1.0.1
04/10/2019
This program contains stuff to quick-start a python project.

FORMATTING
==========

configuration file example
--------------------------

Output
------

PARAMETERS
==========
'''

import sys, os, datetime, requests, re, random, argparse, sqlite3, yaml, json, crayons
import dateutil.parser as dateparser
from collections import OrderedDict

current_dir = os.path.dirname(__file__)
config_dir = os.path.join(current_dir, "..", "config")

#An example of a class
#--------------------------------------------------------------------------------


class Shape:

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.description = "This shape has not been described yet"
    self.author = "Nobody has claimed to make this shape yet"

  def area(self):
    return self.x * self.y


# SQLite
#--------------------------------------------------------------------------------
def writeToDB(fdata, dbpath=None):
  con = sqlite3.connect(dbpath)
  cur = con.cursor()
  cmd = "INSERT INTO COMMENTS (%s) VALUES (%s)"
  cmd = cmd % (",".join(list(fdata.keys())), ",".join(
      ["?"] * len(list(fdata.keys()))))
  cur.execute(cmd, list(fdata.values()))
  con.commit()
  con.close()


def getFromDB(fkeys, sortkeys=False, sanitize=False, id=None, dbpath=None):
  con = sqlite3.connect(dbpath)
  cur = con.cursor()
  if sortkeys:
    fkeys.sort()
  cmd = "SELECT %s FROM COMMENTS" % (",".join(fkeys))
  if id != None:
    cmd += " WHERE id == ?"
    cur.execute(cmd, (id,))
  else:
    cur.execute(cmd)
  columns = cur.fetchall()
  if sanitize == True:
    for i in range(len(columns)):
      row = []
      for j in range(len(columns[i])):
        row.append(escape(columns[i][j]))
      columns[i] = row
  con.close()
  return columns


# File routines
#--------------------------------------------------------------------------------
def readFile(path):
  with open(path) as infile:
    return infile.read()

def writeYAML(data, path):
  with open(path, 'w') as outfile:
    yaml.safe_dump(data, outfile, default_flow_style=False)

def readYAML(path):
  with open(path, 'r') as infile:
    return yaml.safe_load(infile)

def readOrderedJSON(path):
  with open(path, "r") as infile:
    return json.load(infile, object_pairs_hook=OrderedDict)

def readJSON(path):
  with open(path, "r") as infile:
    return json.load(infile)

def writePrettyJSON(data, path):
  with open(path, "w") as outfile:
    return json.dump(data, outfile, sort_keys=True, indent = 2)


# Web Methods
#--------------------------------------------------------------------------------
def getWithRequests():
  payload = {'key1': 'value1', 'key2': 'value2'}
  r = requests.post("http://httpbin.org/post", data=payload)
  print(r.text)


def parseDate(s):
  try:
    return dateparser.parse(s, fuzzy=True)
  except:
    return None


# main()
#--------------------------------------------------------------------------------
def main ():
  print (f"{crayons.red('Type')} {crayons.blue('something.')}")
  inf = sys.stdin
  if args.filename:
    inf = open(args.filename, "r")
  for line in inf:
    print(line)
  

# Parse Arguements
#--------------------------------------------------------------------------------
p = argparse.ArgumentParser(
    description=helpstr, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('-v', '--verbose', action='store_true', help='Work verbosely')
p.add_argument('-f', '--filename', help='Input filename')
args = p.parse_args()

if __name__ == "__main__":
  sys.exit(main())

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2
