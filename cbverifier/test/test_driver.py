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

from cbverifier.driver import main, DriverOptions, Driver
import cbverifier.test.examples


class TestEnc(unittest.TestCase):
    def test_driver(self):

        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace1.json")
        s1 = os.path.join(test_path, "spec1.spec")
        argv = ["", "-t", t1, "-f", "json",
                "-s", s1,
                "-m", "bmc", "-k", "2"]
        retval = main(argv)
        self.assertTrue(0 == retval)


    def test_driver_api(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace1.json")
        s1 = os.path.join(test_path, "spec1.spec")

        driver_opts = DriverOptions(t1,
                                    "json",
                                    [s1],
                                    False,
                                    False,
                                    None)

        driver = Driver(driver_opts)

        driver.check_files(sys.stdout)

        ground_specs = driver.get_ground_specs()
        assert(ground_specs is not None and
               len(ground_specs) > 0)

        trace = driver.run_bmc(2)
        assert (trace is not None)
