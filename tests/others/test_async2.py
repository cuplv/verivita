#! /usr/bin/env python
#################################################################################
#     File Name           :     test_async2.py
#     Created By          :     Peilun Zhang
#     Creation Date       :     [2016-09-15 12:07]
#     Description         :
#################################################################################

import os
import logging
import unittest
try:
    import unittest2 as unittest
except ImportError:
    import unittest

#add the cbverifier as module
import sys
currentPath = os.path.dirname(__file__)
parentPath = os.path.join(currentPath, '..')

sys.path.append(parentPath)

from cbverifier.ctrace import CTraceSerializer as CTS
from cbverifier.verifier import Verifier
from cbverifier.driver import read_from_files


class TestSuite(unittest.TestCase):

    def test_async2(self):
        BASE_DIR = os.path.join(currentPath, "specifications")
        print BASE_DIR
        spec_file_list = ["AsyncTask.spec"]
        spec_file_list = [ os.path.join(BASE_DIR, a) for a in spec_file_list]
        tracefile = os.path.join(currentPath, "SimpleButtonAsyncBug/trace/trace1.json")
        specs_map = read_from_files(spec_file_list)
        with open(tracefile, "r") as infile:
            ctrace = CTS.read_trace(infile)
        not_mapped = ctrace.rename_trace(specs_map["mappings"], True)

        verifier = Verifier(ctrace,
                            specs_map["specs"],
                            specs_map["bindings"],
                            True,
                            True)
        print not_mapped
        cex = verifier.find_bug_inc(30)

        self.assertTrue( None != cex)