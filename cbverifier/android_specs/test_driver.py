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
import cbverifier.android_specs


class TestKnownTraces(unittest.TestCase):
    allspecfiles = ["activity.spec","AppCompatActivity.spec"
        ,"button.spec","countdowntimer.spec","fragment.spec","mediaplayer.spec"]
    test_path = os.path.dirname(cbverifier.android_specs.__file__)
    s1 = [os.path.join(test_path, filename) for filename in allspecfiles]

    @unittest.skip("Disabled due to issue 168")
    def test_contraction_timer_bug(self):
        t1 = os.path.join(self.test_path, "testTraces", "ContractionTimerDistilled", "trace")

        driver_opts = DriverOptions(t1,
                                    "bin",
                                    self.s1,
                                    True,
                                    False,
                                    None)
        driver = Driver(driver_opts)

        driver.check_files(sys.stdout)

        ground_specs = driver.get_ground_specs()
        assert(ground_specs is not None and
               len(ground_specs) > 0)

        trace = driver.run_bmc(20)
        assert (trace is not None)
        assert(trace[0] is not None)

    @unittest.skip("Disabled due to issue 168")
    def test_contraction_timer_fix(self):
        t1 = os.path.join(self.test_path, "testTraces", "ContractionTimerDistilledFix", "trace")

        driver_opts = DriverOptions(t1,
                                    "bin",
                                    self.s1,
                                    True,
                                    False,
                                    None)
        driver = Driver(driver_opts)

        driver.check_files(sys.stdout)

        ground_specs = driver.get_ground_specs()
        assert(ground_specs is not None and
               len(ground_specs) > 0)

        trace = driver.run_bmc(20)
        assert (trace is not None)
        assert(trace[0] is None)

    @unittest.skip("Disabled due to issue 168")
    def test_media_fix(self):
        t1 = os.path.join(self.test_path, "testTraces", "MediaPlayerExample", "trace")

        driver_opts = DriverOptions(t1,
                                    "bin",
                                    self.s1,
                                    True,
                                    False,
                                    None)
        driver = Driver(driver_opts)

        driver.check_files(sys.stdout)

        ground_specs = driver.get_ground_specs()
        assert(ground_specs is not None and
               len(ground_specs) > 0)

        trace = driver.run_bmc(20)
        assert (trace is not None)
        assert(trace[0] is None)

    @unittest.skip("Disabled due to issue 168")
    def test_media_bug(self):
        t1 = os.path.join(self.test_path, "testTraces", "MediaPlayerExampleBug", "trace")

        driver_opts = DriverOptions(t1,
                                    "bin",
                                    self.s1,
                                    True,
                                    False,
                                    None)
        driver = Driver(driver_opts)

        driver.check_files(sys.stdout)

        ground_specs = driver.get_ground_specs()
        assert(ground_specs is not None and
               len(ground_specs) > 0)

        trace = driver.run_bmc(20)
        assert (trace is not None)
        assert(trace[0] is not None)
