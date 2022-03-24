#!/usr/bin/env python3
import sys, os, json, requests, argparse

helpstr = """
minimal python commandline template
"""

class Colors:
    black = "\033[0;30m";red = "\033[0;31m";green = "\033[0;32m";brown = "\033[0;33m";blue = "\033[0;34m";purple = "\033[0;35m";cyan = "\033[0;36m";lightgray = "\033[0;37m"
    darkgray = "\033[1;30m";lightred = "\033[1;31m";lightgreen = "\033[1;32m";yellow = "\033[1;33m";lightblue = "\033[1;34m";lightpurple = "\033[1;35m";lightcyan = "\033[1;36m"
    white = "\033[1;37m";bold = "\033[1m";faint = "\033[2m";italic = "\033[3m";underline = "\033[4m";blink = "\033[5m";negative = "\033[7m";crossed = "\033[9m";end = "\033[0m"

def main(args):
  print(f"{Colors.lightgreen}[+]{Colors.end} {Colors.white}doing something.{Colors.end}")
  inf = sys.stdin
  if args.filename:
    inf = open(args.filename, "r")
  for line in inf:
    print(line)


# Parse Arguements
#--------------------------------------------------------------------------------
p = argparse.ArgumentParser(
    description=helpstr, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('-f', '--filename', help='Input filename', required=True)
args = p.parse_args()


if __name__ == "__main__":
  sys.exit(main(args))
