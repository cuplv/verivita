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

        assert (None != spec_type and None != src and
                None != dst)
        
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

    def testMatchEvt_03(self):
        specs = [TestInst.new_spec((SpecType.Enable, "A", ["x","y"],
                                    "cb", ["y","z"], "B", None))]

        app = [("A", ["p@1", "p@2"], [("cb", ["p@2", "p@3"], [])]),  # match
               ("A", ["p@1", "p@2"], [("cb1", ["p@2", "p@3"], [])]), # no match
               ("B", ["p@1", "p@2"], [("cb", ["p@2", "p@3"], [])]),  # no match
               ("A", ["p@1", "p@2"], [("cb", ["p@3", "p@2"], [])]),  # no match
               ("A", ["p@1", "p@2"], [("cb", ["p@3"], [])])]         # no match
        ctrace = TestInst.create_ctrace(app)
        
        v = Verifier(ctrace, specs)
        
        self.assertTrue(1 == len(v._find_matching_rules_evt(ctrace.events[0])))
        self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[1])))
        self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[2])))
        self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[3])))
        self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[4])))

    def ca(self, v, formula, en, dis):
        def get_atom(v,e):
            if isinstance(e, CEvent):
                atom = v.msgs_to_var[e]
            elif isinstance(e, CCallin):
                key = v._get_ci_key(e)
                atom = v.msgs_to_var[key]
            return atom
            
        new_f = And(formula)
        for e in en: new_f = And(new_f, get_atom(v,e))
        for e in dis: new_f = And(new_f, Not(get_atom(v,e)))

        return is_sat(new_f)
        
    def testEvtEffect_01(self):
        # A is enabled if it is executed
        # A is enabled at the end
        ctrace = TestInst.create_ctrace([("A", [], [])])
        specs = [TestInst.new_spec((SpecType.Enable, "A", None,
                                    None, None, "B", None))]
        v = Verifier(ctrace, specs)
        (msg_enabled, guards, bug_ci) = v._process_event(ctrace.events[0])
        self.assertTrue(1 == msg_enabled[ctrace.events[0]] and
                        self.ca(v, guards, [ctrace.events[0]], []) and
                        None == bug_ci)

    def testEvtEffect_02(self):
        # A disables A
        # A is disabled at the end
        ctrace = TestInst.create_ctrace([("A", [], [])])
        specs = [TestInst.new_spec((SpecType.Disable,
                                    "A", None,
                                    None, None,
                                    "A", None))]
        v = Verifier(ctrace, specs)
        (msg_enabled, guards, bug_ci) = v._process_event(ctrace.events[0])
        self.assertTrue(-1 == msg_enabled[ctrace.events[0]] and
                        self.ca(v, guards, [ctrace.events[0]], []) and
                        None == bug_ci)
        
    def testEvtEffect_03(self):
        # B is unknown
        # B is unknown at the end
        ctrace = TestInst.create_ctrace([("A", [], []),("B", [], [])])
        specs = [TestInst.new_spec((SpecType.Enable, "A", None,
                                    None, None, "C", None))]
        v = Verifier(ctrace, specs)
        (msg_enabled, guards, bug_ci) = v._process_event(ctrace.events[0])
        self.assertTrue(0 == msg_enabled[ctrace.events[1]] and
                        self.ca(v, guards, [ctrace.events[0]], []) and
                        None == bug_ci)

    def testEvtEffect_04(self):
        # A allow ci
        # ci is allowed at the end
        ctrace = TestInst.create_ctrace([("A", [], [("cb",[],[("ci2",[])])]),
                                         ("B", [], [("cb",[],[("ci",[])])])])
        specs = [TestInst.new_spec((SpecType.Allow, "A", None,
                                    None, None, "ci", None))]
        v = Verifier(ctrace, specs)
        (msg_enabled, guards, bug_ci) = v._process_event(ctrace.events[0])
        callin = ctrace.events[1].cb[0].ci[0]
        self.assertTrue(1 == msg_enabled[v._get_ci_key(callin)] and
                        self.ca(v, guards, [ctrace.events[0],
                                            ctrace.events[0].cb[0].ci[0]], []) and
                        None == bug_ci)

    def testEvtEffect_05(self):
        # A disallow ci
        # ci is is called afterwards, creating an error
        ctrace = TestInst.create_ctrace([("A", [], []),
                                         ("B", [], [("cb",[],[("ci",[])])])])
        specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
                                    None, None, "ci", None))]
        v = Verifier(ctrace, specs)
        (msg_enabled, guards, bug_ci) = v._process_event(ctrace.events[0])
        callin = ctrace.events[1].cb[0].ci[0]
        print bug_ci
        self.assertTrue(-1 == msg_enabled[v._get_ci_key(callin)] and
                        None != bug_ci)


    def testEvtEffect_06(self):
        # A disallow c2, c1 allow c2                
        ctrace = TestInst.create_ctrace([("A", [], [("cb",[],[("c1",[]),("c2",[])])])])
        specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
                                    None, None, "c2", None)),
                 TestInst.new_spec((SpecType.Allow, "c1", None,
                                    None, None, "c2", None))]
        v = Verifier(ctrace, specs)
        (msg_enabled, guards, bug_ci) = v._process_event(ctrace.events[0])
        callin = ctrace.events[0].cb[0].ci[1]
        self.assertTrue(1 == msg_enabled[v._get_ci_key(callin)] and
                        None == bug_ci)

    def testBmc_01(self):
        # A disallow c2, c1 allow c2
        ctrace = TestInst.create_ctrace(
            [
                ("A", [], [("cb",[],[("c1",[]),("c2",[])]),
                           ("cb",[],[("c1",[]),("c2",[])])]),
                #
                ("B", [], [("cb",[],[("c1",[]),("c2",[])]),
                           ("cb",[],[("c1",[]),("c2",[])])])                
            ])
        specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
                                    None, None, "c2", None)),
                 TestInst.new_spec((SpecType.Allow, "c1", None,
                                    None, None, "c2", None))]
        v = Verifier(ctrace, specs)

        cex = v.find_bug(4)
        self.assertTrue(None == cex)

    def testBmc_02(self):
        # A disallow c2
        ctrace = TestInst.create_ctrace(
            [
                ("A", [], [("cb",[],[("c2",[])])])
            ])
        specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
                                    None, None, "c2", None))]
        v = Verifier(ctrace, specs)

        cex = v.find_bug(1)
        self.assertTrue(None != cex)

    def testBmc_03(self):
        # A disallow c2, c1 allow c2 
        # B disallow c3, c1 disallow c3
        ctrace = TestInst.create_ctrace(
            [
                ("A", [], [("cb",[],[("c1",[]),("c2",[])])]),
                ("B", [], [("cb",[],[("c1",[]),("c3",[])])])
            ])
        specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
                                    None, None, "c2", None)),
                 TestInst.new_spec((SpecType.Disallow, "B", None,
                                None, None, "c3", None))]
        v = Verifier(ctrace, specs)
        cex = v.find_bug(1)
        self.assertTrue(None != cex)
