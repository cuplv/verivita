import os
import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pysmt.shortcuts import Not, And, is_sat, reset_env
from pysmt.logics import QF_BOOL

from cbverifier.spec import Spec, SpecType, Binding

from cbverifier.ctrace import CTraceSerializer, ConcreteTrace, CEvent, CCallback, CCallin
from cbverifier.verifier import Verifier


class TestInst(unittest.TestCase):

    @staticmethod
    def create_ctrace(l):
        ctrace = ConcreteTrace()
        ctrace.events.append(CEvent("initial"))
        for (evt, args, cbs) in l:
            cevent = CEvent(evt)
            for a in args: cevent.args.append(a)

            for (cb_name, cargs, cis) in cbs:
                cb = CCallback(cb_name, cargs)
                cevent.cb.append(cb)

                for (ci_name, ci_args) in cis:
                    assert None != ci_name
                    ci = CCallin(ci_name)
                    cb.ci.append(ci)
                    for a in ci_args: ci.args.append(a)

            ctrace.events.append(cevent)
        return ctrace

    @staticmethod
    def new_spec(l):
        (spec_type, src, src_args, dst, dst_args) = l

        assert (None != spec_type and None != src and
                None != dst)

        spec = Spec(spec_type, src, dst)
        if None != src_args:
            for f in src_args: spec.src_args.append(f)
        if None != dst_args:
            for f in dst_args: spec.dst_args.append(f)

        return spec

    @staticmethod
    def new_bind(l):
        (spec_type, src, src_args, cb, cb_args) = l

        assert (None != spec_type and None != src and
                None != cb)

        bind = Binding(src, cb)

        if None != src_args:
            for f in src_args: bind.src_args.append(f)
        if None != cb_args:
            for f in cb_args: bind.cb_args.append(f)

        return bind

    def _bmc_opt_tester(self, ctrace, specs, bindings, bound, is_safe):

        debug_opt = [False, True]
        debug_opt = [False, True]
        coi_opt = [False, True]

        for coi in coi_opt:
            for opt in debug_opt:
                v = Verifier(ctrace, specs, bindings, opt, coi)
                cex = v.find_bug(bound)


                print coi
                print opt

                if (is_safe):
                    if cex != None:
                        v.print_cex(cex, True)
                    self.assertTrue(None == cex)
                else:
                    if cex != None:
                        v.print_cex(cex, True)

                    self.assertTrue(None != cex)

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.env = reset_env()
        self.mgr = self.env.formula_manager



    def test_evt_inst(self):
        def _test_enum(values, out):
            res = Verifier._enum_evt_inst(values)
            self.assertTrue(res == out)

        _test_enum([], [])
        _test_enum([[1]], [[1]])
        _test_enum([[1], [2]], [[1],[2]])

        _test_enum([[1,None], [None, 2]], [[1,2]])
        _test_enum([[1,2], [None, 2]], [[1,2]])
        _test_enum([[1,None], [None, 2], [None, 3]],
                   [[1,2],[1,3]])
        _test_enum([[1,None,None], [None, 2, None], [None, None, 3]],
                   [[1,2,3]])
        _test_enum([[1,None,None], [None, 2, None],
                    [None, 4, None], [None, None, 3]],
                   [[1,2,3], [1,4,3]])

    def test_evt_signatures(self):
        def _test_evt(bindings, cb, expected):
            evt_map = {}
            evt_map = Verifier._evt_signature_from_cb(bindings, cb, evt_map)

            self.assertTrue(len(evt_map.keys()) == len(expected.keys()))
            for k,b1 in evt_map.iteritems():
                self.assertTrue(k in expected)
                b2 = expected[k]

                fz1 = frozenset([frozenset(l) for l in b1])
                fz2 = frozenset([frozenset(l) for l in b2])
                self.assertTrue( fz1 == fz2 )

        _test_evt([Binding("evt", "cb", ["x"], ["y"])],
                  CCallback("cb", ["1"]),
                  {"evt" : [[None]]})

        _test_evt([Binding("evt", "cb", ["x"], ["x"])],
                  CCallback("cb", ["1"]),
                  {"evt" : [["1"]]})

        _test_evt([Binding("evt", "cb", ["x","y"], ["x"])],
                  CCallback("cb", ["1"]),
                  {"evt" : [["1", None]]})

        _test_evt([Binding("evt", "cb", ["x"], ["x","y"])],
                  CCallback("cb", ["1","2"]),
                  {"evt" : [["1"]]})

        _test_evt([Binding("evt", "cb", ["x"], ["x","y"])],
                  CCallback("cb", ["1","2"]),
                  {"evt" : [["1"]]})

        _test_evt([Binding("evt", "cb", ["x"], ["x","y"]),
                   Binding("evt2", "cb", ["x"], ["x","y"])],
                  CCallback("cb", ["1","2"]),
                  {"evt" : [["1"]], "evt2" : [["1"]]})

        _test_evt([Binding("evt", "cb", ["x"], ["x","y"]),
                   Binding("evt2", "cb", ["x"], ["x","y"])],
                  CCallback("cb", ["1","2"]),
                  {"evt" : [["1"]], "evt2" : [["1"]]})

    def testVar(self):
        def _testVarCheck(v,
                          state_vars_num,
                          event,
                          ci_allowed,
                          bug_ci):
            v._process_event(event)
            self.assertTrue(len(v.ts_state_vars) == state_vars_num)
            msg_map = v.msgs[v.conc_to_msg[event]]
            guards = msg_map.guards
            _bug_ci = msg_map.bug_ci
            must_be_allowed = msg_map.must_be_allowed
            self.assertTrue(guards == [v.conc_to_msg[event]])
            self.assertTrue(must_be_allowed == ci_allowed)
            self.assertTrue(_bug_ci == bug_ci)


        specs = [TestInst.new_spec((SpecType.Enable,
                                    "A", ["x"],
                                    "B", ["x"]))]
        bindings = [Binding("A", "cb", ["x"], ["x"])]
        app = [("A", ["1"],
                [("cb", ["2"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ]
                )])]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, specs, bindings)

        _testVarCheck(v, 6,
                      ctrace.events[1],
                      set(["ci_ci1_3", "ci_ci2_4"]),
                      None)


        #
        specs = [TestInst.new_spec((SpecType.Enable,
                                    "A", ["x"],
                                    "B", ["x"]))]
        bindings = [Binding("A", "cb", ["x"], ["x"])]
        app = [("A", ["1"],
                [("cb", ["2"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ])
                ]),
               ("A", ["2"],
                [("cb", ["2"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ])
             ])
           ]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, specs, bindings)
        _testVarCheck(v, 6,
                      ctrace.events[1],
                      set(["ci_ci1_3", "ci_ci2_4"]),
                      None)

        #
        specs = [TestInst.new_spec((SpecType.Enable,
                                    "A", ["x"],
                                    "B", ["x"]))]
        bindings = [Binding("A", "cb", ["x"], ["x"])]
        app = [("A", ["1"],
                [("cb", ["2"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ])
                ]),
               ("A", ["2"],
                [("cb", ["3"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ])
             ])
           ]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, specs, bindings)
        self.assertTrue(len(v.ts_state_vars) == 7)

        #
        specs = [TestInst.new_spec((SpecType.Enable,
                                    "A", ["x"],
                                    "B", ["x"]))]
        bindings = [Binding("A", "cb", ["x"], ["x"])]
        app = [("A", ["1"],
                [("cb", ["2"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ])
                ]),
               ("A", ["2"],
                [("cb", ["3"],
                  [ ("ci1", ["3"]), ("ci2", ["5"]) ])
             ])
           ]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, specs, bindings)
        _testVarCheck(v, 8,
                      ctrace.events[2],
                      set(["ci_ci1_3", "ci_ci2_5"]),
                      None)

        # test disable
        specs = [TestInst.new_spec((SpecType.Disable, "A", ["x"], "B", ["x"]))]
        bindings = [Binding("A", "cb", ["x"], ["x"]),
                    Binding("B", "cb", ["x"], ["x"])]
        app = [("A", ["1"],
                [("cb", ["2"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ])
                ]),
               ("B", ["2"],
                [("cb", ["3"],
                  [ ("ci1", ["3"]), ("ci2", ["5"]) ])
             ])
           ]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, specs, bindings)
        _testVarCheck(v, 8,
                      ctrace.events[1],
                      set(["ci_ci1_3", "ci_ci2_4"]),
                      None)
        msg_enabled = v.msgs[v.conc_to_msg[ctrace.events[1]]].msg_enabled
        self.assertTrue(msg_enabled["cb_#_2"] == -1)

        # test disallow
        specs = [TestInst.new_spec((SpecType.Disallow, "A", ["x"], "ci3", ["x"]))]
        bindings = [Binding("A", "cb", ["x"], ["x"]),
                    Binding("B", "cb", ["x"], ["x"])]
        app = [("A", ["1"],
                [("cb", ["2"],
                  [ ("ci1", ["3"]), ("ci2", ["4"]) ])
                ]),
               ("B", ["2"],
                [("cb", ["3"],
                  [ ("ci1", ["3"]), ("ci2", ["5"]), ("ci3", ["2"]) ])
             ])
           ]
        ctrace = TestInst.create_ctrace(app)
        v = Verifier(ctrace, specs, bindings)
        _testVarCheck(v, 9,
                      ctrace.events[1],
                      set(["ci_ci1_3", "ci_ci2_4"]),
                      None)
        msg_enabled = v.msgs[v.conc_to_msg[ctrace.events[1]]].msg_enabled
        self.assertTrue(msg_enabled["ci_ci3_2"] == -1)


    def testBmc_01(self):
        # A disallow c2
        ctrace = TestInst.create_ctrace(
            [
                ("A", [], [("cb1",[],[("c1",[])])]),
                #
                ("B", [], [("cb2",[],[("c2",[])])])
            ])
        bindings = [Binding("A", "cb1", [], []),
                    Binding("B", "cb2", [], [])]
        specs = [TestInst.new_spec((SpecType.Disallow,
                                    "A", None,
                                    "c2", None))]
        self._bmc_opt_tester(ctrace, specs, bindings, 3, False)

        ctrace = TestInst.create_ctrace(
            [
                ("A", [], [("cb1",["1"],[("c1",["1"])])]),
                #
                ("B", [], [("cb2",["1"],[("c2",["1"])])])
            ])
        bindings = [Binding("A", "cb1", ["x"], ["x"]),
                    Binding("B", "cb2", ["x"], ["x"])]
        specs = [TestInst.new_spec((SpecType.Disallow,
                                    "A", "x",
                                    "c2", "x"))]
        self._bmc_opt_tester(ctrace, specs, bindings, 3, False)


        #
        ctrace = TestInst.create_ctrace(
            [
                ("A", [], [("cb1",[],[("c1",[])])]),
                #
                ("B", [], [("cb2",[],[("c3",[]),("c2",[])])])
            ])
        bindings = [Binding("A", "cb1", [], []),
                    Binding("B", "cb2", [], [])]
        specs = [TestInst.new_spec((SpecType.Disallow,
                                    "A", None,
                                    "c2", None)),
                 TestInst.new_spec((SpecType.Allow,
                                    "c3", None,
                                    "c2", None))]
        self._bmc_opt_tester(ctrace, specs, bindings, 3, True)

        #
        ctrace = TestInst.create_ctrace(
            [
                ("A", [], [("cb1",["1"],[("c1",["1"])])]),
                #
                ("B", [], [("cb2",["2"],[("c2",["2"])])])
            ])
        bindings = [Binding("A", "cb1", ["x"], ["x"]),
                    Binding("B", "cb2", ["x"], ["x"])]
        specs = [TestInst.new_spec((SpecType.Disallow,
                                    "A", ["a"],
                                    "c2", ["a"]))]
        self._bmc_opt_tester(ctrace, specs, bindings, 3, True)

if __name__ == '__main__':
    unittest.main()
