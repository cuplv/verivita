""" Test the main driver program

"""

import sys
import logging
import unittest
import os

from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.driver import main, DriverOptions, Driver, NoDisableException
from cbverifier.driver import check_disable, print_ground_spec_map
from cbverifier.traces.ctrace import MalformedTraceException, TraceEndsInErrorException
from cbverifier.encoding.cex_printer import CexPrinter
from cbverifier.utils.stats import Stats
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
        self.stats = Stats()
        driver.check_files(sys.stdout)

        ground_specs = driver.get_ground_specs()
        assert(ground_specs is not None and
               len(ground_specs) > 0)

        trace = driver.run_bmc(2)
        assert (trace is not None)

    def test_driver_not_wf_trace(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace_no_exit.json")
        s1 = os.path.join(test_path, "spec1.spec")

        driver_opts = DriverOptions(t1,
                                    "json",
                                    [s1],
                                    False,
                                    False,
                                    None)

        with self.assertRaises(MalformedTraceException):
            driver = Driver(driver_opts)

    def test_driver_trace_in_exception(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace_exception.json")
        s1 = os.path.join(test_path, "spec1.spec")

        driver_opts = DriverOptions(t1,
                                    "json",
                                    [s1],
                                    False,
                                    False,
                                    None,
                                    False)

        with self.assertRaises(TraceEndsInErrorException):
            driver = Driver(driver_opts)

    def test_driver_trace_disable(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace1.json")
        s1 = os.path.join(test_path, "spec1.spec")

        driver_opts = DriverOptions(t1,
                                    "json",
                                    [s1],
                                    False,
                                    False,
                                    None,
                                    False)
        driver = Driver(driver_opts)
        ground_specs = driver.get_ground_specs()
        # ok, has a disable
        check_disable(ground_specs)

        s1 = os.path.join(test_path, "spec2.spec")

        driver_opts = DriverOptions(t1,
                                    "json",
                                    [s1],
                                    False,
                                    False,
                                    None,
                                    False)
        driver = Driver(driver_opts)
        ground_specs = driver.get_ground_specs()
        with self.assertRaises(NoDisableException):
            check_disable(ground_specs)

    def test_stats(self):
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
        trace = driver.run_bmc(2)

        mystream = StringIO()
        driver.stats.write_times(mystream, Stats.PARSING_TIME)
        self.assertTrue(Stats.PARSING_TIME in mystream.getvalue())
        driver.stats.write_times(mystream, Stats.SPEC_GROUNDING_TIME)
        self.assertTrue(Stats.SPEC_GROUNDING_TIME in mystream.getvalue())
        driver.stats.write_times(mystream, Stats.ENCODING_TIME)
        self.assertTrue(Stats.ENCODING_TIME in mystream.getvalue())
        driver.stats.write_times(mystream, Stats.VERIFICATION_TIME)
        self.assertTrue(Stats.VERIFICATION_TIME in mystream.getvalue())


    def test_print_orig_spec(self):
        # Test of the printing the original specification
        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace1.json")
        s1 = os.path.join(test_path, "spec1.spec")

        # TODO Add driver options
        driver_opts = DriverOptions(t1,
                                    "json",
                                    [s1],
                                    False,
                                    False,
                                    None)

        driver = Driver(driver_opts)
        self.stats = Stats()
        driver.check_files(sys.stdout)

        ground_specs_map = driver.get_ground_specs(True)
        assert(ground_specs_map is not None)

        mystream = StringIO()        
        print_ground_spec_map(ground_specs_map, mystream)

        self.assertTrue("SPEC [CB] [ENTRY] [l] void m1() |- [CI] [ENTRY] [l] void m2()" in mystream.getvalue())


        (cex, mapback) = driver.run_bmc(2)
        assert (cex is not None)
        mystream = StringIO()
        printer = CexPrinter(mapback, cex, mystream)
        printer.print_cex()
#        self.assertTrue("SPEC [CB] [ENTRY] [l] void m1() |- [CI] [ENTRY] [l] void m2()" in mystream.getvalue())



        
