import os
import logging
import unittest

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.ctrace import CTraceSerializer
from cbverifier.verifier import Verifier
from cbverifier.driver import read_from_files

class Test23(unittest.TestCase):

    def _check(self, spec_file_list, tracefile):
        specs_map = read_from_files(spec_file_list)
        with open(tracefile, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)
        not_mapped = ctrace.rename_trace(specs_map["mappings"], True)

        verifier = Verifier(ctrace,
                            specs_map["specs"],
                            specs_map["bindings"],
                            True,
                            True)
        return verifier.find_bug_inc(30)

    def test_23_1(self):
        BASE_DIR="./test/data/regression/iss23"
        spec_file_list = ["spec.spec"]
        spec_file_list = [ os.path.join(BASE_DIR, a) for a in spec_file_list]
        tracefile = os.path.join(BASE_DIR, "trace.json")

        # found a cex
        self.assertTrue(None != self._check(spec_file_list,
                                            tracefile))
    def test_23_2(self):
        BASE_DIR="./test/data/regression/iss23"
        spec_file_list = ["spec2.spec"]
        spec_file_list = [ os.path.join(BASE_DIR, a) for a in spec_file_list]
        tracefile = os.path.join(BASE_DIR, "trace2.json")

        # found a cex
        self.assertTrue(None == self._check(spec_file_list,
                                            tracefile))
