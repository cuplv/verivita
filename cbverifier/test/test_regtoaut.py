""" Test the construction of the automaton from a regexp """

import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.automata import Automaton, AutoEnv
from cbverifier.encoding.encoder import RegExpToAuto
from cbverifier.encoding.counter_enc import CounterEnc
from cbverifier.encoding.grounding import GroundSpecs
from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *

from cbverifier.test.test_grounding import TestGrounding

from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

class TestRegExpToAuto(unittest.TestCase):

    def test_regexptoauto(self):
        auto_env = AutoEnv.get_global_auto_env()
        cenc = CounterEnc(auto_env.pysmt_env)
        alphabet = set(["[CB]_m1(1)","[CI]_m2(1)","[CB]_m3(1)"])

        r2a = RegExpToAuto(cenc, alphabet, auto_env)
        env = r2a.auto_env

        l1 = r2a.get_msg_eq("[CB]_m1(1)")
        l2 = r2a.get_msg_eq("[CI]_m2(1)")
        l3 = r2a.get_msg_eq("[CB]_m3(1)")

        spec_list = Spec.get_specs_from_string("SPEC [CB] [l] m1() |- TRUE; " +
                                               "SPEC ([CB] [l] m1() & [CI] [l] m2()) |- TRUE; " +
                                               "SPEC ([CB] [l] m1() | [CI] [l] m2()) |- TRUE; " +
                                               "SPEC (! [CB] [l] m1()) |- TRUE; " +
                                               "SPEC [CB] [l] m1(); [CI] [l] m2() |- TRUE; " +
                                               "SPEC [CB] [l] m1()[*] |- TRUE")
        assert spec_list is not None
        binding = TestGrounding.newAssign(
            [new_id('l')], [TestGrounding._get_obj("1","string")])

        # Test l.m1()
        gs = GroundSpecs._substitute(spec_list[0], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(l1))
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1() and l.m2()
        gs = GroundSpecs._substitute(spec_list[1], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(And(l1, l2)))
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1() or l.m2()
        gs = GroundSpecs._substitute(spec_list[2], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(Or(l1, l2)))
        self.assertTrue(auto.is_equivalent(res))

        # Test not l.m1()
        gs = GroundSpecs._substitute(spec_list[3], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(Not(l1)))
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1(); l.m1()
        gs = GroundSpecs._substitute(spec_list[4], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        r1 = Automaton.get_singleton(env.new_label(l1))
        r2 = Automaton.get_singleton(env.new_label(l2))
        res = r1.concatenate(r2)
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1()[*]
        gs = GroundSpecs._substitute(spec_list[5], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        r1 = Automaton.get_singleton(env.new_label(l1))
        res = r1.klenee_star()
        self.assertTrue(auto.is_equivalent(res))

