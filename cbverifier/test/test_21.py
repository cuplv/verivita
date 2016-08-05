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

class Test21(unittest.TestCase):
    def test_21(self):
        BASE_DIR="./test/data/regression/iss21"
        spec_file_list = ["CountDownTimer.spec",
                          "Fragment.spec",
                          "AsyncTask.spec",
                          "View.spec",
                          "Activity.spec"]
        spec_file_list = [ os.path.join(BASE_DIR, a) for a in spec_file_list]
        tracefile = os.path.join(BASE_DIR, "_Kistenstapeln-Android_bug_5e54c44349a194006c8f0e3605efc504470b68a3_04.json")
        specs_map = read_from_files(spec_file_list)

        with open(tracefile, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)
        not_mapped = ctrace.rename_trace(specs_map["mappings"], True)

        verifier = Verifier(ctrace,
                            specs_map["specs"],
                            specs_map["bindings"],
                            True,
                            True)
        cex = verifier.find_bug_inc(30)

        # found a cex
        self.assertTrue(None != cex)
