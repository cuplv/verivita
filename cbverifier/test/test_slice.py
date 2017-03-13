""" Test the grounding of specifications

"""

import sys
import logging
import unittest
import os




try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.driver import i_slice

from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, FrameworkOverride, CValue, TraceConverter
from cbverifier.specs.spec_ast import *
from cbverifier.specs.spec import Spec, spec_parser

from cbverifier.traces.ctrace import CTraceSerializer


from cStringIO import StringIO

class TestSlice(unittest.TestCase):
    @staticmethod
    def _get_obj(objId, objType):
        v = CValue()
        v.is_null = False
        v.type = objType
        v.object_id = objId
        return v
    @staticmethod
    def _get_fmwkov(cname, mname, is_int):
        return FrameworkOverride(cname, mname, is_int)
    @staticmethod
    def _get_int(intValue):
        v = CValue()
        v.is_null = False
        v.type = TraceConverter.JAVA_INT
        v.value = intValue
        return v
    def test_slice(self):
        trace = CTrace()
        cb1 = CCallback(6, 1, "", "doSomethingCb()",
                        [self._get_obj("1","string")],
                        None, [self._get_fmwkov("","doSomethingCb()",False)])
        trace.add_msg(cb1)
        ci1 = CCallin(7, 1, "", "doSomethingCi()",
                      [self._get_obj("1","string"), self._get_obj('3','string')],
                      None)
        cb1.add_msg(ci1)
        ci2 = CCallin(9, 1, "", "doSomethingCi(string)",
                      [self._get_obj("1","string"),
                      self._get_obj('2',"string")],
                      None)
        cb1.add_msg(ci2)
        cb2 = CCallback(10,1,"","meh()", [self._get_obj('00','string')])
        trace.add_msg(cb2)
        i_slice(trace,"3")
        assert(cb1 in trace.children)
        assert(ci2 not in trace.children[0].children)
        assert(cb2 not in trace.children)