""" Test the computation of model properies """

import sys
import logging
import unittest

from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue, CTraceException
from cbverifier.test.test_grounding import TestGrounding
from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.model_properties import AttachRelation

from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestModelProperties(unittest.TestCase):
    def _get_init(self):
        spec_list = []
        ctrace = CTrace()

        act1 = TestGrounding._get_obj("act1_id","android.app.Activity")
        frag1 = TestGrounding._get_obj("frag1_id","android.app.Fragment")
        view1 = TestGrounding._get_obj("view1_id","android.app.Activity")
        int_val = TestGrounding._get_int(3)

        cb = CCallback(1, 1, "", "void android.app.Activity.<init>()",
                       [act1],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Activity","<init>()", False)])
        ctrace.add_msg(cb)

        cb = CCallback(2, 1, "", "void android.app.Fragment.<init>()",
                       [frag1],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Fragment","<init>()", False)])
        ctrace.add_msg(cb)

        ci = CCallin(3, 1, "", "android.view.View android.app.Activity.findViewById(int)",
                     [act1, int_val],
                     view1)
        cb.add_msg(ci)

        # L = [CI] [EXIT] [${CONTAINER}] android.view.View android.app.Activity.findViewById(# : int)

        root_components = [act1]

        attach_relation = [(act1, view1)]

        ts_enc = TSEncoder(ctrace, spec_list)
        return (ctrace, ts_enc, root_components, attach_relation)


    def test_attach_relation(self):
        (ctrace, enc, root_components, attach_relation) = self._get_init()
        rel = AttachRelation(enc.gs.trace_map, root_components)

        for (a,b) in attach_relation:
            self.assertTrue(rel.is_attached(a,b))
