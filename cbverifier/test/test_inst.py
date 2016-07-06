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

        for opt in debug_opt:
            v = Verifier(ctrace, specs, bindings, opt)
            cex = v.find_bug(bound)

            if (is_safe):
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

        _testVarCheck(v, 4,
                      ctrace.events[0],
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
        _testVarCheck(v, 4,
                      ctrace.events[0],
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
        self.assertTrue(len(v.ts_state_vars) == 5)

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
        _testVarCheck(v, 6,
                      ctrace.events[1],
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
        _testVarCheck(v, 6,
                      ctrace.events[0],
                      set(["ci_ci1_3", "ci_ci2_4"]),
                      None)
        msg_enabled = v.msgs[v.conc_to_msg[ctrace.events[0]]].msg_enabled
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
        _testVarCheck(v, 7,
                      ctrace.events[0],
                      set(["ci_ci1_3", "ci_ci2_4"]),
                      None)
        msg_enabled = v.msgs[v.conc_to_msg[ctrace.events[0]]].msg_enabled
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
        self._bmc_opt_tester(ctrace, specs, bindings, 2, False)

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
        self._bmc_opt_tester(ctrace, specs, bindings, 2, False)


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
        self._bmc_opt_tester(ctrace, specs, bindings, 2, True)

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
        self._bmc_opt_tester(ctrace, specs, bindings, 2, True)

        # ctrace = TestInst.create_ctrace(
        #     [
        #         ("A", [], [("cb1",["1"],[("c1",["1"])])]),
        #         #
        #         ("B", [], [("cb2",["2"],[("c2",["1"])])])
        #     ])
        # bindings = [Binding("A", "cb1", ["x"], ["x"]),
        #             Binding("B", "cb2", ["x"], ["x"])]
        # specs = [TestInst.new_spec((SpecType.Disallow,
        #                             "A", ["a"],
        #                             "c2", ["a"]))]
        # self._bmc_opt_tester(ctrace, specs, bindings, 1, True)

    # def testVar(self):
    #     fname = "./test/data/test_vars.json"

    #     # Parse the trace file
    #     with open(fname, "r") as infile:
    #         ctrace = CTraceSerializer.read_trace(infile)


    #     # test_evt_no_param
    #     v = Verifier(ctrace, [])
    #     assert v is not None
    #     assert v.ts_state_vars is not None

    #     self.assertTrue(len(v.ts_state_vars) == 5)

    # def testInit(self):
    #     fname = "./test/data/trace_var_inst.json"

    #     # Parse the trace file
    #     with open(fname, "r") as infile:
    #         ctrace = CTraceSerializer.read_trace(infile)

    #     # test_evt_no_param
    #     v = Verifier(ctrace, [])
    #     assert v is not None
    #     assert v.ts_state_vars is not None
    #     assert v.ts_init is not None

    #     for var in v.ts_state_vars:
    #         assert var.is_symbol()

    #         if var != (v.ts_error):
    #             self.assertTrue(is_sat(v.ts_init, logic=QF_BOOL, solver_name="z3"))
    #             to_check = And(Not(var), v.ts_init)
    #             self.assertFalse(is_sat(to_check, logic=QF_BOOL, solver_name="z3"))

    # @unittest.skip("To be update to the new semantic")
    # def testMatchEvt_01(self):
    #     spec = TestInst.new_spec((SpecType.Disable, "A", None,
    #                               None, None,
    #                               "B", None))

    #     app = [("A", [], [("cb", [], [("ci", [])])]),
    #            ("B", [], [("cb", [], [("ci", [])])]),
    #            ("B", [], [("cb", [], [("ci", [])])])]
    #     ctrace = TestInst.create_ctrace(app)
    #     v = Verifier(ctrace, [spec])

    #     m1 = v._find_matching_rules_evt(ctrace.events[0])
    #     self.assertTrue(1 == len(m1))

    #     self.assertTrue(2 == len(v._find_events(m1[0][0], m1[0][1])))
    #     self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[1])))

    # @unittest.skip("To be update to the new semantic")
    # def testMatchEvt_02(self):
    #     specs = [TestInst.new_spec((SpecType.Enable, "A", ["x","y"],
    #                                 None, None, "B", None)),
    #              TestInst.new_spec((SpecType.Enable, "A", ["x","y"],
    #                                 None, None, "ci", ["y","x"]))]

    #     app = [("A", ["p@1", "p@2"], [("cb", [], [])]),
    #            ("B", [], [("cb", [], [("ci", ["p@1","p@2"])])]),
    #            ("A", [], [("cb", [], [("ci", [])])])]
    #     ctrace = TestInst.create_ctrace(app)
    #     v = Verifier(ctrace, specs)

    #     m0 = v._find_matching_rules_evt(ctrace.events[0])
    #     self.assertTrue(2 == len(m0))
    #     m1 = v._find_matching_rules_evt(ctrace.events[1])
    #     self.assertTrue(0 == len(m1))
    #     m2 = v._find_matching_rules_evt(ctrace.events[2])
    #     self.assertTrue(0 == len(m2))

    #     act0 = v._find_events(m0[0][0], m0[0][1])
    #     self.assertTrue(1 == len(act0))
    #     act1 = v._find_callins(m0[1][0], m0[1][1])
    #     self.assertTrue(1 == len(act1))

    # def testMatchEvt_03(self):
    #     specs = [TestInst.new_spec((SpecType.Enable, "A", ["x","y"],
    #                                 "cb", ["y","z"], "B", None))]

    #     app = [("A", ["p@1", "p@2"], [("cb", ["p@2", "p@3"], [])]),  # match
    #            ("A", ["p@1", "p@2"], [("cb1", ["p@2", "p@3"], [])]), # no match
    #            ("B", ["p@1", "p@2"], [("cb", ["p@2", "p@3"], [])]),  # no match
    #            ("A", ["p@1", "p@2"], [("cb", ["p@3", "p@2"], [])]),  # no match
    #            ("A", ["p@1", "p@2"], [("cb", ["p@3"], [])])]         # no match
    #     ctrace = TestInst.create_ctrace(app)

    #     v = Verifier(ctrace, specs)

    #     self.assertTrue(1 == len(v._find_matching_rules_evt(ctrace.events[0])))
    #     self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[1])))
    #     self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[2])))
    #     self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[3])))
    #     self.assertTrue(0 == len(v._find_matching_rules_evt(ctrace.events[4])))

    # def ca(self, v, formula, en, dis):
    #     def get_atom(v,e):
    #         if isinstance(e, CEvent):
    #             atom = v.msgs_to_var[e]
    #         elif isinstance(e, CCallin):
    #             key = v._get_ci_key(e)
    #             atom = v.msgs_to_var[key]
    #         return atom

    #     new_f = And(formula)
    #     for e in en: new_f = And(new_f, get_atom(v,e))
    #     for e in dis: new_f = And(new_f, Not(get_atom(v,e)))

    #     return is_sat(new_f)

    # @unittest.skip("To be update to the new semantic")
    # def testEvtEffect_01(self):
    #     # A is enabled if it is executed
    #     # A is enabled at the end
    #     ctrace = TestInst.create_ctrace([("A", [], [])])
    #     specs = [TestInst.new_spec((SpecType.Enable, "A", None,
    #                                 None, None, "B", None))]
    #     v = Verifier(ctrace, specs)
    #     (msg_enabled, guards, bug_ci, _) = v._process_event(ctrace.events[0])
    #     self.assertTrue(1 == msg_enabled[ctrace.events[0]] and
    #                     self.ca(v, guards, [ctrace.events[0]], []) and
    #                     None == bug_ci)

    # @unittest.skip("To be update to the new semantic")
    # def testEvtEffect_02(self):
    #     # A disables A
    #     # A is disabled at the end
    #     ctrace = TestInst.create_ctrace([("A", [], [])])
    #     specs = [TestInst.new_spec((SpecType.Disable,
    #                                 "A", None,
    #                                 None, None,
    #                                 "A", None))]
    #     v = Verifier(ctrace, specs)
    #     (msg_enabled, guards, bug_ci, _) = v._process_event(ctrace.events[0])
    #     self.assertTrue(-1 == msg_enabled[ctrace.events[0]] and
    #                     self.ca(v, guards, [ctrace.events[0]], []) and
    #                     None == bug_ci)

    # @unittest.skip("To be update to the new semantic")
    # def testEvtEffect_03(self):
    #     # B is unknown
    #     # B is unknown at the end
    #     ctrace = TestInst.create_ctrace([("A", [], []),("B", [], [])])
    #     specs = [TestInst.new_spec((SpecType.Enable, "A", None,
    #                                 None, None, "C", None))]
    #     v = Verifier(ctrace, specs)
    #     (msg_enabled, guards, bug_ci, _) = v._process_event(ctrace.events[0])
    #     self.assertTrue(0 == msg_enabled[ctrace.events[1]] and
    #                     self.ca(v, guards, [ctrace.events[0]], []) and
    #                     None == bug_ci)

    # @unittest.skip("To be update to the new semantic")
    # def testEvtEffect_04(self):
    #     # A allow ci
    #     # ci is allowed at the end
    #     ctrace = TestInst.create_ctrace([("A", [], [("cb",[],[("ci2",[])])]),
    #                                      ("B", [], [("cb",[],[("ci",[])])])])
    #     specs = [TestInst.new_spec((SpecType.Allow, "A", None,
    #                                 None, None, "ci", None))]
    #     v = Verifier(ctrace, specs)
    #     (msg_enabled, guards, bug_ci, _) = v._process_event(ctrace.events[0])
    #     callin = ctrace.events[1].cb[0].ci[0]
    #     self.assertTrue(1 == msg_enabled[v._get_ci_key(callin)] and
    #                     self.ca(v, guards, [ctrace.events[0],
    #                                         ctrace.events[0].cb[0].ci[0]], []) and
    #                     None == bug_ci)

    # @unittest.skip("To be update to the new semantic")
    # def testEvtEffect_05(self):
    #     # A disallow ci
    #     # ci is is called afterwards, creating an error
    #     ctrace = TestInst.create_ctrace([("A", [], []),
    #                                      ("B", [], [("cb",[],[("ci",[])])])])
    #     specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
    #                                 None, None, "ci", None))]
    #     v = Verifier(ctrace, specs)
    #     (msg_enabled, guards, bug_ci, must_be_allowed) = v._process_event(ctrace.events[0])
    #     callin = ctrace.events[1].cb[0].ci[0]
    #     self.assertTrue(-1 == msg_enabled[v._get_ci_key(callin)] and
    #                     None == bug_ci)

    # @unittest.skip("To be update to the new semantic")
    # def testEvtEffect_06(self):
    #     # A disallow c2, c1 allow c2
    #     ctrace = TestInst.create_ctrace([("A", [], [("cb",[],[("c1",[]),("c2",[])])])])
    #     specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
    #                                 None, None, "c2", None)),
    #              TestInst.new_spec((SpecType.Allow, "c1", None,
    #                                 None, None, "c2", None))]
    #     v = Verifier(ctrace, specs)
    #     (msg_enabled, guards, bug_ci, _) = v._process_event(ctrace.events[0])
    #     callin = ctrace.events[0].cb[0].ci[1]
    #     self.assertTrue(1 == msg_enabled[v._get_ci_key(callin)] and
    #                     None == bug_ci)



    # @unittest.skip("To be update to the new semantic")
    # def testBmc_01(self):
    #     # A disallow c2, c1 allow c2
    #     ctrace = TestInst.create_ctrace(
    #         [
    #             ("A", [], [("cb",[],[("c1",[]),("c2",[])]),
    #                        ("cb",[],[("c1",[]),("c2",[])])]),
    #             #
    #             ("B", [], [("cb",[],[("c1",[]),("c2",[])]),
    #                        ("cb",[],[("c1",[]),("c2",[])])])
    #         ])
    #     specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
    #                                 None, None, "c2", None)),
    #              TestInst.new_spec((SpecType.Allow, "c1", None,
    #                                 None, None, "c2", None))]
    #     self._bmc_opt_tester(ctrace, specs, 1, True)

    # @unittest.skip("To be update to the new semantic")
    # def testBmc_02(self):
    #     # A disallow c2
    #     ctrace = TestInst.create_ctrace(
    #         [
    #             ("A", [], [("cb",[],[("c2",[])])])
    #         ])
    #     specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
    #                                 None, None, "c2", None))]
    #     self._bmc_opt_tester(ctrace, specs, 1, False)


    # @unittest.skip("To be update to the new semantic")
    # def testBmc_03(self):
    #     # A disallow c2, c1 allow c2
    #     # B disallow c3, c1 disallow c3
    #     ctrace = TestInst.create_ctrace(
    #         [
    #             ("A", [], [("cb",[],[("c1",[]),("c2",[])])]),
    #             ("B", [], [("cb",[],[("c1",[]),("c3",[])])])
    #         ])
    #     specs = [TestInst.new_spec((SpecType.Disallow, "A", None,
    #                                 None, None, "c2", None)),
    #              TestInst.new_spec((SpecType.Disallow, "B", None,
    #                             None, None, "c3", None))]
    #     self._bmc_opt_tester(ctrace, specs, 1, False)

    # @unittest.skip("To be update to the new semantic")
    # def testBmc_04(self):
    #     # c1 disallow c2
    #     # B execute c2
    #     ctrace = TestInst.create_ctrace(
    #         [
    #             ("B", [], [("cb", [], [("c2",[])])]),
    #             ("A", [], [("cb", [], [("c1",[])])])
    #         ])
    #     specs = [TestInst.new_spec((SpecType.Disallow, "c1", None,
    #                                 None, None, "c2", None))]
    #     self._bmc_opt_tester(ctrace, specs, 2, False)


if __name__ == '__main__':
    unittest.main()
