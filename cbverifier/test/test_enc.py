""" Test the encoding """

""" Test the grounding of specifications

"""

import sys
import logging
import unittest

from ply.lex import LexToken
import ply.yacc as yacc


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.grounding import GroundSpecs
from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue
from cbverifier.specs.spec_ast import *
from cbverifier.specs.spec import Spec

from cbverifier.test.test_grounding import TestGrounding


class TestEnc(unittest.TestCase):

    def test_get_key(self):
        """ Test the retrieval for the key of the message """

        self.assertTrue("method(1,2,3)" == TSEncoder.get_key("method", ["1","2","3"]))
        self.assertTrue("method()" == TSEncoder.get_key("method", []))

        with self.assertRaises(AssertionError):
            TSEncoder.get_key("", [])

        with self.assertRaises(AssertionError):
            TSEncoder.get_key(None, [])

    def test_get_value_key(self):
        obj = TestGrounding._get_obj("1", "string")
        res = TSEncoder.get_value_key(obj)
        self.assertTrue(res == "1")

        obj = TestGrounding._get_obj("1", "string")
        obj.is_null = True
        res = TSEncoder.get_value_key(obj)
        self.assertTrue(res == "NULL")

        value = TestGrounding._get_int("1")
        res = TSEncoder.get_value_key(value)
        self.assertTrue(res == "1")

        value = TestGrounding._get_int("1")
        value.is_null = True
        res = TSEncoder.get_value_key(value)
        self.assertTrue(res == "NULL")

    def test_get_msg_key(self):
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [TestGrounding._get_obj("1","string")],
                       None, ["string"], [], [])
        res = TSEncoder.get_msg_key(cb)
        self.assertTrue("doSomethingCb(1)", res)

        cb = CCallback(1, 1, "", "doSomethingCb",
                       [TestGrounding._get_obj("1","string"),
                        TestGrounding._get_int(1)],
                       None, ["string"], [], [])
        res = TSEncoder.get_msg_key(cb)
        self.assertTrue("doSomethingCb(1,1)", res)

        ci = CCallin(1, 1, "", "doSomethingCi",
                     [TestGrounding._get_obj("1","string")],
                     None)
        res = TSEncoder.get_msg_key(ci)
        self.assertTrue("doSomethingCi(1)", res)

        ci = CCallin(1, 1, "", "doSomethingCi",
                     [],
                     None)
        res = TSEncoder.get_msg_key(ci)
        self.assertTrue("doSomethingCi(1)", res)

    def test_get_key_from_call(self):
        spec_list = Spec.get_specs_from_string("SPEC TRUE |- l.m1(); " +
                                               "SPEC TRUE |- l.m1(a,b,c)")
        assert spec_list is not None

        binding = TestGrounding.newAssign(
            [new_id('l'),new_id("a"),new_id("b"),new_id("c")],
            [TestGrounding._get_obj("1","string"),
             TestGrounding._get_obj("2","string"),
             TestGrounding._get_int(1),
             TestGrounding._get_int(2)])

        calls_nodes = []
        for s in spec_list:
            ground_s = GroundSpecs._substitute(s, binding)
            msg = get_spec_rhs(ground_s)
            assert get_node_type(msg) == CALL
            calls_nodes.append(msg)
        assert (len(calls_nodes) == len(spec_list))

        res = TSEncoder.get_key_from_call(calls_nodes[0])
        self.assertTrue("m1(1)" == res)
        res = TSEncoder.get_key_from_call(calls_nodes[1])
        self.assertTrue("m1(1,2,1,2)" == res)





