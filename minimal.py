#!/usr/bin/env python3
"""A dependency-free command line starter."""

import argparse
import os
import sys


class Colors:
  # fmt: off
  black = '\033[0;30m'; red = '\033[0;31m'; green = '\033[0;32m'; brown = '\033[0;33m'; blue = '\033[0;34m'; purple = '\033[0;35m'; cyan = '\033[0;36m'; lightgray = '\033[0;37m'  # noqa: E501, E702
  darkgray = '\033[90m'; lightred = '\033[91m'; lightgreen = '\033[92m'; yellow = '\033[93m'; lightblue = '\033[94m'; lightpurple = '\033[95m'; lightcyan = '\033[96m'  # noqa: E501, E702
  white = '\033[97m'; bold = '\033[1m'; faint = '\033[2m'; italic = '\033[3m'; underline = '\033[4m'; blink = '\033[5m'; negative = '\033[7m'; crossed = '\033[9m'; end = '\033[0m'  # noqa: E501, E702
  magenta = purple; lightmagenta = lightpurple  # noqa: E702
  # fmt: on

  @classmethod
  def colorize(cls, text, color, *, stream=None):
    """Accept a name like 'green' or an ANSI constant; respect NO_COLOR."""
    code = getattr(cls, color, None)
    if not isinstance(code, str):
      code = color if color in vars(cls).values() else None
    if code is None:
      raise ValueError(f'Unknown color: {color!r}')
    stream = sys.stdout if stream is None else stream
    enabled = stream.isatty() and 'NO_COLOR' not in os.environ
    return f'{code}{text}{cls.end}' if enabled else text


# Export a short form while keeping the implementation with the palette.
colorize = Colors.colorize


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('name', nargs='?', default='world', help='Who to greet')
  parser.add_argument('--color', action='store_true', help='Force ANSI colors')
  args = parser.parse_args(argv)
  message = f'Hello, {args.name}!'
  print(
    f'{Colors.lightgreen}{message}{Colors.end}'
    if args.color
    else colorize(message, 'lightgreen')
  )
  return 0


if __name__ == '__main__':
  raise SystemExit(main())
