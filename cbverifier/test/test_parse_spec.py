import os
import logging


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pysmt.shortcuts import Not, And, is_sat, reset_env
from pysmt.logics import QF_BOOL

from cbverifier.spec import Spec, SpecType, SpecSerializer

class TestParseSepc(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def testVar(self):
        fname = "./test/data/t1.spec"

        # Parse the trace file
        with open(fname, "r") as infile:
            specs = SpecSerializer.read_specs(infile)

        self.assertTrue(len(specs) == 1)
        spec = specs[0]

        self.assertTrue(spec.specType == SpecType.Disable)
        self.assertTrue(spec.src == "0_event")
        self.assertTrue(spec.cb == "cbEvent0")
        self.assertTrue(spec.dst == "callin_true_false")

        self.assertTrue(spec.src_args == ["obj@1"])
        self.assertTrue(spec.cb_args == ["obj@1"])
        self.assertTrue(spec.dst_args == ["obj@2","true","objll","false"])





