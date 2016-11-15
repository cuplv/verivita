""" Test the automata library """

import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.automata import SatLabel

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




