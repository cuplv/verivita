""" Test the creation of the flowdroid model """

import sys
import logging
import unittest

from cbverifier.encoding.grounding import TraceMap
from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue, CTraceException
from cbverifier.test.test_grounding import TestGrounding
from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.flowdroid_model.lifecycle_constants import Activity, Fragment
from cbverifier.encoding.flowdroid_model.flowdroid_model_builder import FlowDroidModelBuilder
from cbverifier.encoding.cex_printer import CexPrinter
from cbverifier.bmc.bmc import BMC

from pysmt.shortcuts import FALSE as FALSE_PYSMT

from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestFlowDroid(unittest.TestCase):

    def setUp(self):
        # Reset the obj id before each test
        self._obj_id_ = 0

    def get_obj_id(self):
        self._obj_id_ += 1
        return self._obj_id_

    def test_activity_lifecycle_callbacks(self):
        """ Test the creation of the ad-hoc classes used to represent
        the activity lifecycle callbacks
        """

        def _gen_activity_trace(class_name):
            act = TestGrounding._get_obj("1",class_name)
            bundle = TestGrounding._get_obj("2","android.os.Bundle")
            lifecycle = TestGrounding._get_obj("3","android.app.Application.ActivityLifecycleCallbacks")
            view = TestGrounding._get_obj("4","android.view.View")

            trace = CTrace()
            helper = TestFlowDroid.ActivityHelper(class_name, act, bundle, lifecycle, None)
            for (cb_name, _) in Activity.get_class_cb_static():
                cb = helper.get_cb(cb_name)
                trace.add_msg(cb)
            return (trace, act)

        for class_name in Activity.class_names:
            (trace, act) = _gen_activity_trace(class_name)
            traceMap = TraceMap(trace)

            activity = Activity(class_name, act, traceMap)
            for (cb_name, _) in Activity.get_class_cb_static():
                self.assertTrue(activity.has_trace_msg(cb_name))

    def test_fragment_lifecycle_callbacks(self):
        """ """
        def _gen_fragment_trace(class_name):
            fragment = TestGrounding._get_obj("1",class_name)
            bundle = TestGrounding._get_obj("2","android.os.Bundle")
            act = TestGrounding._get_obj("3","android.app.Activity")
            inflater = TestGrounding._get_obj("4","android.view.LayoutInflater")
            viewgroup = TestGrounding._get_obj("5","android.view.ViewGroup")
            view = TestGrounding._get_obj("6","android.view.View")

            trace = CTrace()
            helper = TestFlowDroid.FragmentHelper(class_name, fragment, act, bundle,
                                                  inflater, viewgroup, view)
            for (cb_name, _) in Fragment.get_class_cb_static():
                cb = helper.get_cb(cb_name)
                trace.add_msg(cb)
            return (trace, fragment)


        for class_name in Fragment.class_names:
            (trace, act) = _gen_fragment_trace(class_name)
            traceMap = TraceMap(trace)

            fragment = Fragment(class_name, act, traceMap)
            for (cb_name, _) in Fragment.get_class_cb_static():
                self.assertTrue(fragment.has_trace_msg(cb_name))


    def _get_sample_trace(self):
        spec_list = []
        ctrace = CTrace()

        cb = CCallback(1, 1, "", "void android.app.Activity.onCreate(android.os.Bundle)",
                       [TestGrounding._get_obj("d8ad51d","android.app.Activity"),
                        TestGrounding._get_obj("2","android.os.Bundle")],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Activity","onCreate(android.os.Bundle)", False)])
        ctrace.add_msg(cb)

        cb = CCallback(1, 1, "", "void android.app.Fragment.onCreate(android.os.Bundle)",
                       [TestGrounding._get_obj("asefwer","android.app.Fragment"),
                        TestGrounding._get_obj("2","android.os.Bundle")],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Fragment","onCreate(android.os.Bundle)", False)])
        ctrace.add_msg(cb)

        ts_enc = TSEncoder(ctrace, spec_list)
        return ts_enc


    def test_component_construction(self):
        enc = self._get_sample_trace()
        fd_builder = FlowDroidModelBuilder(enc.trace, enc.gs.trace_map)
        fd_builder.init_relation(set([]))

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
        self.assertTrue(activity.has_trace_msg(Activity.ONCREATE))
        trace_msg = activity.get_trace_msgs(Activity.ONCREATE)
        self.assertTrue(trace_msg is not None)

        self.assertTrue(isinstance(fragment, Fragment))
        self.assertTrue(fragment.has_trace_msg(Fragment.ONCREATE))
        trace_msg = fragment.get_trace_msgs(Fragment.ONCREATE)
        self.assertTrue(trace_msg is not None)

    def test_cb_approx(self):
        # Attachment relation:
        #
        # activity_1
        # activity_2
        #
        trace = CTrace()
        (cb1, act1) = self._create_activity()
        (cb2, act2) = self._create_activity()
        trace.add_msg(cb1)
        trace.add_msg(cb2)

        fd = self._get_fdm(trace)

        # No "free messages"
        self.assertTrue(len(fd.free_msg) == 0)

        self.assertTrue(act1 in fd.compid2msg_keys)
        self.assertTrue(0 < fd.compid2msg_keys[act1])
        self.assertTrue(act2 in fd.compid2msg_keys)
        self.assertTrue(0 < fd.compid2msg_keys[act2])
        self.assertTrue(fd.compid2msg_keys[act1].isdisjoint(fd.compid2msg_keys[act2]))


    def test_fragment_in_act(self):
        # Attachment relation:
        #
        # activity_1
        #   frag1
        # activity_2
        #   frag2
        trace = CTrace()
        (cb1, act1) = self._create_activity()
        (cb2, act2) = self._create_activity()
        (cb3, frag1) = self._create_fragment()
        (cb4, frag2) = self._create_fragment()
        cb5 = self._attach_fragment_to_activity(act1, frag1)
        cb6 = self._attach_fragment_to_activity(act2, frag2)
        trace.add_msg(cb1)
        trace.add_msg(cb2)
        trace.add_msg(cb3)
        trace.add_msg(cb4)
        trace.add_msg(cb5)
        trace.add_msg(cb6)

        fd = self._get_fdm(trace)

        self.assertTrue(act1 in fd.compid2msg_keys)
        self.assertTrue(0 < fd.compid2msg_keys[act1])

        self.assertTrue(act2 in fd.compid2msg_keys)
        self.assertTrue(0 < fd.compid2msg_keys[act2])

        self.assertTrue(frag1 in fd.compid2msg_keys)
        self.assertTrue(0 < fd.compid2msg_keys[frag1])

        self.assertTrue(frag2 in fd.compid2msg_keys)
        self.assertTrue(0 < fd.compid2msg_keys[frag2])


        self.assertTrue(fd.compid2msg_keys[act1].isdisjoint(fd.compid2msg_keys[act2]))
        self.assertTrue(fd.compid2msg_keys[act1].isdisjoint(fd.compid2msg_keys[frag1]))
        self.assertTrue(fd.compid2msg_keys[act1].isdisjoint(fd.compid2msg_keys[frag2]))

        self.assertTrue(fd.compid2msg_keys[act2].isdisjoint(fd.compid2msg_keys[frag1]))
        self.assertTrue(fd.compid2msg_keys[act2].isdisjoint(fd.compid2msg_keys[frag2]))

        self.assertTrue(fd.compid2msg_keys[frag1].isdisjoint(fd.compid2msg_keys[frag2]))



    def test_act_frag_view(self):
        # Attachment relation:
        #
        # activity1
        #   frag1
        #   view1
        #
        trace = CTrace()
        (cb1, act1) = self._create_activity()
        (cb2, frag1) = self._create_fragment()
        (cb3, view1) = self._create_view()
        cb4 = self._attach_fragment_to_activity(act1, frag1)
        ci = self._attach_view_to_activity(act1, view1)
        cb1.add_msg(ci)
        cb5 = self._add_view_on_measure(view1)

        trace.add_msg(cb1)
        trace.add_msg(cb2)
        trace.add_msg(cb3)
        trace.add_msg(cb4)
        trace.add_msg(cb5)

        fd = self._get_fdm(trace)


    # Full lifecylce - wxpect it to be accepted
    full_lifecycle = [Activity.ONCREATE,
                      Activity.ONACTIVITYCREATED,
                      Activity.ONSTART,
                      Activity.ONACTIVITYSTARTED,
                      Activity.ONRESTOREINSTANCESTATE,
                      Activity.ONPOSTCREATE,
                      Activity.ONRESUME,
                      Activity.ONACTIVITYRESUMED,
                      Activity.ONPOSTRESUME,
                      Activity.ONPAUSE,
                      Activity.ONACTIVITYPAUSED,
                      Activity.ONCREATEDESCRIPTION,
                      Activity.ONSAVEINSTANCESTATE,
                      Activity.ONACTIVITYSAVEINSTANCESTATE,
                      Activity.ONSTOP,
                      Activity.ONACTIVITYSTOPPED,
                      Activity.ONRESTART,
                      Activity.ONDESTROY,
                      Activity.ONACTIVITYDESTROYED]

    multiple_msgs = [Activity.ONACTIVITYCREATED,
                     Activity.ONACTIVITYSTARTED,
                     Activity.ONACTIVITYRESUMED,
                     Activity.ONACTIVITYPAUSED,
                     Activity.ONACTIVITYSAVEINSTANCESTATE,
                     Activity.ONACTIVITYSTOPPED,
                     Activity.ONACTIVITYDESTROYED]


    def test_lc_0(self):
        # Full lifecylce - wxpect it to be accepted
        full_lifecycle = list(self.full_lifecycle)
        self._test_lc_enc(full_lifecycle,True)
        # full_lifecycle.extend(list(full_lifecycle))
        # self._test_lc_enc(full_lifecycle,True)
        # full_lifecycle.extend(list(full_lifecycle))
        # self._test_lc_enc(full_lifecycle,True)

    def test_lc_1(self):
        # reject all in the initial state
        self._test_lc_enc([Activity.ONACTIVITYCREATED], False)
        self._test_lc_enc([Activity.ONSTART], False)
        self._test_lc_enc([Activity.ONACTIVITYSTARTED], False)
        self._test_lc_enc([Activity.ONRESTOREINSTANCESTATE], False)
        self._test_lc_enc([Activity.ONPOSTCREATE], False)
        self._test_lc_enc([Activity.ONRESUME], False)
        self._test_lc_enc([Activity.ONACTIVITYRESUMED], False)
        self._test_lc_enc([Activity.ONPOSTRESUME], False)
        self._test_lc_enc([Activity.ONPAUSE], False)
        self._test_lc_enc([Activity.ONACTIVITYPAUSED], False)
        self._test_lc_enc([Activity.ONCREATEDESCRIPTION], False)
        self._test_lc_enc([Activity.ONSAVEINSTANCESTATE], False)
        self._test_lc_enc([Activity.ONACTIVITYSAVEINSTANCESTATE], False)
        self._test_lc_enc([Activity.ONSTOP], False)
        self._test_lc_enc([Activity.ONACTIVITYSTOPPED], False)
        self._test_lc_enc([Activity.ONRESTART], False)
        self._test_lc_enc([Activity.ONDESTROY], False)
        self._test_lc_enc([Activity.ONACTIVITYDESTROYED], False)


    def test_lc_optional(self):
        # test when skipping the optional transitions
        optional= [[Activity.ONCREATE,
                    Activity.ONACTIVITYCREATED,
                    Activity.ONACTIVITYSTARTED,
                    Activity.ONRESTOREINSTANCESTATE],
                   [Activity.ONCREATE,
                    Activity.ONACTIVITYCREATED,
                    Activity.ONSTART,
                    Activity.ONRESTOREINSTANCESTATE],
                   [Activity.ONCREATE,
                    Activity.ONACTIVITYCREATED,
                    Activity.ONRESTOREINSTANCESTATE]]

        for optional_seq in optional:
            self._test_lc_enc(optional_seq, True)


    def test_lc_at_least_one(self):
        # test for multiple instances

        # Test duplication
        for msg in TestFlowDroid.multiple_msgs:

            print "TESTING " + msg

            to_test = []
            for l in self.full_lifecycle:
                to_test.append(l)
                if l == msg:
                    to_test.append(l) # duplicate
            self._test_lc_enc(to_test, True)

    def test_lc_more_act(self):
        # test serialization of activities
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        act2 = TestGrounding._get_obj("2","android.app.Activity")
        bundle = TestGrounding._get_obj("2","android.os.Bundle")
        lifecycle = TestGrounding._get_obj("3","android.app.Application.ActivityLifecycleCallbacks")
        view1 = TestGrounding._get_obj("4","android.view.View")
        view2 = TestGrounding._get_obj("5","android.view.View")

        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, None)
        helper2 = TestFlowDroid.ActivityHelper("android.app.Activity", act2, bundle, lifecycle, None)


        to_run = [(helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED),
                  (helper1, Activity.ONSTART),
                  (helper1, Activity.ONACTIVITYSTARTED),
                  (helper1, Activity.ONRESTOREINSTANCESTATE),
                  (helper1, Activity.ONPOSTCREATE),
                  (helper1, Activity.ONRESUME),
                  (helper1, Activity.ONACTIVITYRESUMED),
                  (helper1, Activity.ONPOSTRESUME),
                  (helper1, Activity.ONPAUSE),
                  (helper1, Activity.ONACTIVITYPAUSED),
                  (helper1, Activity.ONCREATEDESCRIPTION),
                  (helper1, Activity.ONSAVEINSTANCESTATE),
                  (helper1, Activity.ONACTIVITYSAVEINSTANCESTATE),
                  (helper1, Activity.ONSTOP),
                  (helper1, Activity.ONACTIVITYSTOPPED),
                  (helper1, Activity.ONRESTART),
                  (helper1, Activity.ONDESTROY),
                  (helper1, Activity.ONACTIVITYDESTROYED),
                  (helper2, Activity.ONCREATE),
                  (helper2, Activity.ONACTIVITYCREATED),
                  (helper2, Activity.ONSTART),
                  (helper2, Activity.ONACTIVITYSTARTED),
                  (helper2, Activity.ONRESTOREINSTANCESTATE),
                  (helper2, Activity.ONPOSTCREATE),
                  (helper2, Activity.ONRESUME),
                  (helper2, Activity.ONACTIVITYRESUMED),
                  (helper2, Activity.ONPOSTRESUME),
                  (helper2, Activity.ONPAUSE),
                  (helper2, Activity.ONACTIVITYPAUSED),
                  (helper2, Activity.ONCREATEDESCRIPTION),
                  (helper2, Activity.ONSAVEINSTANCESTATE),
                  (helper2, Activity.ONACTIVITYSAVEINSTANCESTATE),
                  (helper2, Activity.ONSTOP),
                  (helper2, Activity.ONACTIVITYSTOPPED),
                  (helper2, Activity.ONRESTART),
                  (helper2, Activity.ONDESTROY),
                  (helper2, Activity.ONACTIVITYDESTROYED),
                  (helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED),
                  (helper1, Activity.ONSTART),
                  (helper1, Activity.ONACTIVITYSTARTED),
                  (helper1, Activity.ONRESTOREINSTANCESTATE),
                  (helper1, Activity.ONPOSTCREATE),
                  (helper1, Activity.ONRESUME),
                  (helper1, Activity.ONACTIVITYRESUMED),
                  (helper1, Activity.ONPOSTRESUME),
                  (helper1, Activity.ONPAUSE),
                  (helper1, Activity.ONACTIVITYPAUSED),
                  (helper1, Activity.ONCREATEDESCRIPTION),
                  (helper1, Activity.ONSAVEINSTANCESTATE),
                  (helper1, Activity.ONACTIVITYSAVEINSTANCESTATE),
                  (helper1, Activity.ONSTOP),
                  (helper1, Activity.ONACTIVITYSTOPPED),
                  (helper1, Activity.ONRESTART),
                  (helper1, Activity.ONDESTROY),
                  (helper1, Activity.ONACTIVITYDESTROYED)]
        self._test_lc_multi(to_run, True)

    def test_lc_more_act_2(self):
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        act2 = TestGrounding._get_obj("2","android.app.Activity")
        bundle = TestGrounding._get_obj("2","android.os.Bundle")
        lifecycle = TestGrounding._get_obj("3","android.app.Application.ActivityLifecycleCallbacks")
        view1 = TestGrounding._get_obj("4","android.view.View")
        view2 = TestGrounding._get_obj("5","android.view.View")

        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, None)
        helper2 = TestFlowDroid.ActivityHelper("android.app.Activity", act2, bundle, lifecycle, None)

        to_run = [(helper1, Activity.ONCREATE),
                  (helper2, Activity.ONCREATE), # should not move
                  (helper1, Activity.ONACTIVITYCREATED)]
        self._test_lc_multi(to_run, False)

    def test_activity_cb_out(self):
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        objoutlc = TestGrounding._get_obj("2",TestFlowDroid.ObjOutLcHelper.CLASS_NAME)
        bundle = TestGrounding._get_obj("2","android.os.Bundle")
        lifecycle = TestGrounding._get_obj("3","android.app.Application.ActivityLifecycleCallbacks")
        view = TestGrounding._get_obj("4","android.view.View")
        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, None)
        helper_out = TestFlowDroid.ObjOutLcHelper(objoutlc)

        to_run = [(helper1, Activity.ONCREATE),
                  (helper_out, TestFlowDroid.ObjOutLcHelper.RANDOMCB)]

        self._test_lc_multi(to_run, True)

    def test_activity_cb_in_lc(self):
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        objoutlc = TestGrounding._get_obj("2",TestFlowDroid.ObjOutLcHelper.CLASS_NAME)
        bundle = TestGrounding._get_obj("2","android.os.Bundle")
        lifecycle = TestGrounding._get_obj("3","android.app.Application.ActivityLifecycleCallbacks")
        view = TestGrounding._get_obj("4","android.view.View")
        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, None)
        helper_out = TestFlowDroid.ObjOutLcHelper(objoutlc)

        # before resume
        to_run = [(helper1, Activity.ONCREATE),
                  (helper1, TestFlowDroid.ActivityHelper.RANDOMCB)]
        self._test_lc_multi(to_run, False)

        # after on resume
        to_run = [(helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED),
                  (helper1, Activity.ONSTART),
                  (helper1, Activity.ONACTIVITYSTARTED),
                  (helper1, Activity.ONRESTOREINSTANCESTATE),
                  (helper1, Activity.ONPOSTCREATE),
                  (helper1, Activity.ONRESUME),
                  (helper1, Activity.ONACTIVITYRESUMED),
                  (helper1, Activity.ONPOSTRESUME), # CB can run after ONPOSTONRESUME
                  (helper1, TestFlowDroid.ActivityHelper.RANDOMCB),
                  (helper1, Activity.ONPAUSE)]
        self._test_lc_multi(to_run, True)

        # after on pause
        to_run  = [(helper1, Activity.ONCREATE),
                   (helper1, Activity.ONACTIVITYCREATED),
                   (helper1, Activity.ONSTART),
                   (helper1, Activity.ONACTIVITYSTARTED),
                   (helper1, Activity.ONRESTOREINSTANCESTATE),
                   (helper1, Activity.ONPOSTCREATE),
                   (helper1, Activity.ONRESUME),
                   (helper1, Activity.ONACTIVITYRESUMED),
                   (helper1, Activity.ONPOSTRESUME),
                   (helper1, Activity.ONPAUSE),
                   (helper1, Activity.ONPOSTRESUME), # CB cannot run after ONPOSTONRESUME
                   (helper1, Activity.ONACTIVITYPAUSED),
                   (helper1, Activity.ONCREATEDESCRIPTION),
                   (helper1, Activity.ONSAVEINSTANCESTATE),
                   (helper1, Activity.ONACTIVITYSAVEINSTANCESTATE),
                   (helper1, Activity.ONSTOP),
                   (helper1, Activity.ONACTIVITYSTOPPED),
                   (helper1, Activity.ONRESTART),
                   (helper1, Activity.ONDESTROY),
                   (helper1, Activity.ONACTIVITYDESTROYED)]
        self._test_lc_multi(to_run, False)

    def test_activity_cb_in_lc_registration(self):
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        objoutlc = TestGrounding._get_obj("2",TestFlowDroid.ObjOutLcHelper.CLASS_NAME)
        bundle = TestGrounding._get_obj("3","android.os.Bundle")
        lifecycle = TestGrounding._get_obj("4","android.app.Application.ActivityLifecycleCallbacks")
        listener = TestGrounding._get_obj("5","android.view.View$OnClickListener")
        view = TestGrounding._get_obj("6","android.view.View")

        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, view, listener)
        helper_out = TestFlowDroid.ObjOutLcHelper(objoutlc)
        helper_listener = TestFlowDroid.ViewListenerHelper(listener, view)

        # before resume
        to_run = [(helper1, Activity.ONCREATE),
                  (helper_listener, TestFlowDroid.ViewListenerHelper.ONCLICK)]
        self._test_lc_multi(to_run, False)

        # after on resume
        to_run = [(helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED),
                  (helper1, Activity.ONSTART),
                  (helper1, Activity.ONACTIVITYSTARTED),
                  (helper1, Activity.ONRESTOREINSTANCESTATE),
                  (helper1, Activity.ONPOSTCREATE),
                  (helper1, Activity.ONRESUME),
                  (helper1, Activity.ONACTIVITYRESUMED),
                  (helper1, Activity.ONPOSTRESUME), # CB can run after ONPOSTONRESUME
                  (helper_listener, TestFlowDroid.ViewListenerHelper.ONCLICK), 
                  (helper1, TestFlowDroid.ActivityHelper.RANDOMCB),
                  (helper1, Activity.ONPAUSE)]
        self._test_lc_multi(to_run, True)


    def test_fragment_lc(self):
        # test the fragment lifecycle
        # activity + fragment: act lifecycle, frag lifecycle
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        frag1 = TestGrounding._get_obj("2", "android.app.Fragment")
        bundle = TestGrounding._get_obj("3","android.os.Bundle")
        inflater = TestGrounding._get_obj("4","android.view.LayoutInflater")
        viewgroup = TestGrounding._get_obj("5","android.view.ViewGroup")
        view1 = TestGrounding._get_obj("6","android.view.View")
        view2 = TestGrounding._get_obj("8","android.view.View")
        lifecycle = TestGrounding._get_obj("7","android.app.Application.ActivityLifecycleCallbacks")

        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, None)
        helper2 = TestFlowDroid.FragmentHelper("android.app.Fragment", frag1, act1, bundle,
                                               inflater, viewgroup, view2)

        # test different entry points for fragment
        entry_points = [(helper2, Fragment.ONATTACHFRAGMENT),
                        (helper2, Fragment.ONATTACH)]
        for ep in entry_points:
            to_run = [(helper1, Activity.ONCREATE),
                      (helper1, Activity.ONACTIVITYCREATED), # begin the fragment lifecycle
                      ep]
            self._test_lc_multi(to_run, True)

        # test a possible fragment run
        to_run = [(helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED), # begin the fragment lifecycle
                  (helper2, Fragment.ONATTACHFRAGMENT),
                  (helper2, Fragment.ONATTACH),
                  (helper2, Fragment.ONCREATE),
                  (helper2, Fragment.ONCREATEVIEW),
                  (helper2, Fragment.ONVIEWCREATED),
                  (helper2, Fragment.ONACTIVITYCREATED),
                  (helper2, Fragment.ONSTART),
                  (helper2, Fragment.ONRESUME),
                  (helper2, Fragment.ONPAUSE),
                  (helper2, Fragment.ONSAVEINSTANCESTATE),
                  (helper2, Fragment.ONSTOP),
                  (helper2, Fragment.ONDESTROYVIEW),
                  (helper2, Fragment.ONDESTROY),
                  (helper2, Fragment.ONDETACH),
                  (helper1, Activity.ONSTART),
                  (helper1, Activity.ONACTIVITYSTARTED),
                  (helper1, Activity.ONRESTOREINSTANCESTATE),
                  (helper1, Activity.ONPOSTCREATE),
                  (helper1, Activity.ONRESUME),
                  (helper1, Activity.ONACTIVITYRESUMED),
                  (helper1, Activity.ONPOSTRESUME)]
        self._test_lc_multi(to_run, True)

        # test multiple fragment runs
        to_run = [(helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED), # begin the fragment lifecycle
                  (helper2, Fragment.ONATTACHFRAGMENT),
                  (helper2, Fragment.ONATTACH),
                  (helper2, Fragment.ONCREATE),
                  (helper2, Fragment.ONCREATEVIEW),
                  (helper2, Fragment.ONVIEWCREATED),
                  (helper2, Fragment.ONACTIVITYCREATED),
                  (helper2, Fragment.ONSTART),
                  (helper2, Fragment.ONRESUME),
                  (helper2, Fragment.ONPAUSE),
                  (helper2, Fragment.ONSAVEINSTANCESTATE),
                  (helper2, Fragment.ONSTOP),
                  (helper2, Fragment.ONDESTROYVIEW),
                  (helper2, Fragment.ONDESTROY),
                  (helper2, Fragment.ONDETACH),
                  (helper1, Activity.ONSTART),
                  (helper1, Activity.ONACTIVITYSTARTED),
                  (helper1, Activity.ONRESTOREINSTANCESTATE),
                  (helper1, Activity.ONPOSTCREATE),
                  (helper1, Activity.ONRESUME),
                  (helper1, Activity.ONACTIVITYRESUMED),
                  (helper1, Activity.ONPOSTRESUME),
                  (helper1, Activity.ONPAUSE),
                  (helper1, Activity.ONACTIVITYPAUSED),
                  (helper1, Activity.ONCREATEDESCRIPTION),
                  (helper1, Activity.ONSAVEINSTANCESTATE),
                  (helper1, Activity.ONACTIVITYSAVEINSTANCESTATE),
                  (helper1, Activity.ONSTOP),
                  (helper1, Activity.ONACTIVITYSTOPPED),
                  (helper1, Activity.ONRESTART),
                  (helper1, Activity.ONDESTROY),
                  (helper1, Activity.ONACTIVITYDESTROYED),
                  (helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED), # begin the fragment lifecycle
                  (helper2, Fragment.ONATTACHFRAGMENT),
                  (helper2, Fragment.ONATTACH),
                  (helper2, Fragment.ONCREATE),
                  (helper2, Fragment.ONCREATEVIEW),
                  (helper2, Fragment.ONVIEWCREATED),
                  (helper2, Fragment.ONACTIVITYCREATED),
                  (helper2, Fragment.ONSTART),
                  (helper2, Fragment.ONRESUME),
                  (helper2, Fragment.ONPAUSE),
                  (helper2, Fragment.ONSAVEINSTANCESTATE),
                  (helper2, Fragment.ONSTOP),
                  (helper2, Fragment.ONDESTROYVIEW),
                  (helper2, Fragment.ONDESTROY),
                  (helper2, Fragment.ONDETACH),
                  (helper1, Activity.ONSTART)]
        self._test_lc_multi(to_run, True)

    def test_block_fragment_lc(self):
        # test when activity/lifecycle blocks each other
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        frag1 = TestGrounding._get_obj("2", "android.app.Fragment")
        bundle = TestGrounding._get_obj("3","android.os.Bundle")
        inflater = TestGrounding._get_obj("4","android.view.LayoutInflater")
        viewgroup = TestGrounding._get_obj("5","android.view.ViewGroup")
        view = TestGrounding._get_obj("6","android.view.View")
        lifecycle = TestGrounding._get_obj("7","android.app.Application.ActivityLifecycleCallbacks")

        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, None)
        helper2 = TestFlowDroid.FragmentHelper("android.app.Fragment", frag1, act1, bundle,
                                               inflater, viewgroup, view)

        # test an out-of order fragment run
        to_run = [(helper1, Activity.ONCREATE),
                  (helper2, Fragment.ONATTACH), # cannot run in the "wrong" position
                  (helper1, Activity.ONACTIVITYCREATED)] # begin the fragment lifecycle
        self._test_lc_multi(to_run, False)

        # # test an out-of order activity run
        # to_run = [(helper1, Activity.ONCREATE),
        #           (helper1, Activity.ONACTIVITYCREATED), # begin the fragment lifecycle
        #           (helper2, Fragment.ONATTACH),
        #           (helper1, Activity.ONSTART), # activity cannot be run here
        #           (helper2, Fragment.ONATTACH),
        #           (helper2, Fragment.ONCREATE)]
        # self._test_lc_multi(to_run, False)


    def test_print_model(self):
        act1 = TestGrounding._get_obj("1","android.app.Activity")
        objoutlc = TestGrounding._get_obj("2",TestFlowDroid.ObjOutLcHelper.CLASS_NAME)
        bundle = TestGrounding._get_obj("3","android.os.Bundle")
        lifecycle = TestGrounding._get_obj("4","android.app.Application.ActivityLifecycleCallbacks")
        listener = TestGrounding._get_obj("5","android.view.View$OnClickListener")
        view = TestGrounding._get_obj("6","android.view.View")

        helper1 = TestFlowDroid.ActivityHelper("android.app.Activity", act1, bundle, lifecycle, view, listener)
        helper_out = TestFlowDroid.ObjOutLcHelper(objoutlc)
        helper_listener = TestFlowDroid.ViewListenerHelper(listener, view)

        # after on resume
        to_run = [(helper1, Activity.ONCREATE),
                  (helper1, Activity.ONACTIVITYCREATED),
                  (helper1, Activity.ONSTART),
                  (helper1, Activity.ONACTIVITYSTARTED),
                  (helper1, Activity.ONRESTOREINSTANCESTATE),
                  (helper1, Activity.ONPOSTCREATE),
                  (helper1, Activity.ONRESUME),
                  (helper1, Activity.ONACTIVITYRESUMED),
                  (helper1, Activity.ONPOSTRESUME), # CB can run after ONPOSTONRESUME
                  (helper_listener, TestFlowDroid.ViewListenerHelper.ONCLICK), 
                  (helper1, TestFlowDroid.ActivityHelper.RANDOMCB),
                  (helper1, Activity.ONPAUSE)]

        trace = self._get_trace_multi(to_run)
        enc = TSEncoder(trace, [], False, None, True)
        # TODO: check if output works
        enc.fd_builder.print_model(sys.stdout)


    def _test_sim(self, trace, expected_result):
#        enc = TSEncoder(trace, [], True, None, True)
        enc = TSEncoder(trace, [], False, None, True)
        (step, cex, _) = self._simulate(enc)

        if (not cex is None):
            stringio = StringIO()
            printer = CexPrinter(enc.mapback, cex, stringio)
            printer.print_cex()
            print stringio.getvalue()

        self.assertTrue( (not cex is None) == expected_result)

    def _get_trace_multi(self,obj_cb_seq):
        trace = CTrace()
        for (helper, cb_name) in obj_cb_seq:
            cb = helper.get_cb(cb_name)
            trace.add_msg(cb)
        return trace

    def _test_lc_multi(self, obj_cb_seq, expected_result):
        trace = self._get_trace_multi(obj_cb_seq)
        self._test_sim(trace, expected_result)

    def _test_lc_enc(self, cb_sequence, expected_result):
        # activity: simulate lifecycle
        act = TestGrounding._get_obj("1","android.app.Activity")
        bundle = TestGrounding._get_obj("2","android.os.Bundle")
        lifecycle = TestGrounding._get_obj("3","android.app.Application.ActivityLifecycleCallbacks")
        view = TestGrounding._get_obj("4","android.view.View")
        helper = TestFlowDroid.ActivityHelper("android.app.Activity", act, bundle, lifecycle, None)

        trace = CTrace()
        for cb_name in cb_sequence:
            cb = helper.get_cb(cb_name)
            trace.add_msg(cb)

        self._test_sim(trace, expected_result)


    def _simulate(self, ts_enc):
        ts = ts_enc.get_ts_encoding()
        trace_enc = ts_enc.get_trace_encoding()

        # print "TRACE ENC"
        # for step in trace_enc:
        #     print trace_enc

        bmc = BMC(ts_enc.helper, ts, FALSE_PYSMT())
        (step, cex, _) = bmc.simulate(trace_enc)
        return (step, cex, _)


    def _get_fdm(self, trace):
        enc = TSEncoder(trace, [])
        fd_builder = FlowDroidModelBuilder(enc.trace,
                                           enc.gs.trace_map)
        fd_builder.init_relation(set([]))

        return fd_builder


    def _create_activity(self):
        obj_id = TestGrounding._get_obj("objid_%d" % self.get_obj_id(), "android.app.Activity")
        obj_bundle_id = TestGrounding._get_obj("objid_%d" % self.get_obj_id(), "android.os.Bundle")
        cb = CCallback(1, 1, "", "void android.app.Activity.onCreate(android.os.Bundle)",
                       [obj_id, obj_bundle_id],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Activity","onCreate(android.os.Bundle)", False)])
        return (cb, obj_id)

    def _create_fragment(self):
        obj_id = TestGrounding._get_obj("objid_%d" % self.get_obj_id(), "android.app.Fragment")
        obj_bundle_id = TestGrounding._get_obj("objid_%d" % self.get_obj_id(), "android.os.Bundle")

        cb = CCallback(1, 1, "", "void android.app.Fragment.onCreate(android.os.Bundle)",
                       [obj_id, obj_bundle_id],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Fragment","onCreate(android.os.Bundle)", False)])
        return (cb, obj_id)

    def _create_view(self):
        obj_id = TestGrounding._get_obj("objid_%d" % self.get_obj_id(),"android.view.View")
        cb = CCallback(1, 1, "", "void android.view.View.<init>()",
                       [obj_id],
                       None,
                       [TestGrounding._get_fmwkov("void android.view.View","<init>()", False)])
        return (cb, obj_id)

    def _attach_fragment_to_activity(self, activity, fragment):
        # public void onAttach (Context context)
        cb = CCallback(1, 1, "", "void android.app.Fragment.onAttach(android.app.Activity)",
                       [fragment, activity],
                       None,
                       [TestGrounding._get_fmwkov("void android.app.Fragment","onAttach(android.app.Activity)", False)])
        return cb

    def _attach_view_to_activity(self, activity, view):
        ci = CCallin(1, 1, "", "android.view.View android.app.Activity.findViewById(int)",
                     [activity, TestGrounding._get_int(1)], view)
        return ci

    def _add_view_on_measure(self, view):
        cb = CCallback(1, 1, "", "void android.view.View.onMeasure(int,int)",
                       [view, TestGrounding._get_int(1), TestGrounding._get_int(1)],
                       None,
                       [TestGrounding._get_fmwkov("void android.view.View","onMeasure(int,int)", False)])
        return cb



    class ActivityHelper:
        RANDOMCB = "RANDOMCB"

        def __init__(self, class_name, act, bundle, lifecycle, view=None, listener=None):

            self.class_name = class_name
            self.bundle = bundle
            self.act = act
            self.lifecycle = lifecycle
            self.cb_map = {}
            self.view = view

            for (method_name, key) in [("onCreate(android.os.Bundle)", Activity.ONCREATE),
                                       ("onPostCreate(android.os.Bundle)", Activity.ONPOSTCREATE),
                                       ("onSaveInstanceState(android.os.Bundle)", Activity.ONSAVEINSTANCESTATE),
                                       ("onRestoreInstanceState(android.os.Bundle)", Activity.ONRESTOREINSTANCESTATE)]:
                cb = CCallback(1, 1, "", "void %s.%s" % (class_name, method_name),
                               [act, bundle],
                               None,
                               [TestGrounding._get_fmwkov("void %s" % class_name, method_name, False)])

                if (Activity.ONCREATE == key):
                    if not view is None:
                        ci = CCallin(1, 1, "", "android.view.View %s.findViewById(int)" % class_name,
                                     [act],
                                     view)
                        cb.add_msg(ci)

                        if not listener is None:
                            ci = CCallin(1, 1, "", "void android.view.View.setOnClickListener(android.view.View$OnClickListener)",
                                         [view, listener],
                                         None)
                            cb.add_msg(ci)
                self.cb_map[key] = cb


            for (method_name, key) in [("onDestroy()", Activity.ONDESTROY),
                                       ("onPause()", Activity.ONPAUSE),
                                       ("onPostResume()", Activity.ONPOSTRESUME),
                                       ("onRestart()", Activity.ONRESTART),
                                       ("onResume()", Activity.ONRESUME),
                                       ("onStart()", Activity.ONSTART),
                                       ("onStop()", Activity.ONSTOP)]:
                cb = CCallback(1, 1, "", "void %s.%s" % (class_name, method_name),
                               [act],
                               None,
                               [TestGrounding._get_fmwkov("void %s" % class_name, method_name, False)])
                self.cb_map[key] = cb

            cb = CCallback(1, 1, "", "java.lang.CharSequence %s.onCreateDescription()" % (class_name),
                           [act],
                           None,
                           [TestGrounding._get_fmwkov("java.lang.CharSequence %s" % class_name,
                                                      "onCreateDescription()", False)])
            self.cb_map[Activity.ONCREATEDESCRIPTION] = cb

            for (method_name, key) in [("onActivityStarted", Activity.ONACTIVITYSTARTED),
                                       ("onActivityStopped", Activity.ONACTIVITYSTOPPED),
                                       ("onActivityResumed", Activity.ONACTIVITYRESUMED),
                                       ("onActivityPaused", Activity.ONACTIVITYPAUSED),
                                       ("onActivityDestroyed", Activity.ONACTIVITYDESTROYED)]:
                cb = CCallback(1, 1, "", "void android.app.Application.ActivityLifecycleCallbacks.%s(%s)" % (method_name,class_name),
                               [lifecycle, act],
                               None,
                               [TestGrounding._get_fmwkov("void android.app.Application.ActivityLifecycleCallbacks", "%s(%s)" % (method_name, class_name), False)])
                self.cb_map[key] = cb

            for (method_name, key) in [("onActivityCreated", Activity.ONACTIVITYCREATED),
                                       ("onActivitySaveInstanceState", Activity.ONACTIVITYSAVEINSTANCESTATE)]:
                cb = CCallback(1, 1, "", "void android.app.Application.ActivityLifecycleCallbacks.%s(%s,android.os.Bundle)" % (method_name,class_name),
                               [lifecycle, act, bundle],
                               None,
                               [TestGrounding._get_fmwkov("void android.app.Application.ActivityLifecycleCallbacks", "%s(%s,android.os.Bundle)" % (method_name, class_name), False)])
                self.cb_map[key] = cb

            cb = CCallback(1, 1, "", "void %s.randomcb " % class_name,
                           [act],
                           None,
                           [TestGrounding._get_fmwkov("void %s" %  class_name, "randomcb", False)])
            self.cb_map[TestFlowDroid.ActivityHelper.RANDOMCB] = cb

        def get_cb(self, key):
            return self.cb_map[key]

    class FragmentHelper:
        RANDOMCB = "RANDOMCB"

        def get_cb(self, key):
            return self.cb_map[key]

        def __init__(self, class_name, fragment, act, bundle,
                     inflater, viewgroup, view):
            self.class_name = class_name
            self.fragment = fragment
            self.act = act
            self.bundle = bundle
            self.inflater = inflater
            self.viewgroup = viewgroup
            self.view = view
            self.cb_map = {}

            for method_name, key in [("onStart()", Fragment.ONSTART),
                                     ("onResume()", Fragment.ONRESUME),
                                     ("onPause()", Fragment.ONPAUSE),
                                     ("onStop()", Fragment.ONSTOP),
                                     ("onDestroyView()", Fragment.ONDESTROYVIEW),
                                     ("onDestroy()", Fragment.ONDESTROY),
                                     ("onDetach()", Fragment.ONDETACH)]:
                cb = CCallback(1, 1, "", "void %s.%s" % (class_name, method_name),
                               [fragment],
                               None,
                               [TestGrounding._get_fmwkov("void %s" % class_name, method_name, False)])
                self.cb_map[key] = cb


            for method_name, key in [("onCreate(android.os.Bundle)", Fragment.ONCREATE),
                                     ("onActivityCreated(android.os.Bundle)", Fragment.ONACTIVITYCREATED),
                                     ("onSaveInstanceState(android.os.Bundle)", Fragment.ONSAVEINSTANCESTATE)]:
                cb = CCallback(1, 1, "", "void %s.%s" % (class_name, method_name),
                               [fragment, bundle],
                               None,
                               [TestGrounding._get_fmwkov("void %s" % class_name, method_name, False)])
                self.cb_map[key] = cb

            for method_name, key in [("onAttach(android.app.Activity)", Fragment.ONATTACH),
                                     ("onViewStateRestored(android.app.Activity)", Fragment.ONVIEWSTATERESTORED)]:
                cb = CCallback(1, 1, "", "void %s.%s" % (class_name, method_name),
                               [fragment, act],
                               None,
                               [TestGrounding._get_fmwkov("void %s" % class_name, method_name, False)])
                self.cb_map[key] = cb

            for method_name, key in [("onViewCreated(android.view.View,android.os.Bundle)", Fragment.ONVIEWCREATED)]:
                cb = CCallback(1, 1, "", "void %s.%s" % (class_name, method_name),
                               [fragment, view, bundle],
                               None,
                               [TestGrounding._get_fmwkov("void %s" % class_name, method_name, False)])
                self.cb_map[key] = cb

            for method_name, key in [("onCreateView(android.view.LayoutInflater,android.view.ViewGroup,android.os.Bundle)", Fragment.ONCREATEVIEW)]:
                cb = CCallback(1, 1, "", "android.view.View %s.%s" % (class_name, method_name),
                               [fragment, inflater, viewgroup, bundle],
                               view,
                               [TestGrounding._get_fmwkov("android.view.View %s" % class_name, method_name, False)])
                self.cb_map[key] = cb

            cb = CCallback(1, 1, "", "void android.app.Activity.onAttachFragment(%s)" % class_name,
                           [act,fragment],
                           None,
                           [TestGrounding._get_fmwkov("void android.app.Activity", "onAttachFragment(%s)" % class_name, False)])
            self.cb_map[Fragment.ONATTACHFRAGMENT] = cb

            cb = CCallback(1, 1, "", "void %s.randomcb()" % class_name,
                           [act],
                           None,
                           [TestGrounding._get_fmwkov("void %s" %  class_name, "randomcb()", False)])
            self.cb_map[TestFlowDroid.FragmentHelper.RANDOMCB] = cb

    class ObjOutLcHelper:
        RANDOMCB = "RANDOMCB"
        CLASS_NAME = "android.app.ObjOutLc"

        def get_cb(self, key):
            return self.cb_map[key]

        def __init__(self, obj):
            self.cb_map = {}
            cb = CCallback(1, 1, "", "void %s.randomcb()" % TestFlowDroid.ObjOutLcHelper.CLASS_NAME,
                           [obj],
                           None,
                           [TestGrounding._get_fmwkov("void %s" % TestFlowDroid.ObjOutLcHelper.CLASS_NAME, "randomcb()", False)])
            self.cb_map[TestFlowDroid.ObjOutLcHelper.RANDOMCB] = cb

    class ViewListenerHelper:
        CLASS_NAME = "android.view.View$OnClickListener"
        ONCLICK = "ONCLICK"

        def get_cb(self, key):
            return self.cb_map[key]

        def __init__(self, listener, view):
            self.cb_map = {}
            cb = CCallback(1, 1, "", "void %s.onClick(android.view.View)" % TestFlowDroid.ViewListenerHelper.CLASS_NAME,
                           [listener,view],
                           None,
                           [TestGrounding._get_fmwkov("void %s" % TestFlowDroid.ViewListenerHelper.CLASS_NAME, "onClick(android.view.View)", False)])
            self.cb_map[TestFlowDroid.ViewListenerHelper.ONCLICK] = cb


