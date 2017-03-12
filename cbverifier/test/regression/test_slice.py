""" Test the grounding of specifications

"""

import sys
import logging
import unittest
import os

from ply.lex import LexToken
import ply.yacc as yacc


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import cbverifier.test.examples
from cbverifier.encoding.grounding import GroundSpecs, Assignments, bottom_value, TraceSpecConverter
from cbverifier.encoding.grounding import AssignmentsSet, TraceMap
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
        v.value = objId
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
                      [self._get_obj("1","string"), self._get_obj('2','string')],
                      None)
        cb1.add_msg(ci1)
        ci2 = CCallin(8, 1, "", "doSomethingCi(int)",
                      [self._get_obj("1","string"),
                      self._get_int(2)],
                      None)
        cb1.add_msg(ci2)