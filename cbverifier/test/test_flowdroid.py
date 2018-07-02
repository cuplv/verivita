""" Test the creation of the flowdroid model """

import sys
import logging
import unittest

from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue, CTraceException
from cbverifier.test.test_grounding import TestGrounding
from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.flowdroid_model.lifecycle_constants import Activity, Fragment
from cbverifier.encoding.flowdroid_model.flowdroid_model_builder import FlowDroidModelBuilder

from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestFlowDroid(unittest.TestCase):

    def test_const_classes(self):
        """ Test the creation of ad-hoc classes used to lookup methods """

        inst_value = TestGrounding._get_obj("1","android.app.Activity")
        activity = Activity("android.app.Activity", inst_value)
        self.assertTrue(activity.has_methods_names(Activity.INIT))
        "[CB] [ENTRY] [l]  android.app.Activity <init>()" in activity.get_methods_names(Activity.INIT)

        inst_value = TestGrounding._get_obj("1","android.support.v4.app.FragmentActivity")
        activity = Activity("android.support.v4.app.FragmentActivity", inst_value)
        self.assertTrue(activity.has_methods_names(Activity.INIT))
        "[CB] [ENTRY] [l]  android.support.v4.app.FragmentActivity <init>()" in activity.get_methods_names(Activity.INIT)


    def _get_sample_trace(self):
        spec_list = []
        ctrace = CTrace()

        cb = CCallback(1, 1, "", "void android.app.Activity.<init>()",
                       [TestGrounding._get_obj("d8ad51d","android.app.Activity")],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Activity","<init>()", False)])
        ctrace.add_msg(cb)

        cb = CCallback(1, 1, "", "void android.app.Fragment.<init>()",
                       [TestGrounding._get_obj("eae2341","android.app.Fragment")],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Fragment","<init>()", False)])
        ctrace.add_msg(cb)

        ts_enc = TSEncoder(ctrace, spec_list)
        return ts_enc


    def test_flowdroid_init(self):
        enc = self._get_sample_trace()
        fd_builder = FlowDroidModelBuilder(enc)

        # check that it finds the activity component
        components_set = fd_builder.get_components()
        self.assertTrue(2 == len(components_set))

        activity = None
        fragment = None
        for elem in components_set:
            if (isinstance(elem, Activity)):
                activity = elem
            if (isinstance(elem, Fragment)):
                fragment = elem
        self.assertTrue(activity is not None)
        self.assertTrue(fragment is not None)

        self.assertTrue(isinstance(activity, Activity))
        activity.has_methods_names(Activity.INIT)
        activity.has_trace_msg(Activity.INIT)
        trace_msg = activity.get_trace_msgs(Activity.INIT)
        self.assertTrue (isinstance(trace_msg, CCallin) or
                         isinstance(trace_msg, CCallback))

        self.assertTrue(isinstance(fragment, Fragment))
        fragment.has_methods_names(Fragment.INIT)
        fragment.has_trace_msg(Fragment.INIT)
        trace_msg = fragment.get_trace_msgs(Fragment.INIT)
        self.assertTrue (isinstance(trace_msg, CCallin) or
                         isinstance(trace_msg, CCallback))



        # check that it attaches 
