import os
import logging


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pysmt.shortcuts import Not, And, is_sat, reset_env
from pysmt.logics import QF_BOOL

from counting.spec import Spec, SpecType

from cbverifier.ctrace import CTraceSerializer, ConcreteTrace, CEvent, CCallback, CCallin
from cbverifier.verifier import Verifier


class TestInst(unittest.TestCase):

    @staticmethod
    def create_ctrace(l):
        ctrace = ConcreteTrace()

        for (evt, args, cbs) in l:
            cevent = CEvent(evt)
            for a in args: cevent.args.append(a)

            for (cb_name, cargs, cis) in cbs:
                cb = CCallback(cb_name)
                cevent.cb.append(cb)
                for a in cargs: cb.args.append(a)

                for (ci_name, ci_args) in cis:
                    assert None != ci_name
                    ci = CCallin(ci_name, "t")
                    cb.ci.append(ci)
                    for a in ci_args: ci.args.append(a)

            ctrace.events.append(cevent)
        return ctrace

    @staticmethod
    def new_spec(l):
        (spec_type, src, src_args, cb, cb_args, dst, dst_args) = l

        spec = Spec(spec_type, src, dst)
        if None != cb: spec.cb = cb

        if None != src_args:
            for f in src_args: spec.src_args.append(f)
        if None != cb_args:
            for f in cb_args: spec.cb_args.append(f)
        if None != dst_args:
            for f in dst_args: spec.dst_args.append(f)

        return spec


    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.env = reset_env()
        self.mgr = self.env.formula_manager

    def testVar(self):
        fname = "./test/data/test_vars.json"

        # Parse the trace file
        with open(fname, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)


        # test_evt_no_param
        v = Verifier(ctrace, [])
        assert v is not None
        assert v.ts_vars is not None

        self.assertTrue(len(v.ts_vars) == 4)

    def testInit(self):
        fname = "./test/data/trace_var_inst.json"

        # Parse the trace file
        with open(fname, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)

        # test_evt_no_param
        v = Verifier(ctrace, [])
        assert v is not None
        assert v.ts_vars is not None
        assert v.ts_init is not None

        for var in v.ts_vars:
            assert var.is_symbol()

            if var != (v.ts_error):
                self.assertTrue(is_sat(v.ts_init, logic=QF_BOOL, solver_name="z3"))
                to_check = And(Not(var), v.ts_init)
                self.assertFalse(is_sat(to_check, logic=QF_BOOL, solver_name="z3"))

    def testMatchEvt_01(self):
        spec = TestInst.new_spec((SpecType.Disable, "A", None,
                                  None, None,
                                  "B", None))

        app = [("A", [], [("cb", [], [("ci", [])])]),
               ("B", [], [("cb", [], [("ci", [])])]),
               ("B", [], [("cb", [], [("ci", [])])])]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, [spec])

        m1 = v._find_matching_rules_evt(ctrace.events[0])
        self.assertTrue(1 == len(m1))

        self.assertTrue(2 == len(v._find_events(m1[0][0], m1[0][1])))
        self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[1])))

    def testMatchEvt_02(self):
        specs = [TestInst.new_spec((SpecType.Enable, "A", ["x","y"],
                                    None, None, "B", None)),
                 TestInst.new_spec((SpecType.Enable, "A", ["x","y"],
                                    None, None, "ci", ["y","x"]))]

        app = [("A", ["p@1", "p@2"], [("cb", [], [])]),
               ("B", [], [("cb", [], [("ci", ["p@1","p@2"])])]),
               ("A", [], [("cb", [], [("ci", [])])])]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, specs)

        m0 = v._find_matching_rules_evt(ctrace.events[0])
        self.assertTrue(2 == len(m0))
        m1 = v._find_matching_rules_evt(ctrace.events[1])
        self.assertTrue(0 == len(m1))
        m2 = v._find_matching_rules_evt(ctrace.events[2])
        self.assertTrue(0 == len(m2))

        act0 = v._find_events(m0[0][0], m0[0][1])
        self.assertTrue(1 == len(act0))
        act1 = v._find_callins(m0[1][0], m0[1][1])
        self.assertTrue(1 == len(act1))






