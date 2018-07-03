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

    def test_attach_relation(self):
        def _get():
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

            root_components = [act1]
            attach_relation = [(act1, view1)]

            ts_enc = TSEncoder(ctrace, [])
            return (ctrace, ts_enc, root_components, attach_relation)


        (ctrace, enc, root_components, attach_relation) = _get()
        rel = AttachRelation(enc.gs.trace_map, root_components)

        for (a,b) in attach_relation:
            self.assertTrue(rel.is_attached(a,b))


    def test_register_relation(self):
        def _get():
            ctrace = CTrace()

            act1 = TestGrounding._get_obj("act1_id","android.app.Activity")
            frag1 = TestGrounding._get_obj("frag1_id","android.app.Fragment")
            view1 = TestGrounding._get_obj("view1_id","android.app.Activity")
            onclick_listener1 = TestGrounding._get_obj("clicklist_id",
                                                       "android.view.View.setOnClickListener")
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

            ci = CCallin(3, 1, "", "void android.view.View.setOnClickListener(android.view.View$OnClickListener)",
                         [view1, onclick_listener1],None)
            cb.add_msg(ci)

            root_components = [act1]
            relation = [(view1, onclick_listener1)]

            ts_enc = TSEncoder(ctrace, [])
            return (ctrace, ts_enc, root_components, relation)

        (ctrace, enc, root_components, relation) = self._get_init()
        rel = RegisterRelation(enc.gs.trace_map, root_components)

        for (a,b) in relation:
            self.assertTrue(rel.is_attached(a,b))

