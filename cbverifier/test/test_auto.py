""" Test the automata library """

import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.automata import SatLabel, BddLabel, Automaton, AutoEnv


import sys

import pysmt
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE, get_env
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne



class TestAuto(unittest.TestCase):

    def test_labels(self):
        def _check_tautologies(l1):
            l1_not = l1.complement()

            self.assertTrue(l1.is_contained(l1))
            self.assertFalse(l1.is_intersecting(l1_not))
            self.assertFalse(l1.is_contained(l1_not))
            self.assertFalse(l1_not.is_contained(l1))

            l1_union = l1.union(l1_not)
            self.assertTrue(l1_union.is_sat())
            self.assertTrue(l1_union.is_valid())

            l1_int = l1.intersect(l1_not)
            self.assertFalse(l1_int.is_sat())
            self.assertFalse(l1_int.is_valid())

        symbols = [Symbol(chr(i), BOOL) for i in range(ord('a'),ord('z')+1)]

        # just try some formulas
        labels = [SatLabel(And(symbols[0], symbols[1])),
                  SatLabel(Or(symbols[1], symbols[1])),
                  SatLabel(Not(And(symbols[0], symbols[1]))),
                  SatLabel(And(Not(symbols[0]), symbols[1]))]

        if self._has_bdd():
            bdd_env = AutoEnv(get_env(), True)

            labels.extend([BddLabel(And(symbols[0], symbols[1]), bdd_env),
                           BddLabel(Or(symbols[1], symbols[1]), bdd_env),
                           BddLabel(Not(And(symbols[0], symbols[1])), bdd_env),
                           BddLabel(And(Not(symbols[0]), symbols[1]), bdd_env)])

        for l in labels:
            _check_tautologies(l)

    def _has_bdd(self):
        try:
            from pysmt.solvers.bdd import BddSolver
        except pysmt.exceptions.SolverAPINotFound:
            return False
        return True

    def test_auto(self):
        sat_env = AutoEnv(get_env(), False)
        self._test_auto_aux(sat_env)

        if self._has_bdd():
            bdd_env = AutoEnv(get_env(), True)
            self._test_auto_aux(bdd_env)

    def _test_auto_aux(self, auto_env):
        def _check_auto_tautologies(auto):
            self.assertTrue(auto.is_equivalent(auto))
            self.assertTrue(auto.is_equivalent(auto.copy_reachable()))
            self.assertTrue(auto.is_equivalent(auto.complete()))
            self.assertTrue(auto.is_equivalent(auto.determinize()))
            self.assertTrue(auto.is_equivalent(auto.union(auto)))
            self.assertTrue(auto.is_equivalent((auto.reverse()).reverse()))
            self.assertTrue(auto.is_equivalent(auto.minimize()))

        symbols = [Symbol(chr(i), BOOL) for i in range(ord('a'),ord('z')+1)]

        a = auto_env.new_label(symbols[0])
        b = auto_env.new_label(symbols[1])
        c = auto_env.new_label(symbols[2])

        # test copy
        auto_a = Automaton.get_singleton(a, auto_env)
        self.assertTrue(auto_a.is_equivalent(auto_a))

        copy_1 = auto_a.copy_reachable()
        copy_2 = copy_1.copy_reachable()
        det = auto_a.determinize()
        twice_neg = auto_a.complement().complement()
        complete = auto_a.complete()
        for auto in [auto_a, copy_1, copy_2, twice_neg, complete]:
            self.assertFalse(auto.is_empty())
            self.assertTrue(auto.accept([a]))
            self.assertFalse(auto.accept([a,a]))
            _check_auto_tautologies(auto)

        auto_a_neg = auto_a.complement()
        self.assertFalse(auto_a_neg.accept([a]))
        self.assertTrue(auto_a_neg.accept([a,a]))
        self.assertTrue(auto_a_neg.accept([b]))

        # aa
        auto_aa = auto_a.concatenate(auto_a)
        det = auto_aa.determinize()
        twice_neg = auto_aa.complement().complement()
        complete = auto_aa.complete()
        for auto in [auto_aa, det, twice_neg, complete]:
            self.assertFalse(auto.is_empty())
            self.assertFalse(auto.accept([a]))
            self.assertTrue(auto.accept([a,a]))
            self.assertFalse(auto.accept([a,a,a]))
            _check_auto_tautologies(auto)

        auto_aa_neg = auto_aa.complement()
        self.assertTrue(auto_aa_neg.accept([a]))
        self.assertTrue(auto_aa_neg.accept([b]))
        self.assertFalse(auto_aa_neg.accept([a,a]))
        self.assertTrue(auto_aa_neg.accept([a,a,a]))

        # a[*]
        auto_astar = auto_a.klenee_star()
        det = auto_astar.determinize()
        twice_neg = auto_astar.complement().complement()
        complete = auto_astar.complete()
        for auto in [auto_astar, det, twice_neg, complete]:
            self.assertFalse(auto.is_empty())
            self.assertTrue(auto.accept([]))
            self.assertTrue(auto.accept([a,a]))
            self.assertTrue(auto.accept([a,a,a]))
            _check_auto_tautologies(auto)

        # TRUE
        aut_true = Automaton.get_singleton(auto_env.new_label(TRUE()), auto_env)
        twice_neg = aut_true.complement().complement()
        det = aut_true.determinize()
        complete = aut_true.complete()
        for auto in [aut_true, det, twice_neg, complete]:
            self.assertFalse(det.is_empty())
            self.assertFalse(det.accept([]))
            self.assertTrue(det.accept([a]))
            self.assertTrue(det.accept([b]))
            self.assertTrue(det.accept([c]))
            self.assertFalse(det.accept([a,b]))
            _check_auto_tautologies(auto)

        # TRUE[*]
        aut_truestar = aut_true.klenee_star()
        twice_neg = aut_truestar.complement().complement()
        det = aut_truestar.determinize()
        complete = aut_truestar.complete()
        for auto in [aut_truestar, det, twice_neg, complete]:
            self.assertFalse(auto.is_empty())
            self.assertTrue(auto.accept([]))
            self.assertTrue(auto.accept([a]))
            self.assertTrue(auto.accept([b]))
            self.assertTrue(auto.accept([c]))
            self.assertTrue(auto.accept([a,b]))
            _check_auto_tautologies(auto)

        a = Automaton()
        self.assertTrue(a.is_empty())
        a = Automaton.get_empty(auto_env)
        self.assertTrue(a.is_empty())

    def test_enum_trans(self):
        env = AutoEnv.get_global_auto_env()
        solver = env.sat_solver

        symbols = [Symbol(chr(i), BOOL) for i in range(ord('a'),ord('z')+1)]
        false_label = env.new_label(FALSE())
        true_label = env.new_label(TRUE())
        a = env.new_label(symbols[0])
        b = env.new_label(symbols[1])
        c = env.new_label(symbols[2])
        a_and_b = a.intersect(b)

        results = Automaton.enum_trans([false_label], env.sat_solver)
        self.assertTrue(len(results) == 1)

        results = Automaton.enum_trans([true_label], env.sat_solver)
        self.assertTrue(len(results) == 1)

        results = Automaton.enum_trans([a,b,c], env.sat_solver)
        self.assertTrue(len(results) == 8)

        results = Automaton.enum_trans([a,b,a_and_b], env.sat_solver)
        self.assertTrue(len(results) == 4)


    def test_enum_trans(self):
        def _compare(solver, res, expected):
            """ Not efficient, but ok for tests"""

            if len(res) != len(expected):
                return False

            for (exp_set, exp_label) in expected:
                found = False
                for (res_set, res_label) in res:
                    if (res_set == exp_set):
                        exp_f = exp_label.get_formula()
                        res_f = res_label.get_formula()
                        if (solver.is_valid(Iff(exp_f, res_f))):
                            found = True
                            break
                if (not found):
                    return False
            return True

        symbols = [Symbol(chr(i), BOOL) for i in range(ord('a'),ord('z')+1)]
        env = AutoEnv.get_global_auto_env()
        solver = env.sat_solver

        a = symbols[0]
        b = symbols[1]
        c = symbols[2]
        d = symbols[3]

        a_label = env.new_label(a)
        b_label = env.new_label(b)
        c_label = env.new_label(c)
        d_label = env.new_label(d)

        auto_a = Automaton.get_singleton(a_label, env)
        res = auto_a._sc_enum_trans(auto_a.initial_states)
        expected = [(set([1]), a_label), (set([]), a_label.complement())]
        self.assertTrue(_compare(solver, res, expected))

        auto_a = Automaton()
        s0 = auto_a._add_new_state()
        s1 = auto_a._add_new_state()
        s2 = auto_a._add_new_state()
        s3 = auto_a._add_new_state()
        s4 = auto_a._add_new_state()
        s5 = auto_a._add_new_state()
        auto_a._add_trans(s0,s1,a_label)
        auto_a._add_trans(s0,s2,b_label)
        auto_a._add_trans(s2,s3,c_label)
        auto_a._add_trans(s2,s4,a_label)
        auto_a._add_trans(s4,s5,d_label)

        res = auto_a._sc_enum_trans(set([s0,s2,s3]))
        expected = [(set([]), env.new_label(And([Not(a), Not(b), Not(c)]))),
                    (set([3]), env.new_label(And([Not(a), Not(b), c]))),
                    (set([2]), env.new_label(And([Not(a), b, Not(c)]))),
                    (set([2,3]), env.new_label(And([Not(a), b, c]))),
                    (set([1,4]), env.new_label(And([a, Not(b), Not(c)]))),
                    (set([1,3,4]), env.new_label(And([a, Not(b), c]))),
                    (set([1,2,4]), env.new_label(And([a, b, Not(c)]))),
                    (set([1,2,3,4]), env.new_label(And([a, b,c])))]

        self.assertTrue(_compare(solver, res, expected))

    def test_seq(self):
        env = AutoEnv.get_global_auto_env()

        a_label = env.new_label(Symbol('a'))
        b_label = env.new_label(Symbol('b'))
        c_label = env.new_label(Symbol('c'))

        auto_a = Automaton.get_singleton(env.new_label(TRUE()))
        auto_b = auto_a.klenee_star()
        auto_c = Automaton.get_singleton(a_label)
        auto_d = auto_b.concatenate(auto_c)

        self.assertFalse(auto_d.accept([]))

    def test_seq_2(self):
        env = AutoEnv.get_global_auto_env()

        a_label = env.new_label(Symbol('a'))
        b_label = env.new_label(Symbol('b'))
        c_label = env.new_label(Symbol('c'))

        auto_true_star = Automaton.get_singleton(env.new_label(TRUE())).klenee_star()
        auto_do_a = Automaton.get_singleton(a_label)
        auto_ts_a  = auto_true_star.concatenate(auto_do_a)
        auto_ts_a_ts = auto_ts_a.concatenate(auto_true_star)

        self.assertTrue(auto_ts_a_ts.accept([a_label]))
        self.assertFalse(auto_ts_a_ts.accept([]))

    def test_iss171(self):
        auto_env = AutoEnv(get_env(), False)

        auto = Automaton(auto_env)

        s0 = auto._add_new_state(True, True)
        s1 = auto._add_new_state(False, False)
        s2 = auto._add_new_state(False, True)

        l1 = auto_env.new_label(Symbol('l1'))
        true_label = auto_env.new_label(TRUE())

        auto._add_trans(s0, s1, l1)
        auto._add_trans(s0, s2, l1)
        auto._add_trans(s1, s2, true_label)
        auto._add_trans(s1, s2, true_label)

        auto.klenee_star()


    def test_iss198(self):
        auto_env = AutoEnv(get_env(), False)
        auto = Automaton(auto_env)
        
        # Add a single initial state
        s0 = auto._add_new_state(True, False)

        det_auto = auto.determinize()
    

        self.assertTrue(len(det_auto.trans[0]) >0 )
