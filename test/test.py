#!/usr/bin/env python3
import sys, os, unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cmdline


class CmdlineMethods(unittest.TestCase):
  def test_instance(self):
    self.data = {}

  def test_read(self):
    self.data = cmdline.readFile("test.json")
    self.assertTrue(isinstance(self.data, str))
    self.assertTrue(bool(self.data))
    self.data = cmdline.readOrderedJSON("test.json")
    self.assertTrue(isinstance(self.data, dict))
    self.assertTrue(bool(self.data))
    self.data = cmdline.readYAML("test.yaml")
    self.assertTrue(isinstance(self.data, dict))
    self.assertTrue(bool(self.data))

  def test_write(self):
    self.data = cmdline.readJSON("test.json")
    cmdline.writePrettyJSON(self.data,"pretty.json")
    cmdline.writeYAML(self.data,"test.yaml")

if __name__ == '__main__':
  unittest.main()
