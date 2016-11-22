""" Test the logarithmic encoding of counters

"""

import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.counter_enc import CounterEnc

from pysmt.shortcuts import get_model
from pysmt.shortcuts import get_env, Solver
from pysmt.shortcuts import TRUE, FALSE
from pysmt.shortcuts import And, Or, Not, Iff
import pysmt

class TestCounterEnc(unittest.TestCase):

    def setUp(self):
        self.enc = CounterEnc(get_env(), False)
        self.solver = Solver(logic=pysmt.logics.BOOL)

    def _is_eq(self, a, b):
        f = Iff(a, b)
        self.assertTrue(self.solver.is_valid(f))

    def test_0(self):
        var_name = "counter_0"
        self.enc.add_var(var_name, 0)

        b0 = self.enc._get_bitvar(var_name,0)

        e = self.enc.eq_val(var_name, 0)
        self._is_eq(e, Not(b0))

        with self.assertRaises(AssertionError):
            e = self.enc.eq_val(var_name, 1)

        mask = self.enc.get_mask(var_name)
        self._is_eq(mask, Not(b0))

    def test_1(self):
        var_name = "counter_1"
        self.enc.add_var(var_name, 1)

        b0 = self.enc._get_bitvar(var_name,0)

        e = self.enc.eq_val(var_name, 0)
        self._is_eq(e, Not(b0))
        e = self.enc.eq_val(var_name, 1)
        self._is_eq(e, b0)

        with self.assertRaises(AssertionError):
            e = self.enc.eq_val(var_name, 2)

        mask = self.enc.get_mask(var_name)
        self._is_eq(mask, TRUE())


    def test_2(self):
        # need 2 bits
        var_name = "counter_2"
        self.enc.add_var(var_name, 2)

        b0 = self.enc._get_bitvar(var_name,0)
        b1 = self.enc._get_bitvar(var_name,1)

        e = self.enc.eq_val(var_name, 0)
        self._is_eq(e, And(Not(b0), Not(b1)))
        e = self.enc.eq_val(var_name, 1)
        self._is_eq(e, And(b0, Not(b1)))
        e = self.enc.eq_val(var_name, 2)
        self._is_eq(e, And(Not(b0), b1))

        with self.assertRaises(AssertionError):
            # out of the counter bound
            e = self.enc.eq_val(var_name, 3)

        mask = self.enc.get_mask(var_name)
        self._is_eq(mask, Not(And(b0, b1)))

    def test_3(self):
        # need 2 bits
        var_name = "counter_3"
        self.enc.add_var(var_name, 3)

        b0 = self.enc._get_bitvar(var_name,0)
        b1 = self.enc._get_bitvar(var_name,1)

        e = self.enc.eq_val(var_name, 0)
        self._is_eq(e, And(Not(b0), Not(b1)))
        e = self.enc.eq_val(var_name, 1)
        self._is_eq(e, And(b0, Not(b1)))
        e = self.enc.eq_val(var_name, 2)
        self._is_eq(e, And(Not(b0), b1))
        e = self.enc.eq_val(var_name, 3)
        self._is_eq(e, And(b0, b1))

        mask = self.enc.get_mask(var_name)
        self._is_eq(mask, TRUE())


    def test_4(self):
        # need 3 bits
        var_name = "counter_4"
        self.enc.add_var(var_name, 4)

        b0 = self.enc._get_bitvar(var_name,0)
        b1 = self.enc._get_bitvar(var_name,1)
        b2 = self.enc._get_bitvar(var_name,2)

        e = self.enc.eq_val(var_name, 0)
        self._is_eq(e, And([Not(b0), Not(b1), Not(b2)]))
        e = self.enc.eq_val(var_name, 1)
        self._is_eq(e, And([b0, Not(b1), Not(b2)]))

        e = self.enc.eq_val(var_name, 4)
        self._is_eq(e, And([Not(b0), Not(b1), b2]))

        with self.assertRaises(AssertionError):
            e = self.enc.eq_val(var_name, 5)

        mask = self.enc.get_mask(var_name)
        models = Or([And([b0, Not(b1), b2]),
                     And([Not(b0), b1, b2]),
                     And([b0, b1, b2])])
        self._is_eq(mask, Not(models))


    def test_value(self):
        def eq_value(self, var_name, value):
            eq_val = self.enc.eq_val(var_name, value)
            self.solver.is_sat(eq_val)
            model = self.solver.get_model()
            res = self.enc.get_counter_value(var_name, model)
            self.assertTrue(res == value)

        var_name = "counter_4"

        self.enc.add_var(var_name, 4)
        eq_value(self, var_name, 0)
        eq_value(self, var_name, 1)
        eq_value(self, var_name, 2)
        eq_value(self, var_name, 3)
        eq_value(self, var_name, 4)


