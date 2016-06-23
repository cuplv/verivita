import os
import logging


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.ctrace import CTraceSerializer, ConcreteTrace
from cbverifier.verifier import Verifier


class TestInst(unittest.TestCase):

    def testVar(self):
        # Common to all modes
        logging.basicConfig(level=logging.DEBUG)
        
        fname = "./test/data/test_vars.json"

        # Parse the trace file
        with open(fname, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)


        # test_evt_no_param
        v = Verifier(ctrace, [])
        assert v is not None
        assert v.ts_vars is not None

        print v.ts_vars
        
        self.assertTrue(len(v.ts_vars) == 4)
        
