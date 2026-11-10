import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('helpers', ROOT / 'cmdline.py')
helpers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helpers)


class HelperTests(unittest.TestCase):
  def test_colorize(self):
    spec = importlib.util.spec_from_file_location('minimal', ROOT / 'minimal.py')
    minimal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(minimal)
    self.assertEqual(minimal.Colors.magenta, minimal.Colors.purple)
    self.assertEqual(minimal.Colors.lightmagenta, '\033[95m')
    self.assertEqual(minimal.Colors.white, '\033[97m')
    stream = Mock()
    with patch.dict('os.environ', {}, clear=True):
      stream.isatty.return_value = True
      self.assertEqual(
        minimal.colorize('ok', minimal.Colors.green, stream=stream),
        f'{minimal.Colors.green}ok{minimal.Colors.end}',
      )
      self.assertEqual(
        minimal.Colors.colorize('ok', 'green', stream=stream),
        minimal.colorize('ok', minimal.Colors.green, stream=stream),
      )
      with self.assertRaises(ValueError):
        minimal.colorize('ok', 'not-a-color', stream=stream)
      stream.isatty.return_value = False
      self.assertEqual(
        minimal.colorize('ok', minimal.Colors.green, stream=stream), 'ok'
      )
    with patch.dict('os.environ', {'NO_COLOR': ''}):
      stream.isatty.return_value = True
      self.assertEqual(
        minimal.colorize('ok', minimal.Colors.green, stream=stream), 'ok'
      )

  def test_recipes(self):
    import subprocess
    import sys

    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / 'result.txt'
      helpers.atomicWrite(path, 'original')
      with self.assertRaises(RuntimeError), helpers.atomicWriter(path) as target:
        target.write('partial')
        raise RuntimeError('failed')
      self.assertEqual(path.read_text(), 'original')
      self.assertEqual(list(Path(directory).iterdir()), [path])
      self.assertEqual(list(helpers.findFiles(directory, '*.txt')), [path])
      toml = Path(directory) / 'config.toml'
      toml.write_text('timeout = 10\n')
      self.assertEqual(helpers.readTOML(toml), {'timeout': 10})
    result = helpers.runCommand([sys.executable, '-c', 'print("ok")'])
    self.assertEqual(result.stdout, 'ok\n')
    with self.assertRaises(subprocess.CalledProcessError):
      helpers.runCommand([sys.executable, '-c', 'raise SystemExit(1)'])
    with patch.dict('os.environ', {'APP_TEST': 'env'}):
      self.assertEqual(helpers.configValue('cli', 'APP_TEST', 'default'), 'cli')
      self.assertEqual(helpers.configValue(None, 'APP_TEST', 'default'), 'env')
    self.assertEqual(
      helpers.subcommandParser().parse_args(['list', '.']).command, 'list'
    )

  def test_json_http_and_download(self):
    with patch.object(helpers.requests, 'get') as get:
      response = get.return_value.__enter__.return_value
      response.json.return_value = {'ok': True}
      with patch.dict('os.environ', {'API_TOKEN': 'secret'}):
        self.assertEqual(
          helpers.getJSON('https://example.com', token_env='API_TOKEN'), {'ok': True}
        )
        self.assertEqual(
          get.call_args.kwargs['headers'], {'Authorization': 'Bearer secret'}
        )
      response.iter_content.return_value = [b'one', b'two']
      with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'download'
        helpers.downloadFile('https://example.com', path)
        self.assertEqual(path.read_bytes(), b'onetwo')
    with patch.object(helpers.requests, 'post') as post:
      response = post.return_value.__enter__.return_value
      response.json.return_value = {'created': True}
      self.assertEqual(
        helpers.postJSON('https://example.com', {'a': 1}), {'created': True}
      )
      self.assertEqual(post.call_args.kwargs['json'], {'a': 1})

  def test_file_round_trips(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / 'data'
      data = {'name': 'café', 'count': 2}
      for write, read in (
        (helpers.writePrettyJSON, helpers.readJSON),
        (helpers.writeYAML, helpers.readYAML),
      ):
        write(data, path)
        self.assertEqual(read(path), data)
        self.assertTrue(helpers.readFile(path))
      rows = [{'name': 'café', 'value': 'one,two'}]
      helpers.writeCSVdict(rows, path)
      self.assertEqual(helpers.readCSVdict(path), rows)
      self.assertEqual(helpers.readCSV(path)[1], ['café', 'one,two'])

  def test_sqlite(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / 'data.db'
      with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE COMMENTS (id INTEGER, message TEXT)')
      helpers.writeToDB({'id': 1, 'message': "it's fine"}, path)
      self.assertEqual(
        helpers.getFromDB(['message'], id=1, dbpath=path), [("it's fine",)]
      )
      with self.assertRaises(ValueError):
        helpers.getFromDB(['id; DROP TABLE COMMENTS'], dbpath=path)

  def test_dates(self):
    self.assertEqual(helpers.parseDate('2026-01-02').year, 2026)
    self.assertIsNone(helpers.parseDate('not a date'))

  def test_http(self):
    with patch.object(helpers.requests, 'post') as post:
      response = post.return_value.__enter__.return_value
      response.text = 'ok'
      self.assertEqual(helpers.getWithRequests(), 'ok')
      response.raise_for_status.assert_called_once()
      self.assertEqual(post.call_args.kwargs['timeout'], 30)

  def test_colors(self):
    import subprocess
    import sys

    result = subprocess.run(
      [sys.executable, str(ROOT / 'minimal.py'), '--color', 'Python'],
      capture_output=True,
      text=True,
      check=True,
    )
    self.assertEqual(result.stdout, '\033[92mHello, Python!\033[0m\n')
