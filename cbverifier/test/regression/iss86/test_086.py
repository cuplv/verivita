import sys
import logging
import unittest
import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.driver import main
import cbverifier.test.examples


class TestIss86(unittest.TestCase):
    def test_driver(self):
        test_path = os.path.dirname(cbverifier.test.regression.iss86.__file__)
        t1 = os.path.join(test_path, "nocrashsequence.out")
        s1 = os.path.join(test_path, "button.spec")
        argv = ["", "-t", t1, "-s", s1,
                "-m", "bmc", "-k", "2"]
        retval = main(argv)
        self.assertTrue(0 == retval)
