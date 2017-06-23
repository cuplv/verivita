""" Test the construction of the automaton from a regexp """

import logging
import unittest

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.automata import Automaton, AutoEnv
from cbverifier.encoding.encoder import RegExpToAuto, TSMapback
from cbverifier.encoding.counter_enc import CounterEnc
from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *

from cbverifier.traces.ctrace import CCallback, CCallin

from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE, get_env
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

class TestRegExpToAuto(unittest.TestCase):

    def test_regexptoauto(self):
        auto_env = AutoEnv.get_global_auto_env()
        # auto_env = AutoEnv(get_env(), True)
        cenc = CounterEnc(auto_env.pysmt_env)
        alphabet = set(["[CB]_[ENTRY]_void m1()(1)","[CI]_[ENTRY]_void m2()(1)",
                        "[CB]_[ENTRY]_void m3()(1)"])

        r2a = RegExpToAuto(cenc, alphabet,
                           TSMapback(auto_env.pysmt_env, None, None),
                           auto_env)
        env = r2a.auto_env

        l1 = r2a.get_msg_eq("[CB]_[ENTRY]_void m1()(1)")
        l2 = r2a.get_msg_eq("[CI]_[ENTRY]_void m2()(1)")
        l3 = r2a.get_msg_eq("[CB]_[ENTRY]_void m3()(1)")

        spec_list = Spec.get_specs_from_string("SPEC [CB] [ENTRY] [1] void m1() |- TRUE; " +
                                               "SPEC ([CB] [ENTRY] [1] void m1() & [CI] [ENTRY] [1] void m2()) |- TRUE; " +
                                               "SPEC ([CB] [ENTRY] [1] void m1() | [CI] [ENTRY] [1] void m2()) |- TRUE; " +
                                               "SPEC (! [CB] [ENTRY] [1] void m1()) |- TRUE; " +
                                               "SPEC [CB] [ENTRY] [1] void m1(); [CI] [ENTRY] [1] void m2() |- TRUE; " +
                                               "SPEC [CB] [ENTRY] [1] void m1()[*] |- TRUE;" +
                                               "SPEC ([CB] [ENTRY] [1] void m1() & ([CI] [ENTRY] [1] void m2(); [CB] [ENTRY] [1] void m3())) |- TRUE ")
        assert spec_list is not None

        # Test l.m1()
        regexp = get_regexp_node(spec_list[0].ast)
        auto = r2a.get_from_regexp(regexp)
        label = env.new_label(l1)
        res = Automaton.get_singleton(label, auto_env)
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1() and l.m2()
        regexp = get_regexp_node(spec_list[1].ast)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(And(l1, l2)), auto_env)
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1() or l.m2()
        regexp = get_regexp_node(spec_list[2].ast)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(Or(l1, l2)), auto_env)
        self.assertTrue(auto.is_equivalent(res))

        # Test not l.m1()
        regexp = get_regexp_node(spec_list[3].ast)
        auto = r2a.get_from_regexp(regexp)
        l1_aut = Automaton.get_singleton(env.new_label(l1), auto_env)
        res = l1_aut.complement()

        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1(); l.m1()
        regexp = get_regexp_node(spec_list[4].ast)
        auto = r2a.get_from_regexp(regexp)
        r1 = Automaton.get_singleton(env.new_label(l1), auto_env)
        r2 = Automaton.get_singleton(env.new_label(l2), auto_env)
        res = r1.concatenate(r2)
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1()[*]
        regexp = get_regexp_node(spec_list[5].ast)
        auto = r2a.get_from_regexp(regexp)
        r1 = Automaton.get_singleton(env.new_label(l1), auto_env)
        res = r1.klenee_star()
        self.assertTrue(auto.is_equivalent(res))

        # intersection of different regexpes
        regexp = get_regexp_node(spec_list[6].ast)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(FALSE()), auto_env)
        self.assertTrue(auto.is_equivalent(res))


    def test_regexptoauto_exit(self):
        auto_env = AutoEnv.get_global_auto_env()
        cenc = CounterEnc(auto_env.pysmt_env)
        alphabet = set(["[CB]_[ENTRY]_void m1()(1)","[CB]_[EXIT]_void m1()(1)"])
        r2a = RegExpToAuto(cenc, alphabet, TSMapback(auto_env.pysmt_env, None,
                                                     None),
                           auto_env)
        env = r2a.auto_env

        l_m1_entry = r2a.get_msg_eq("[CB]_[ENTRY]_void m1()(1)")
        l_m1_exit = r2a.get_msg_eq("[CB]_[EXIT]_void m1()(1)")

        spec_list = Spec.get_specs_from_string("SPEC [CB] [ENTRY] [1] void m1() |- TRUE; " +
                                               "SPEC [CB] [EXIT] [1] void m1() |- TRUE; " +
                                               "SPEC [CB] [ENTRY] [1] void m1() & [CB] [EXIT] [1] void m1() |- TRUE")
        assert spec_list is not None

        # Test l.m1()
        regexp = get_regexp_node(spec_list[0].ast)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(l_m1_entry))
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1_exit()
        regexp = get_regexp_node(spec_list[1].ast)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(l_m1_exit))
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1() and l.m2()
        regexp = get_regexp_node(spec_list[2].ast)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(And(l_m1_entry, l_m1_exit)))
        self.assertTrue(auto.is_equivalent(res))
