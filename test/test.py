"""CLI tests; run from the repository root with unittest discovery."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script, *args, input=''):
  return subprocess.run(
    [sys.executable, str(ROOT / script), *args],
    input=input,
    capture_output=True,
    text=True,
    check=False,
    cwd=ROOT,
  )


class CommandLineTests(unittest.TestCase):
  def test_output_and_filters(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / 'out.txt'
      result = run(
        'cmdline.py',
        '-o',
        str(path),
        '--include',
        'yes',
        '--include',
        'also',
        input='yes\nno\nalso\n',
      )
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(path.read_text(), 'yes\nalso\n')
      self.assertEqual(result.stdout, '')
      result = run('cmdline.py', '-o', str(path), '--dry-run', input='replace')
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(path.read_text(), 'yes\nalso\n')
      self.assertIn('Would read', result.stderr)
    result = run('cmdline.py', '--exclude', 'no', input='yes\nno\n')
    self.assertEqual(result.stdout, 'yes\n')
    result = run('cmdline.py', '--include', 'yes', '--exclude', 'no')
    self.assertEqual(result.returncode, 2)

  def test_stdin(self):
    result = run('cmdline.py', input='one\ntwo\nlast')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, 'one\ntwo\nlast')
    self.assertEqual(result.stderr, '')

  def test_file(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / 'input.txt'
      path.write_text('hello café\n', encoding='utf-8')
      result = run('cmdline.py', '-f', str(path))
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, 'hello café\n')

  def test_missing_file(self):
    with tempfile.TemporaryDirectory() as directory:
      result = run('cmdline.py', '-f', str(Path(directory) / 'missing'))
    self.assertEqual(result.returncode, 1)
    self.assertIn('ERROR:', result.stderr)
    self.assertNotIn('Traceback', result.stderr)

  def test_verbose(self):
    result = run('cmdline.py', '-v', input='hello\n')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, 'hello\n')
    self.assertIn('DEBUG:', result.stderr)

  def test_help(self):
    for script in ('cmdline.py', 'minimal.py'):
      with self.subTest(script=script):
        result = run(script, '--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('usage:', result.stdout)

  def test_minimal(self):
    result = run('minimal.py', 'Python')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, 'Hello, Python!\n')

  def test_import_has_no_side_effects(self):
    result = subprocess.run(
      [sys.executable, '-c', 'import cmdline; import minimal'],
      cwd=ROOT,
      capture_output=True,
      text=True,
      check=False,
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout + result.stderr, '')


if __name__ == '__main__':
  unittest.main()
