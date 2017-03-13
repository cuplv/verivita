import sys
import logging
import unittest
import os
from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.cex_printer import CexPrinter
from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue, CTraceException
from cbverifier.specs.spec import Spec
from cbverifier.bmc.bmc import BMC

from cbverifier.test.test_grounding import TestGrounding


class TestIss90(unittest.TestCase):

    def test_090_cb_name(self):
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CI] [ENTRY] [l] void m4();" \
                                               "SPEC FALSE[*] |- [CB] [ENTRY][l] void m3();" \
                                               "SPEC [CB] [ENTRY][l1] void m1() |+ [CB] [ENTRY] [l2] void m3()")
        assert spec_list is not None

        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(2, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(3, 1, "", "void m3()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m3()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(4, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(5, 1, "", "void m5()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m5()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(6, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)


        ts_enc = TSEncoder(ctrace, spec_list)
        ts = ts_enc.get_ts_encoding()
        error = ts_enc.error_prop
        bmc = BMC(ts_enc.helper, ts, error)
        cex = bmc.find_bug(6)
        self.assertTrue(cex is not None)

        stringio = StringIO()
        printer = CexPrinter(ts_enc.mapback, cex, stringio)
        printer.print_cex()

        io_string = stringio.getvalue()

        self.assertTrue("[1] [CB] [ENTRY] void m1()" in io_string)
        self.assertTrue("[3] [CB] [ENTRY] void m3()" in io_string or
                        "[5] [CB] [ENTRY] void m5()" in io_string)
        self.assertTrue("[4] [CI] [ENTRY] void m4()" in io_string or
                        "[6] [CI] [ENTRY] void m4()" in io_string)


    def test_090_multiple_cbs(self):
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CI] [ENTRY] [l] void m4();" \
                                               "SPEC FALSE[*] |- [CB] [ENTRY] [l] void m3();" \
                                               "SPEC [CB] [ENTRY] [l1] void m1() |+ [CB] [ENTRY] [l2] void m3()")
        assert spec_list is not None

        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(2, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        ci = CCallin(3, 1, "", "void m6()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(4, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(5, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(6, 1, "", "void m3()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m3()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(7, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)

        ts_enc = TSEncoder(ctrace, spec_list)
        ts = ts_enc.get_ts_encoding()
        error = ts_enc.error_prop
        bmc = BMC(ts_enc.helper, ts, error)
        cex = bmc.find_bug(6)
        self.assertTrue(cex is not None)

        stringio = StringIO()
        printer = CexPrinter(ts_enc.mapback, cex, stringio)
        printer.print_cex()

        io_string = stringio.getvalue()

        self.assertTrue("[4] [CB] [ENTRY] void m1()" in io_string)
        self.assertTrue("[5] [CI] [ENTRY] void m2()" in io_string)
        self.assertTrue("[6] [CB] [ENTRY] void m3()" in io_string)
        self.assertTrue("[7] [CI] [ENTRY] void m4()" in io_string)
