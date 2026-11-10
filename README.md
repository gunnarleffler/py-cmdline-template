# Python command line templates

Small starters for **Python 3.14+**, managed with **uv**.
Clone, delete what you don't need, and get coding.

- `minimal.py`: dependency-free argparse starter with the ANSI `Colors` class.
- `cmdline.py`: file/stdin CLI plus a grab bag of helper examples.
- `package/`: optional, standalone packaging example.
- `test/`: standard-library CLI tests.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
uv sync --locked
uv run minimal.py Python
uv run cmdline.py --help
uv run cmdline.py -f README.md
printf 'hello\n' | uv run cmdline.py
uv run cmdline.py -v -f README.md
```

uv installs Python 3.14 if needed and manages `.venv`. `.python-version` selects
3.14 for development; `requires-python` allows 3.14 and newer.
`minimal.py` also runs directly with Python 3.14+, without dependencies.
Colors are automatic on terminals, plain when redirected or `NO_COLOR` is set.
Use `uv run minimal.py --color Python` to force ANSI-colored output.

The `Colors` constants remain ordinary strings, so both styles work:

```python
# Always emit ANSI codes (your original style).
print(f'{Colors.green}Done{Colors.end}')

# Respect terminal detection and NO_COLOR.
print(colorize('Done', 'green'))
print(colorize('Warning', 'yellow', stream=sys.stderr), file=sys.stderr)

# The helper lives on Colors and is also exported as a module-level alias.
print(Colors.colorize('Done', 'green'))
```

Import with `from minimal import Colors, colorize`, or copy the class and alias
into standalone scripts. ANSI constants such as `Colors.green` also work as the
second argument. Unknown color names raise `ValueError`.

## Development

```sh
uv run ruff check .
uv run ruff format --check .
uv run python -m unittest discover -s test
```

Ruff handles linting and formatting, retaining the original two-space indentation.
Tests use temporary files and don't overwrite fixtures. CI runs these same checks.
Commit `uv.lock`; after changing dependencies, run `uv lock` and commit the update.

## File-processing CLI

```sh
uv run cmdline.py -f input.txt -o output.txt
uv run cmdline.py -f input.txt --include ERROR --include WARNING
uv run cmdline.py -f input.txt --exclude DEBUG --exclude TRACE
uv run cmdline.py -f input.txt -o output.txt --dry-run
```

Input defaults to stdin; output defaults to stdout. Include/exclude are mutually
exclusive, case-sensitive substring filters. Repeating include matches any term;
repeating exclude drops any matching line. Dry-run reports the plan on stderr
without reading input or creating output. File output is replaced atomically on
success; its parent directory must exist. Input and output cannot be the same path.
Errors return 1, usage errors 2, Ctrl-C 130; a closed output pipe exits quietly.
Logs go to stderr.

## Helper grab bag

| Task                   | Helpers                                                               |
| ---------------------- | --------------------------------------------------------------------- |
| Configuration          | `loadConfig`, `configValue`, `readTOML`                                 |
| Filesystem             | `findFiles`, `atomicWrite`, `atomicWriter`                              |
| Commands               | `runCommand`                                                          |
| Text / CSV             | `readFile`, `readCSV`, `readCSVdict`, `writeCSVdict`                     |
| JSON / YAML            | `readJSON`, `readOrderedJSON`, `writePrettyJSON`, `readYAML`, `writeYAML` |
| SQLite                 | `writeToDB`, `getFromDB`                                                |
| HTTP                   | `getWithRequests` (form POST), `getJSON`, `postJSON`, `downloadFile`      |
| Dates / language       | `parseDate`, `Shape`, `comprehension`, `functional`                      |
| Optional CLI structure | `subcommandParser`                                                    |

Requests, PyYAML, python-dateutil, and python-dotenv are installed by uv.

Call `loadConfig()` explicitly to load the project `.env` and retrieve `db_user`.
Importing the module does not read configuration or open a database. SQLite
helpers require a database path and an existing `COMMENTS` table. HTTP requests
use HTTPS, a timeout, and status checking; `getWithRequests()` returns response
text. `readOrderedJSON` aliases `readJSON` because dictionaries preserve order.

### Copy-and-adapt recipes

```python
from cmdline import (
  atomicWrite,
  configValue,
  downloadFile,
  findFiles,
  getJSON,
  loadConfig,
  postJSON,
  readTOML,
  runCommand,
  subcommandParser,
)

# Filesystem: iterator of Paths; remove recursive=True for one directory.
for path in findFiles('.', '*.py', recursive=True):
  print(path)
atomicWrite('result.txt', 'complete output\n')

# Commands: argument list, no shell interpolation. Returns CompletedProcess.
result = runCommand(['git', 'status', '--short'], timeout=10)
print(result.stdout)
# Raises subprocess.CalledProcessError (with stdout/stderr), TimeoutExpired,
# or OSError (e.g. command not found); handle these at your CLI boundary.

# Configuration: explicit .env loading; CLI > environment > default.
loadConfig()
timeout = int(configValue(None, 'APP_TIMEOUT', '30'))  # Replace None with args.timeout.
settings = readTOML('pyproject.toml')  # Dict; binary-mode TOML reading.

# HTTP: query parameters, JSON, bearer authentication, and downloads.
data = getJSON('https://httpbin.org/get', params={'page': 1})
data = postJSON('https://httpbin.org/post', {'name': 'example'})
# token_env='API_TOKEN' adds Bearer auth; missing env var raises KeyError.
# data = getJSON('https://your-api.example/items', token_env='API_TOKEN')
downloadFile('https://httpbin.org/bytes/1024', 'download.bin')

# Optional subcommands, not wired into the default CLI:
args = subcommandParser().parse_args(['list', '.', '--pattern', '*.py'])
if args.command == 'list':
  for path in findFiles(args.directory, args.pattern):
    print(path)
```

HTTP helpers use 30-second request timeouts and check status. Downloads stream in
chunks and replace the destination on success. `parseDate` returns `None` for
invalid input; `writeCSVdict` infers columns from the first row.

Delete helpers and dependencies you don't need (`uv remove <dependency>`).

For a standalone script copied outside this project, `uv init --script my_script.py
--python 3.14` adds inline metadata; `uv add --script my_script.py requests` adds
script-specific dependencies.

## License

[MIT](LICENSE.md). Created by Gunnar Leffler.
