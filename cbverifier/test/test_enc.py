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

from pysmt.shortcuts import is_sat, is_valid
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne


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


    def test_trace_stats(self):
        def _test_eq(ts_enc, length, msgs, cb_set, ci_set):
            # print ts_enc.trace_length
            # print ts_enc.msgs
            # print ts_enc.cb_set
            # print ts_enc.ci_set

            self.assertTrue(ts_enc.trace_length == length and
                            ts_enc.msgs == msgs and
                            ts_enc.cb_set == cb_set and
                            ts_enc.ci_set == ci_set)


        ts_enc = TSEncoder(CTrace(), [])
        _test_eq(ts_enc, 0, set(), set(), set())

        trace = CTrace()
        cb = CCallback(1, 1, "", "doSomethingCb", [], None, [], [], [])
        trace.add_msg(cb)
        ts_enc = TSEncoder(trace, [])
        _test_eq(ts_enc, 1, set(["doSomethingCb()"]), set(["doSomethingCb()"]), set())

        trace = CTrace()
        cb = CCallback(1, 1, "", "doSomethingCb", [], None, [], [], [])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",[], None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "doSomethingCb", [], None, [], [], [])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",[], None)
        cb.add_msg(ci)

        ts_enc = TSEncoder(trace, [])
        _test_eq(ts_enc, 4, set(["doSomethingCb()","doSomethingCi()"]),
                 set(["doSomethingCb()"]), set(["doSomethingCi()"]))

        trace = CTrace()

        cb = CCallback(1, 1, "", "cb", [], None, [], [], [])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [], [], [])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        cb = CCallback(1, 1, "", "cb", [], None, [], [], [])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [], [], [])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        ts_enc = TSEncoder(trace, [])
        _test_eq(ts_enc, 6, set(["cb()","cb1()","ci()"]),
                 set(["cb()","cb1()"]), set(["ci()"]))


    def test_encode_vars(self):
        trace = CTrace()

        cb = CCallback(1, 1, "", "cb", [], None, [], [], [])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [], [], [])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        cb = CCallback(1, 1, "", "cb", [], None, [], [], [])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [], [], [])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        ts_enc = TSEncoder(trace, [])

        ts_var = ts_enc._encode_vars()

        self.assertTrue(len(ts_var.state_vars) == 3)
        self.assertTrue(len(ts_var.state_vars) == len(ts_var.input_vars))

        cb_var = TSEncoder._get_state_var(TSEncoder.get_msg_key(cb))
        cb1_var = TSEncoder._get_state_var(TSEncoder.get_msg_key(cb1))
        ci_var = TSEncoder._get_state_var(TSEncoder.get_msg_key(ci))
        cb_ivar = TSEncoder._get_input_var(TSEncoder.get_msg_key(cb))
        cb1_ivar = TSEncoder._get_input_var(TSEncoder.get_msg_key(cb1))
        ci_ivar = TSEncoder._get_input_var(TSEncoder.get_msg_key(ci))

        trans = And([Implies(cb_ivar, cb_var),
                     Implies(cb1_ivar, cb1_var),
                     Implies(ci_ivar, ci_var)])

        self.assertTrue(is_valid(Iff(ts_var.init, TRUE())))
        self.assertTrue(is_valid(Iff(ts_var.trans, trans)))
