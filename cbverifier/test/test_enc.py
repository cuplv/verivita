""" Test the encoding """

import sys
import logging
import unittest


from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.encoder import TSEncoder, TSMapback
from cbverifier.encoding.cex_printer import CexPrinter
from cbverifier.encoding.counter_enc import CounterEnc
from cbverifier.encoding.grounding import GroundSpecs
from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue, CTraceException
from cbverifier.specs.spec_ast import *
from cbverifier.specs.spec import Spec
from cbverifier.bmc.bmc import BMC

from pysmt.typing import BOOL
from pysmt.logics import QF_BOOL
from pysmt.shortcuts import Solver
from pysmt.shortcuts import get_env, is_sat, is_valid, get_model
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from cbverifier.test.test_grounding import TestGrounding


class TestEnc(unittest.TestCase):

    def _accept_word(self, ts_enc, ts, word, final_states):
        """ Check if a particular word with a given final state
        is accepted by ts
        """

        # error is encoded in the final state
        bmc = BMC(ts_enc.helper, ts, TRUE())

        solver = Solver(name='z3', logic=QF_BOOL)
        all_vars = set(ts.state_vars)
        all_vars.update(ts.input_vars)

        bmc.encode_up_to_k(solver, all_vars, len(word))

        error = bmc.helper.get_formula_at_i(all_vars, final_states, len(word))
        solver.add_assertion(error)

        # encode the word
        for i in range(len(word)):
            w_formula = ts_enc.r2a.get_msg_eq(word[i])
            w_at_i = bmc.helper.get_formula_at_i(ts.input_vars,
                                                 w_formula, i)
            solver.add_assertion(w_at_i)

        res = solver.solve()
        # if res:
        #     model = solver.get_model()
        #     print model
        return res


    def test_get_key(self):
        """ Test the retrieval for the key of the message """

        self.assertTrue("[CB]_method(int,int,int)(1,2,3)" ==
                        TSEncoder.get_key(None, "CB", "method(int,int,int)", ["1","2","3"]))

        self.assertTrue("[CI]_method()()" ==
                        TSEncoder.get_key(None, "CI", "method()", []))
        self.assertTrue("1=[CB]_method(int,int)(1,2)" ==
                        TSEncoder.get_key("1", "CB", "method(int,int)", ["1","2"]))

        with self.assertRaises(AssertionError):
            TSEncoder.get_key(False, "CI", "", [])
        with self.assertRaises(AssertionError):
            TSEncoder.get_key(False, "CI", None, [])
        with self.assertRaises(AssertionError):
            TSEncoder.get_key(False, "CA", "method", [])

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

    def test_get_key_from_msg(self):
        fmwk_over = TestGrounding._get_fmwkov("","doSomethingCb", False)

        cb = CCallback(1, 1, "", "type doSomethingCb(int)",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [fmwk_over])
        res = TSEncoder.get_key_from_msg(cb)
        self.assertTrue("[CB]_type doSomethingCb(1)", res)

        cb = CCallback(1, 1, "", "void doSomethingCb(int)",
                       [TestGrounding._get_obj("1","string")],
                       TestGrounding._get_obj("1","string"),
                       [fmwk_over])
        res = TSEncoder.get_key_from_msg(cb)
        self.assertTrue("1=[CB]_void doSomethingCb(int)(1)", res)

        cb = CCallback(1, 1, "pippo.Class", "void doSomethingCb(int, int)",
                       [TestGrounding._get_obj("1","string"),
                        TestGrounding._get_int(1)],
                       None, [fmwk_over])
        res = TSEncoder.get_key_from_msg(cb)
        self.assertTrue("[CB]_void pippo.Class.doSomethingCb(int,int)(1,1)", res)

        ci = CCallin(1, 1, "a.Class", "void doSomethingCi(string)",
                     [TestGrounding._get_obj("1","string")],
                     None)
        res = TSEncoder.get_key_from_msg(ci)
        self.assertTrue("[CI]_void a.Class.doSomethingCi(string)(1)", res)

        ci = CCallin(1, 1, "", "doSomethingCi",
                     [],
                     None)
        res = TSEncoder.get_key_from_msg(ci)
        self.assertTrue("[CI]_doSomethingCi(1)", res)



    def test_get_key_from_call(self):
        spec_list = Spec.get_specs_from_string("SPEC TRUE |- [CI] [l] void m1(); " +
                                               "SPEC TRUE |- [CI] [l] void m1(a : int,b : int,c : int);" +
                                               "SPEC TRUE |- z = [CI] [l] void m1(a : int,b : int,c : int)")
        assert spec_list is not None

        ci1 = CCallin(1, 1, "", "void m1()",
                      [TestGrounding._get_obj("1","string")],
                      None)
        ci2 = CCallin(1, 1, "", "void m1(int,int,int)",
                      [TestGrounding._get_obj("1","string"),
                       TestGrounding._get_int(2),
                       TestGrounding._get_int(1),
                       TestGrounding._get_int(2),], None)
        ci3 = CCallin(1, 1, "", "void m1(int,int,int)",
                      [TestGrounding._get_obj("1","string"),
                       TestGrounding._get_int(2),
                       TestGrounding._get_int(1),
                       TestGrounding._get_int(2),],
                      TestGrounding._get_int(3))

        base_var = [new_id('l'),new_id("a"),new_id("b"),new_id("c"),new_id("z")]
        base_val = [TestGrounding._get_obj("1","string"),
                    TestGrounding._get_int(2),
                    TestGrounding._get_int(1),
                    TestGrounding._get_int(2),
                    TestGrounding._get_int(3)]

        bindings = [
            TestGrounding.newAssign(base_var + [get_spec_rhs(spec_list[0].ast)],
                                    base_val + [ci1]),
            TestGrounding.newAssign(base_var + [get_spec_rhs(spec_list[1].ast)],
                                    base_val + [ci2]),
            TestGrounding.newAssign(base_var + [get_spec_rhs(spec_list[2].ast)],
                                    base_val + [ci3])
            ]

        calls_nodes = []
        for (s,binding) in zip(spec_list, bindings):
            ground_s = GroundSpecs._substitute(s, binding)
            msg = get_spec_rhs(ground_s)

            assert get_node_type(msg) == CALL
            calls_nodes.append(msg)
        assert (len(calls_nodes) == len(spec_list))

        res = TSEncoder.get_key_from_call(calls_nodes[0])
        res2 = TSEncoder.get_key_from_msg(ci1)
        self.assertTrue("[CI]_void m1()(1)" == res)
        self.assertTrue(res == res2)

        res = TSEncoder.get_key_from_call(calls_nodes[1])
        res2 = TSEncoder.get_key_from_msg(ci2)
        self.assertTrue("[CI]_void m1(int,int,int)(1,2,1,2)" == res)
        self.assertTrue(res == res2)


        res = TSEncoder.get_key_from_call(calls_nodes[2])
        res2 = TSEncoder.get_key_from_msg(ci3)
        self.assertTrue("3=[CI]_void m1(int,int,int)(1,2,1,2)" == res)
        self.assertTrue(res == res2)


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

        fmwk_over = TestGrounding._get_fmwkov("","doSomethingCb", False)

        trace = CTrace()
        cb = CCallback(1, 1, "", "doSomethingCb", [], None, [fmwk_over])
        trace.add_msg(cb)
        ts_enc = TSEncoder(trace, [])
        _test_eq(ts_enc, 1, set(["[CB]_doSomethingCb()"]),
                 set(["[CB]_doSomethingCb()"]), set())

        trace = CTrace()
        cb = CCallback(1, 1, "", "doSomethingCb", [], None, [fmwk_over])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",[], None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "doSomethingCb", [], None, [fmwk_over])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",[], None)
        cb.add_msg(ci)

        ts_enc = TSEncoder(trace, [])
        _test_eq(ts_enc, 4, set(["[CB]_doSomethingCb()","[CI]_doSomethingCi()"]),
                 set(["[CB]_doSomethingCb()"]), set(["[CI]_doSomethingCi()"]))

        trace = CTrace()

        fmwk_over_cb = TestGrounding._get_fmwkov("","cb", False)
        fmwk_over_cb1 = TestGrounding._get_fmwkov("","cb1", False)
        cb = CCallback(1, 1, "", "cb", [], None, [fmwk_over_cb])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [fmwk_over_cb1])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        cb = CCallback(1, 1, "", "cb", [], None, [fmwk_over_cb])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [fmwk_over_cb1])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        ts_enc = TSEncoder(trace, [])
        _test_eq(ts_enc, 6, set(["[CB]_cb()","[CB]_cb1()","[CI]_ci()"]),
                 set(["[CB]_cb()","[CB]_cb1()"]), set(["[CI]_ci()"]))


    def test_encode_vars(self):
        fmwk_over = TestGrounding._get_fmwkov("","cb", False)
        trace = CTrace()

        fmwk_over_cb = TestGrounding._get_fmwkov("","cb", False)
        fmwk_over_cb1 = TestGrounding._get_fmwkov("","cb1", False)

        cb = CCallback(1, 1, "", "cb", [], None, [fmwk_over_cb])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [fmwk_over_cb1])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        cb = CCallback(1, 1, "", "cb", [], None, [fmwk_over_cb])
        cb1 = CCallback(1, 1, "", "cb1", [], None, [fmwk_over_cb1])
        ci = CCallin(1, 1, "", "ci",[], None)
        cb.add_msg(cb1)
        cb1.add_msg(ci)
        trace.add_msg(cb)

        ts_enc = TSEncoder(trace, [])

        ts_var = ts_enc._encode_vars()

        self.assertTrue(len(ts_var.state_vars) == 3)

        cb_var = TSEncoder._get_state_var(TSEncoder.get_key_from_msg(cb))
        cb1_var = TSEncoder._get_state_var(TSEncoder.get_key_from_msg(cb1))
        ci_var = TSEncoder._get_state_var(TSEncoder.get_key_from_msg(ci))
        cb_ivar = ts_enc.r2a.get_msg_eq(TSEncoder.get_key_from_msg(cb))
        cb1_ivar = ts_enc.r2a.get_msg_eq(TSEncoder.get_key_from_msg(cb1))
        ci_ivar = ts_enc.r2a.get_msg_eq(TSEncoder.get_key_from_msg(ci))

        trans = And([Implies(cb_ivar, cb_var),
                     Implies(cb1_ivar, cb1_var),
                     Implies(ci_ivar, ci_var)])

        self.assertTrue(is_valid(Iff(ts_var.init, TRUE())))
        self.assertTrue(is_valid(Iff(ts_var.trans, trans)))


    def test_get_ground_spec_ts(self):
        def _encode_error(accepting, final):
            f_error = FALSE()
            for f in accepting:
                f_error = Or(f, f_error)
            f_error = And(f_error, final)
            return f_error

        spec_list = Spec.get_specs_from_string("SPEC [CB] [l] void m1() |- [CI] [l] void m2()")
        assert spec_list is not None

        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)

        binding = TestGrounding.newAssign([new_id('l'),
                                           get_regexp_node(spec_list[0].ast),
                                           get_spec_rhs(spec_list[0].ast)],
                                          [TestGrounding._get_obj("1","string"),
                                           cb, ci])
        ground_s = Spec(GroundSpecs._substitute(spec_list[0], binding))

        ts_enc = TSEncoder(ctrace,[])
        ts_var = ts_enc._encode_vars()

        accepting = []
        gs_ts = ts_enc._get_ground_spec_ts(ground_s, 0, accepting)
        gs_ts.product(ts_var)

        error = _encode_error(accepting, TRUE())
        self.assertTrue(self._accept_word(ts_enc, gs_ts, ["[CB]_void m1()(1)"], error))
        self.assertFalse(self._accept_word(ts_enc, gs_ts, ["[CI]_void m2()(1)"], error))

        # check the disable
        error = _encode_error(accepting, TSEncoder._get_state_var("[CI]_void m2()(1)"))
        self.assertFalse(self._accept_word(ts_enc, gs_ts, ["[CB]_void m1()(1)"], error))
        self.assertFalse(self._accept_word(ts_enc, gs_ts, ["[CI]_void m2()(1)"], error))

    def _get_sample_trace(self):
        spec_list = Spec.get_specs_from_string("SPEC [CB] [l] void m1() |- [CI] [l] void m2()")
        assert spec_list is not None

        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()", [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        ts_enc = TSEncoder(ctrace, spec_list)
        return ts_enc

    def test_encode_ground_specs(self):
        ts_enc = self._get_sample_trace()
        vars_ts = ts_enc._encode_vars()
        (ts, disabled_ci, accepting) = ts_enc._encode_ground_specs()
        ts.product(vars_ts)

        accepting_states = FALSE()
        for k,v in accepting.iteritems():
            for state in v:
                accepting_states = Or(accepting_states, state)

        assert(disabled_ci == set(["[CI]_void m2()(1)"]))

        self.assertTrue(self._accept_word(ts_enc, ts, ["[CB]_void m1()(1)"], accepting_states))
        self.assertFalse(self._accept_word(ts_enc, ts, ["[CI]_void m2()(1)"], accepting_states))
        error = And(accepting_states, TSEncoder._get_state_var("[CI]_void m2()(1)"))
        self.assertFalse(self._accept_word(ts_enc, ts, ["[CB]_void m1()(1)"], error))


    def test_encode_cbs(self):
        def cb(name):
            fmwk_over = TestGrounding._get_fmwkov("",name, False)

            cb = CCallback(1, 1, "", name, [], None, [fmwk_over])
            return cb
        def ci(name):
            ci = CCallin(1, 1, "", name,[], None)
            return ci

        def new_trace(tree_trace_list):
            def add_rec(parent, children):
                for (child, lchildren) in children:
                    parent.add_msg(child)
                    add_rec(child, lchildren)

            ctrace = CTrace()
            add_rec(ctrace, tree_trace_list)

            return ctrace


        trace_tree = [(cb("cb1"), [(ci("ci1"),[])]),
                      (cb("cb2"), [(ci("ci2"),[])])]
        ctrace = new_trace(trace_tree)
        # ctrace.print_trace(sys.stdout)
        ts_enc = TSEncoder(ctrace, [])
        vars_ts = ts_enc._encode_vars()

        (ts, errors) = ts_enc._encode_cbs(set())
        ts.product(vars_ts)
        self.assertTrue(len(errors) == 0)

        cb_1_seq = ["[CB]_cb1()", "[CI]_ci1()"]
        cb_2_seq = ["[CB]_cb2()", "[CI]_ci2()"]
        cb_11 = ["[CB]_cb1()", "[CI]_ci1()","[CB]_cb1()", "[CI]_ci1()"]
        cb_12 = ["[CB]_cb1()", "[CI]_ci1()","[CB]_cb2()", "[CI]_ci2()"]
        cb_22 = ["[CB]_cb2()", "[CI]_ci2()","[CB]_cb2()", "[CI]_ci2()"]

        accepting_traces = [cb_1_seq, cb_2_seq,
                            cb_11, cb_12, cb_22]

        for seq in accepting_traces:
            self.assertTrue(self._accept_word(ts_enc, ts, seq, TRUE()))

        deadlock_traces = [["[CI]_ci1()"], ["[CI]_ci2()"],
                           ["[CB]_cb1()", "[CI]_ci1()", "[CI]_ci2()"],
                           ["[CB]_cb2()", "[CB]_cb1()", "[CI]_ci1()"]]
        for seq in deadlock_traces:
            self.assertFalse(self._accept_word(ts_enc, ts, seq, TRUE()))

        ts_enc = TSEncoder(ctrace, [])
        vars_ts = ts_enc._encode_vars()
        (ts, errors) = ts_enc._encode_cbs(set(["[CI]_ci1()"]))
        ts.product(vars_ts)
        self.assertTrue(len(errors) == 1)
        self.assertTrue(is_sat(And(errors[0],
                                   Not(TSEncoder._get_state_var("[CI]_ci1()")))))


        ts_enc = TSEncoder(ctrace, [])
        vars_ts = ts_enc._encode_vars()
        (ts, errors) = ts_enc._encode_cbs(set(["[CI]_ci1()","[CI]_ci2()"]))
        ts.product(vars_ts)
        self.assertTrue(len(errors) == 1)

        self.assertTrue(is_sat(And([errors[0],
                                    Not(TSEncoder._get_state_var("[CI]_ci1()")),
                                    Not(TSEncoder._get_state_var("[CI]_ci2()"))])))


    def test_mapback(self):
        def get_def_model(formula, vars_list, val):
            model_sat = get_model(formula)

            assert model_sat is not None

            model = {}
            for v in vars_list:
                if v not in model_sat:
                    model[v] = val
                else:
                    if model_sat.get_value(v) == TRUE():
                        model[v] = True
                    else:
                        model[v] = False

            return model

        pysmt_env = get_env()
        cenc = CounterEnc(pysmt_env)

        all_vars = []

        msg_ivar = "msg_ivar"
        cenc.add_var(msg_ivar, 10)
        all_vars.extend(cenc.get_counter_var(msg_ivar))

        pc_counter = "pc_counter"
        cenc.add_var(pc_counter, 10)
        all_vars.extend(cenc.get_counter_var(pc_counter))

        msg_vars_text = ["m_%d" % v for v in range(10)]
        msg_vars = [Symbol(v, BOOL) for v in msg_vars_text]
        all_vars.extend(msg_vars)

        auto_counters = ["a_%d" % v for v in range(2)]
        auto_counters_vars = []
        for c in auto_counters:
            cenc.add_var(c, 10)
            all_vars.extend(cenc.get_counter_var(c))

        # Fake spec (it is not important to test the mapback)
        specs = Spec.get_specs_from_string("SPEC [CB] [l] void m1() |- [CI] [l] void m2();" \
                                           "SPEC [CB] [l] void m1() |- [CI] [l] void m2()")


        mapback = TSMapback(pysmt_env, msg_ivar, pc_counter)

        mapback.add_encoder(msg_ivar, cenc)
        mapback.add_encoder(pc_counter, cenc)

        for i in range(10):
            mapback.add_vars2msg(i,"void m_%d()" % i)
        for i in range(10):
            mapback.add_pc2trace(i, i+1, "trace_%d" % i, "void m_0()")

        c0 = Or(cenc.eq_val(auto_counters[0], 0),
                cenc.eq_val(auto_counters[0], 1))
        mapback.add_var2spec(msg_vars[0], True,
                             specs[0],
                             c0,
                             specs[0])

        c1 = Or(cenc.eq_val(auto_counters[1], 2),
                cenc.eq_val(auto_counters[1], 3))
        mapback.add_var2spec(msg_vars[1], True,
                             specs[1],
                             c1,
                             specs[1])

        for i in range(10):
            m = get_def_model(cenc.eq_val(msg_ivar,i), all_vars, False)
            res = mapback.get_trans_label(m)
            self.assertTrue("void m_%d()" %i == res)

        for i in range(10):
            m = get_def_model(And(msg_vars[i], cenc.eq_val(pc_counter,i)), all_vars, False)
            m_next = get_def_model(cenc.eq_val(pc_counter,i+1), all_vars, False)
            res = mapback.get_fired_trace_msg(m, m_next)
            self.assertTrue("trace_%d" %i == res)

        current_m = get_def_model(TRUE(), all_vars, False)
        next_m = get_def_model(And([msg_vars[0], c0, Not(c1)]),
                               all_vars, False)
        fired_specs = mapback.get_fired_spec(current_m, next_m, False)
        self.assertTrue(fired_specs == [(specs[0], specs[0])])

        current_m = get_def_model(TRUE(), all_vars, False)
        next_m = get_def_model(And([Not(msg_vars[0]), c0, Not(c1)]),
                               all_vars, False)
        fired_specs = mapback.get_fired_spec(current_m, next_m, False)
        self.assertTrue(fired_specs == [])

        current_m = get_def_model(TRUE(), all_vars, False)
        next_m = get_def_model(And([msg_vars[1], c1, Not(c0)]),
                               all_vars, False)
        fired_specs = mapback.get_fired_spec(current_m, next_m, False)
        self.assertTrue(fired_specs == [(specs[1], specs[1])])

        # changes msg_vars[0]
        current_m = get_def_model(Not(msg_vars[0]),
                                  all_vars, False)
        next_m = get_def_model(And([msg_vars[0], c0, Not(c1)]),
                               all_vars, False)
        fired_specs = mapback.get_fired_spec(current_m, next_m, True)
        self.assertTrue(fired_specs == [(specs[0], specs[0])])

        current_m = get_def_model(msg_vars[0],
                                  all_vars, False)
        next_m = get_def_model(And([msg_vars[0], c0, Not(c1)]),
                               all_vars, False)
        fired_specs = mapback.get_fired_spec(current_m, next_m, True)
        self.assertTrue(fired_specs == [])


    def test_encode(self):
        ts_enc = self._get_sample_trace()

        ts = ts_enc.get_ts_encoding()

        error = ts_enc.error_prop
        bmc = BMC(ts_enc.helper, ts, error)

        # not None == there is a bug
        self.assertTrue(bmc.find_bug(0) is None)
        self.assertTrue(bmc.find_bug(1) is None)
        self.assertTrue(bmc.find_bug(2) is not None)
        self.assertTrue(bmc.find_bug(3) is not None)

        self.assertTrue(bmc.find_bug(0,True) is None)
        self.assertTrue(bmc.find_bug(1,True) is None)
        self.assertTrue(bmc.find_bug(2,True) is not None)
        self.assertTrue(bmc.find_bug(3,True) is not None)


    def test_cex_printer(self):
        ts_enc = self._get_sample_trace()
        ts = ts_enc.get_ts_encoding()
        error = ts_enc.error_prop
        bmc = BMC(ts_enc.helper, ts, error)
        cex = bmc.find_bug(2)
        cex = bmc.find_bug(2,True)

        self.assertFalse(cex is None)

        stringio = StringIO()
        printer = CexPrinter(ts_enc.mapback, cex, stringio)
        printer.print_cex()

        io_string = stringio.getvalue()
        self.assertTrue("SPEC [CB] [1] void m1() |- [CI] [1] void m2()" in io_string)
        self.assertTrue("Reached an error state in step 2" in io_string)


    def test_init_state(self):
        """ Test if specification can force an initial value

          - m2 is disabled in the initial state
          - the trace try to call m1 and then m2, causing an exception
        """
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CI] void m2()")

        ctrace = CTrace()

        cb = CCallback(1, 1, "", "void m1()", [TestGrounding._get_null()], None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ci = CCallin(1, 1, "", "void m2()", [TestGrounding._get_null()], None)
        cb.add_msg(ci)
        ctrace.add_msg(cb)

        ts_enc = TSEncoder(ctrace, spec_list)
        ts = ts_enc.get_ts_encoding()
        bmc = BMC(ts_enc.helper, ts, ts_enc.error_prop)
        self.assertTrue(bmc.find_bug(2) is not None)
        self.assertTrue(bmc.find_bug(2,True) is not None)


    def test_exception(self):
        """ Test the removal of exception from top-level callbacks
        """
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CI] void m2()")

        ctrace = CTrace()
        cb1 = CCallback(1, 1, "", "void m1()", [TestGrounding._get_null()], None,
                        [TestGrounding._get_fmwkov("","void m1()", False)])

        cb1.exception = CTraceException("void m1()", "",
                                        "NullPointerException",
                                        "NullPointerException message")

        ci1 = CCallin(1, 1, "", "void m2()", [TestGrounding._get_null()], None)
        cb1.add_msg(ci1)
        ctrace.add_msg(cb1)

        cb2 = CCallback(1, 1, "", "void m1()", [TestGrounding._get_null()], None,
                        [TestGrounding._get_fmwkov("","void m1()", False)])
        ci2 = CCallin(1, 1, "", "void m3()", [TestGrounding._get_null()], None)
        cb2.add_msg(ci2)
        ctrace.add_msg(cb2)

        ts_enc = TSEncoder(ctrace, spec_list)
        assert (1 == len(ts_enc.trace.children))
        ts = ts_enc.get_ts_encoding()
        bmc = BMC(ts_enc.helper, ts, ts_enc.error_prop)
        # if the first callback is removed, m2 cannot be called anymore
        self.assertTrue(bmc.find_bug(2) is None)
        self.assertTrue(bmc.find_bug(2,True) is None)

    def test_multiple(self):
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CB] [l] void m3(); SPEC FALSE[*] |- [CI] [l] void m4()")
        assert spec_list is not None


        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "void m3()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m3()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)

        ts_enc = TSEncoder(ctrace, spec_list)
        ts = ts_enc.get_ts_encoding()
        error = ts_enc.error_prop
        bmc = BMC(ts_enc.helper, ts, error)
        cex = bmc.find_bug(2)
        cex = bmc.find_bug(2, True)
        self.assertTrue(cex is None)


    def test_multiple_single_cb(self):
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CB] [l] void m3(); SPEC FALSE[*] |- [CI] [l] void m4()")
        assert spec_list is not None


        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "void m5()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m5()", False)])
        ctrace.add_msg(cb)
        cb = CCallback(1, 1, "", "void m3()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m3()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)

        ts_enc = TSEncoder(ctrace, spec_list)
        ts = ts_enc.get_ts_encoding()
        error = ts_enc.error_prop
        bmc = BMC(ts_enc.helper, ts, error)
        cex = bmc.find_bug(2, True)
        self.assertTrue(cex is None)

    def test_simplify_1(self):
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CB] [l] void m3(); SPEC FALSE[*] |- [CI] [l] void m4()")
        assert spec_list is not None

        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "void m5()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m5()", False)])
        ctrace.add_msg(cb)
        cb = CCallback(1, 1, "", "void m3()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m3()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)

        ts_enc = TSEncoder(ctrace, spec_list, True)

        self.assertTrue(2 == ts_enc.trace.get_total_msg())


    def test_simplify_2(self):
        spec_list = Spec.get_specs_from_string("SPEC FALSE[*] |- [CB] [l] void m3(); SPEC FALSE[*] |- [CI] [l] void m4()")
        assert spec_list is not None

        ctrace = CTrace()
        cb = CCallback(1, 1, "", "void m1()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m1()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m2()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "void m5()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m5()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "void m3()",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("","void m3()", False)])
        ctrace.add_msg(cb)
        ci = CCallin(1, 1, "", "void m4()",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)

        ts_enc = TSEncoder(ctrace, spec_list, True)

        self.assertTrue(4 == ts_enc.trace.get_total_msg())


    def test_simulation(self):
        ts_enc = self._get_sample_trace()

        ts = ts_enc.get_ts_encoding()
        trace_enc = ts_enc.get_trace_encoding()

        bmc = BMC(ts_enc.helper, ts, FALSE())
        (step, trace) = bmc.simulate(trace_enc)

        self.assertTrue(trace is not None)

