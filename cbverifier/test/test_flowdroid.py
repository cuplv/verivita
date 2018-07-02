""" Test the creation of the flowdroid model """

import sys
import logging
import unittest


from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest


from cbverifier.encoding.flowdroid_model.lifecycle_constants import Activity

class TestFlowDroid(unittest.TestCase):

    def test_const_classes(self):
        """ Test the creation of ad-hoc classes used to lookup methods """
        activity = Activity("android.app.Activity")
        self.assertTrue(activity.has_methods_names(Activity.INIT))
        "[CB] [ENTRY] [l]  android.app.Activity <init>()" in activity.get_methods_names(Activity.INIT)

        activity = Activity("android.support.v4.app.FragmentActivity")
        self.assertTrue(activity.has_methods_names(Activity.INIT))
        "[CB] [ENTRY] [l]  android.support.v4.app.FragmentActivity <init>()" in activity.get_methods_names(Activity.INIT)

