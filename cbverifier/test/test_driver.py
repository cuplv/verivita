""" Test the main driver program

"""

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


class TestEnc(unittest.TestCase):
    def test_driver(self):

        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace1.json")
        s1 = os.path.join(test_path, "spec1.spec")
        argv = ["", "-t", t1, "-f", "json",
                "-s", s1,
                "-m", "bmc", "-k", "2"]
        main(argv)
