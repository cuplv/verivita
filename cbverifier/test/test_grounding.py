""" Test the grounding of specifications

"""

import logging
import unittest

from ply.lex import LexToken
import ply.yacc as yacc


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.grounding import GroundSpecs, Assignments, AssignmentsSet, TraceMap
from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue
from cbverifier.specs.spec_ast import *

class TestGrounding(unittest.TestCase):

    def _new_ass(self,variables, values):
        assert len(values) == len(variables)
        a = Assignments()
        for v,l in zip(variables, values): a.add(v,l)
        return a

    def _new_bottom_ass(self):
        a = Assignments()
        a._is_bottom = True
        return a


    def _check_val(self, a, variables, values, is_bottom=False):
        assert len(values) == len(variables)
        for v,l in zip(variables, values):
            self.assertTrue(a.get(v) == l)
        assert not is_bottom or a.is_bottom()
        assert is_bottom or not a.is_bottom()
        return a

    def test_assignments(self):
        a = self._new_ass(['x','y'],[1,2])
        self._check_val(a, ['x','y'],[1,2])

        a1 = self._new_ass(['x','y'],[1,2])
        a2 = self._new_ass([],[])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y'],[1,2])

        a1 = self._new_ass(['x','y'],[1,2])
        a2 = self._new_ass(['x'],[3])
        a3 = a1.intersect(a2)
        self.assertTrue(a3.is_bottom())

        a1 = self._new_ass(['x','y'],[1,2])
        a2 = self._new_ass(['x'],[1])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y'],[1,2])

        a1 = self._new_ass(['x','y'],[1,2])
        a2 = self._new_ass(['x','z'],[1,3])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y','z'],[1,2,3])

        a1 = self._new_ass(['x','y'],[1,2])
        a2 = self._new_ass(['z'],[3])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y','z'],[1,2,3])

        a1 = self._new_ass(['x','y'],[1,2])
        a2 = self._new_ass(['z'],[1])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y','z'],[1,2,1])


    def _test_aset_eq(self, aset, expected):
        res = set()
        for elem in aset: res.add(elem)
        self.assertTrue(set(expected) == res)


    def _test_aset_new(self, matrix):
        aset = AssignmentsSet()
        added = []
        for row in matrix:
            assert len(row) == 2
            a = self._new_ass(row[0],row[1])
            added.append(a)
            aset.add(a)

        self._test_aset_eq(aset, added)
        return aset



    def test_assignements_set(self):
        aset1 = self._test_aset_new([])
        aset2 = self._test_aset_new([])
        aset1 = aset1.combine(aset2)
        assert(aset1.assignments == self._test_aset_new([]).assignments)

        aset1 = self._test_aset_new([[['x','y'],[1,2]]])
        aset2 = AssignmentsSet()
        aset2.add(Assignments())
        aset_new = aset1.combine(aset2)

        assert(aset1 == aset_new)

        aset1 = self._test_aset_new([[['x','y'],[1,2]]])
        aset2 = self._test_aset_new([
            [['z'],[1]],
            [['x'],[1]],
            [['x'],[2]]])
        aset1 = aset1.combine(aset2)
        res = self._test_aset_new([
            [['x','y','z'],[1,2,1]],
            [['x','y'],[1,2]]])
        assert(aset1 == res)


    def test_trace_map(self):
        def _get_int(intValue):
            v = CValue()
            v.is_null = False
            v.type = "java.lang.int"
            v.value = intValue
            return v

        def _get_obj(objId, objType):
            v = CValue()
            v.is_null = False
            v.type = objType
            v.value = objId
            return v

        trace = CTrace()
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [_get_obj("1","string")],
                       None, ["string"], [], [])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",
                     [_get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [],
                       None, [], [], [])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",
                     [_get_obj("1","string"),_get_int(2)],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [_get_obj("2","string")],
                       None, ["string"], [], [])
        trace.add_msg(cb)

        tmap = TraceMap(trace)

        assert (len(tmap.lookup_methods("other", 0)) == 0)
        assert (len(tmap.lookup_methods("doSomethingCb", 0)) == 1)
        assert (len(tmap.lookup_methods("doSomethingCb", 1)) == 2)
        assert (len(tmap.lookup_methods("doSomethingCi", 1)) == 1)
        assert (len(tmap.lookup_methods("doSomethingCi", 2)) == 1)

        cnode = new_call(new_nil(), new_id("doSomethingCb"),
                         new_param(new_id("l"), new_nil()))
        res = tmap.lookup_assignments(cnode)
        res_2 = self._test_aset_new([
            [[new_id('l')],[_get_obj("1","string")]],
            [[new_id('l')],[_get_obj("2","string")]]])
        assert (res == res_2)

        cnode = new_call(new_nil(), new_id("doSomethingCb"),
                         new_param(new_dontcare(), new_nil()))
        res = tmap.lookup_assignments(cnode)
        res_2 = self._test_aset_new([[[],[]]])
        assert (res == res_2)

        cnode = new_call(new_nil(), new_id("doSomethingCi"),
                         new_param(new_dontcare(),
                                   new_param(new_id('z'), new_nil())))
        res = tmap.lookup_assignments(cnode)
        res_2 = self._test_aset_new([[[new_id('z')],[_get_int(2)]]])
        assert (res == res_2)
