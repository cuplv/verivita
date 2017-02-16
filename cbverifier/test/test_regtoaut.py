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
from cbverifier.encoding.grounding import GroundSpecs
from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *

from cbverifier.traces.ctrace import CCallback, CCallin

from cbverifier.test.test_grounding import TestGrounding

from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

class TestRegExpToAuto(unittest.TestCase):

    def test_regexptoauto(self):
        auto_env = AutoEnv.get_global_auto_env()
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

        spec_list = Spec.get_specs_from_string("SPEC [CB] [ENTRY] [l] void m1() |- TRUE; " +
                                               "SPEC ([CB] [ENTRY] [l] void m1() & [CI] [ENTRY] [l] void m2()) |- TRUE; " +
                                               "SPEC ([CB] [ENTRY] [l] void m1() | [CI] [ENTRY] [l] void m2()) |- TRUE; " +
                                               "SPEC (! [CB] [ENTRY] [l] void m1()) |- TRUE; " +
                                               "SPEC [CB] [ENTRY] [l] void m1(); [CI] [ENTRY] [l] void m2() |- TRUE; " +
                                               "SPEC [CB] [ENTRY] [l] void m1()[*] |- TRUE")
        assert spec_list is not None

        m1 = new_call_entry(new_cb(), new_id("l"), new_id("void m1"), new_nil())
        m2 = new_call_entry(new_ci(), new_id("l"), new_id("void m2"), new_nil())
        m1_cb = CCallback(1, 1, "", "void m1()", [TestGrounding._get_obj("1","")],
                          None, [TestGrounding._get_fmwkov("", "void m1()", False)])
        m2_ci = CCallin(1, 1, "", "void m2()", [TestGrounding._get_obj("1","")], None)
        binding = TestGrounding.newAssign([new_id('l'), (True,m1), (True,m2)],
                                          [TestGrounding._get_obj("1","string"), m1_cb, m2_ci])

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

        spec_list = Spec.get_specs_from_string("SPEC [CB] [ENTRY] [l] void m1() |- TRUE; " +
                                               "SPEC [CB] [EXIT] [l] void m1() |- TRUE; " +
                                               "SPEC [CB] [ENTRY] [l] void m1() & [CB] [EXIT] [l] void m1() |- TRUE")
        assert spec_list is not None

        m1_entry = new_call_entry(new_cb(), new_id("l"), new_id("void m1"), new_nil())
        m1_exit = new_call_exit(new_nil(), new_cb(), new_id("l"), new_id("void m1"), new_nil())
        m1_cb = CCallback(1, 1, "", "void m1()", [TestGrounding._get_obj("1","")],
                          None, [TestGrounding._get_fmwkov("", "void m1()", False)])
        binding = TestGrounding.newAssign([new_id('l'), (True,m1_entry), (False,m1_exit)],
                                          [TestGrounding._get_obj("1","string"), m1_cb, m1_cb])

        # Test l.m1()
        gs = GroundSpecs._substitute(spec_list[0], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(l_m1_entry))
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1_exit()
        gs = GroundSpecs._substitute(spec_list[1], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(l_m1_exit))
        self.assertTrue(auto.is_equivalent(res))

        # Test l.m1() and l.m2()
        gs = GroundSpecs._substitute(spec_list[2], binding)
        regexp = get_regexp_node(gs)
        auto = r2a.get_from_regexp(regexp)
        res = Automaton.get_singleton(env.new_label(And(l_m1_entry, l_m1_exit)))
        self.assertTrue(auto.is_equivalent(res))
