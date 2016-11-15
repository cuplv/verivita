""" Test the automata library """

import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.automata import SatLabel, Automaton


import sys

from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
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

        for l in labels:
            _check_tautologies(l)


    def test_auto(self):
        symbols = [Symbol(chr(i), BOOL) for i in range(ord('a'),ord('z')+1)]

        a = SatLabel(symbols[0])
        b = SatLabel(symbols[1])
        c = SatLabel(symbols[2])

        # test copy
        auto_a = Automaton.get_singleton(a)
        copy_1 = auto_a.copy_reachable()
        copy_2 = copy_1.copy_reachable()
        for auto in [auto_a, copy_1, copy_2]:
            self.assertFalse(auto.is_empty())
            self.assertTrue(auto.accept([a]))
            self.assertFalse(auto.accept([a,a]))

        # aa
        auto_aa = auto_a.concatenate(auto_a)
        self.assertFalse(auto_aa.is_empty())
        self.assertFalse(auto_aa.accept([a]))
        self.assertTrue(auto_aa.accept([a,a]))
        self.assertFalse(auto_aa.accept([a,a,a]))

        # a[*]
        auto_astar = auto_a.klenee_star()
        self.assertFalse(auto_astar.is_empty())
        self.assertTrue(auto_astar.accept([]))
        self.assertTrue(auto_astar.accept([a,a]))
        self.assertTrue(auto_astar.accept([a,a,a]))

        # TRUE
        aut_true = Automaton.get_singleton(SatLabel(TRUE()))
        self.assertFalse(aut_true.is_empty())
        self.assertFalse(aut_true.accept([]))
        self.assertTrue(aut_true.accept([a]))
        self.assertTrue(aut_true.accept([b]))
        self.assertTrue(aut_true.accept([c]))
        self.assertFalse(aut_true.accept([a,b]))

        # TRUE[*]
        aut_truestar = aut_true.klenee_star()
        self.assertFalse(aut_truestar.is_empty())
        self.assertTrue(aut_truestar.accept([]))
        self.assertTrue(aut_truestar.accept([a]))
        self.assertTrue(aut_truestar.accept([b]))
        self.assertTrue(aut_truestar.accept([c]))
        self.assertTrue(aut_truestar.accept([a,b]))

        a = Automaton()
        self.assertTrue(a.is_empty())
        a = Automaton.get_empty()
        self.assertTrue(a.is_empty())

