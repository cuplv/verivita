""" Test the grounding of specifications

"""

import sys
import logging
import unittest

from ply.lex import LexToken
import ply.yacc as yacc


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.encoding.grounding import GroundSpecs, Assignments, AssignmentsSet, TraceMap
from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, FrameworkOverride, CValue
from cbverifier.specs.spec_ast import *
from cbverifier.specs.spec import Spec

class TestGrounding(unittest.TestCase):

    @staticmethod
    def newAssign(variables, values):
        assert len(values) == len(variables)
        a = Assignments()
        for v,l in zip(variables, values): a.add(v,l)
        return a

    @staticmethod
    def _get_int(intValue):
        v = CValue()
        v.is_null = False
        v.type = "java.lang.int"
        v.value = intValue
        return v

    @staticmethod
    def _get_obj(objId, objType):
        v = CValue()
        v.is_null = False
        v.type = objType
        v.value = objId
        return v

    @staticmethod
    def _get_fmwkov(cname, mname, is_int):
        return FrameworkOverride(cname, mname, is_int)

    def _new_bottom_ass(self):
        a = Assignments()
        a._is_bottom = True
        return a

    @staticmethod
    def newBinding(matrix):
        """ Create a new assignment set """
        aset = AssignmentsSet()
        added = []
        for row in matrix:
            assert len(row) == 2
            a = TestGrounding.newAssign(row[0],row[1])
            added.append(a)
            aset.add(a)
            assert a.is_frozen()

        # Checks if two assignemnts set are the same
        res = set()
        for elem in aset: res.add(elem)
        assert(set(added) == res)

        return aset

    def _check_val(self, a, variables, values, is_bottom=False):
        assert len(values) == len(variables)
        for v,l in zip(variables, values):
            self.assertTrue(a.get(v) == l)
        assert not is_bottom or a.is_bottom()
        assert is_bottom or not a.is_bottom()
        return a

    def test_assignments(self):
        a = TestGrounding.newAssign(['x','y'],[1,2])
        self._check_val(a, ['x','y'],[1,2])

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        a2 = TestGrounding.newAssign([],[])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y'],[1,2])

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        a2 = TestGrounding.newAssign(['x'],[3])
        a3 = a1.intersect(a2)
        self.assertTrue(a3.is_bottom())

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        a2 = TestGrounding.newAssign(['x'],[1])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y'],[1,2])

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        a2 = TestGrounding.newAssign(['x','z'],[1,3])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y','z'],[1,2,3])

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        a2 = TestGrounding.newAssign(['z'],[3])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y','z'],[1,2,3])

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        a2 = TestGrounding.newAssign(['z'],[1])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y','z'],[1,2,1])

    def test_assignements_set(self):
        aset1 = TestGrounding.newBinding([])
        aset2 = TestGrounding.newBinding([])
        aset1 = aset1.combine(aset2)
        assert(aset1.assignments == TestGrounding.newBinding([]).assignments)

        aset1 = TestGrounding.newBinding([[['x','y'],[1,2]]])
        aset2 = AssignmentsSet()
        aset2.add(Assignments())
        aset_new = aset1.combine(aset2)

        assert(aset1 == aset_new)

        aset1 = TestGrounding.newBinding([[['x','y'],[1,2]]])
        aset2 = TestGrounding.newBinding([
            [['z'],[1]],
            [['x'],[1]],
            [['x'],[2]]])
        aset1 = aset1.combine(aset2)
        res = TestGrounding.newBinding([
            [['x','y','z'],[1,2,1]],
            [['x','y'],[1,2]]])
        assert(aset1 == res)

    def test_trace_map(self):
        trace = CTrace()
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [TestGrounding._get_obj("1","string")],
                       None, [TestGrounding._get_fmwkov("","doSomethingCb",False)])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",
                     [TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [],
                       None, [TestGrounding._get_fmwkov("","doSomethingCb",False)])
        trace.add_msg(cb)
        ci = CCallin(1, 1, "", "doSomethingCi",
                     [TestGrounding._get_obj("1","string"), TestGrounding._get_int(2)],
                     None)
        cb.add_msg(ci)
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [TestGrounding._get_obj("2","string")],
                       None, [TestGrounding._get_fmwkov("","doSomethingCb",False)])
        trace.add_msg(cb)

        cb = CCallback(1, 1, "", "doSomethingCb",
                       [TestGrounding._get_obj("2","string")],
                       TestGrounding._get_obj("3","string"),
                       [TestGrounding._get_fmwkov("","doSomethingCb",False)])
        trace.add_msg(cb)

        cb = CCallback(1, 1, "package.MyClass", "testClassName",
                       [TestGrounding._get_obj("2","string")],
                       TestGrounding._get_obj("3","string"),
                       [TestGrounding._get_fmwkov("package.MyClass","testClassName",False)])
        trace.add_msg(cb)

        cb = CCallback(1, 1, "package.MyClass", "testAssignConstant",
                       [TestGrounding._get_obj("2","string")],
                       TestGrounding._get_int(3),
                       [TestGrounding._get_fmwkov("package.MyClass","testAssignConstant",False)])
        trace.add_msg(cb)

        # Test first framework type
        cb = CCallback(1, 1, "package.MyClass", "testClassName",
                       [TestGrounding._get_obj("2","string")],
                       TestGrounding._get_obj("3","string"),
                       [TestGrounding._get_fmwkov("android.Button",
                                                  "testClassName", False),
                        TestGrounding._get_fmwkov("android.ButtonInterface",
                                                  "testClassName", True),
                        TestGrounding._get_fmwkov("android.ButtonInner",
                                                  "testClassName", False)])
        trace.add_msg(cb)

        tmap = TraceMap(trace)

        assert (len(tmap.lookup_methods(new_ci(), "other", 0, False)) == 0)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCb", 0, False)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCb", 1, False)) == 2)
        assert (len(tmap.lookup_methods(new_ci(), "doSomethingCi", 1, False)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCi", 1, False)) == 0)
        assert (len(tmap.lookup_methods(new_ci(), "doSomethingCi", 2, False)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCb", 1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "package.MyClass.testClassName",
                                        1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "android.Button.testClassName",
                                        1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "android.ButtonInner.testClassName",
                                        1, True)) == 0)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "android.ButtonInterface.testClassName",
                                        1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "package.MyClass.testAssignConstant",
                                        1, True)) == 1)


        cnode = new_call(new_nil(), new_cb(),
                         new_nil(), new_id("doSomethingCb"),
                         new_param(new_id("l"), new_nil()))
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([
            [[new_id('l')],[TestGrounding._get_obj("1","string")]],
            [[new_id('l')],[TestGrounding._get_obj("2","string")]]])
        assert (res == res_2)

        cnode = new_call(new_nil(), new_cb(),
                         new_nil(), new_id("doSomethingCb"),
                         new_param(new_dontcare(), new_nil()))
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([[[],[]]])
        assert (res == res_2)

        cnode = new_call(new_nil(), new_ci(),
                         new_nil(), new_id("doSomethingCi"),
                         new_param(new_dontcare(),
                                   new_param(new_id('z'), new_nil())))
        res = tmap.lookup_assignments(cnode)

        res_2 = TestGrounding.newBinding([[[new_id('z')],[ TestGrounding._get_int(2)]]])
        assert (res == res_2)

        cnode = new_call(new_id("z"), new_cb(),
                         new_nil(), new_id("doSomethingCb"),
                         new_param(new_id("l"), new_nil()))
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([
            [[new_id('z'),new_id('l')],
             [TestGrounding._get_obj("3","string"),
              TestGrounding._get_obj("2","string")]]])
        assert (res == res_2)

        cnode = new_call(new_id("z"), new_cb(),
                         new_nil(), new_id("package.MyClass.testClassName"),
                         new_param(new_id("l"), new_nil()))
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([
            [[new_id('z'),new_id('l')],
             [TestGrounding._get_obj("3","string"),
              TestGrounding._get_obj("2","string")]]])
        assert (res == res_2)

        cnode = new_call(new_int(3), new_cb(),
                         new_nil(), new_id("package.MyClass.testAssignConstant"),
                         new_param(new_id("l"), new_nil()))
        res = tmap.lookup_assignments(cnode)

        res_2 = TestGrounding.newBinding([
            [[new_id('l')],
             [TestGrounding._get_obj("2","string")]]])
        assert (res == res_2)



    def test_ground_bindings(self):
        trace = CTrace()
        cb = CCallback(1, 1, "", "doSomethingCb",
                       [TestGrounding._get_obj("1","string")],
                       None,
                       [TestGrounding._get_fmwkov("",
                                                  "doSomethingCb", False)])
        trace.add_msg(cb)

        # 1.doSomethingCi(2)
        ci = CCallin(1, 1, "", "doSomethingCi",
                     [TestGrounding._get_obj("1","string"),
                      TestGrounding._get_obj("2","string")],
                     None)
        cb.add_msg(ci)

        # 3.otherCi(1)
        ci = CCallin(1, 1, "", "otherCi",
                     [TestGrounding._get_obj("4","string"),
                      TestGrounding._get_obj("1","string")],
                     None)
        cb.add_msg(ci)

        # 1.doSomethingCi(4)
        ci = CCallin(1, 1, "", "doSomethingCi",
                     [TestGrounding._get_obj("1","string"),
                      TestGrounding._get_obj("4","string")],
                     None)
        cb.add_msg(ci)

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC [CI] [l] doSomethingCi(z) |- [CI] [z] otherCi(f)")
        bindings = gs._get_ground_bindings(spec)
        res = TestGrounding.newBinding([
            [[new_id('l'),new_id('z'),new_id('f')],
             [TestGrounding._get_obj("1","string"),
              TestGrounding._get_obj("4","string"),
              TestGrounding._get_obj("1","string")]]])
        assert (bindings == res)

        ground_specs = gs.ground_spec(spec)
        assert len(ground_specs) == 1
        spec = Spec.get_spec_from_string("SPEC [CI] [l] doSomethingCi(#) |- [CI] [#] otherCi(#)")
        bindings = gs._get_ground_bindings(spec)
        res = TestGrounding.newBinding([
            [[new_id('l')],
             [TestGrounding._get_obj("1","string")]]])
        assert (bindings == res)

        ground_specs = gs.ground_spec(spec)
        assert len(ground_specs) == 1


        ground_specs = gs.ground_spec(spec)
        assert len(ground_specs) == 1
        spec = Spec.get_spec_from_string("SPEC [CB] [l] doSomethingCb() |- [CI] [#] otherCi(l)")
        bindings = gs._get_ground_bindings(spec)
        res = TestGrounding.newBinding([
            [[new_id('l')],
             [TestGrounding._get_obj("1","string")]]])

        assert (bindings == res)

        ground_specs = gs.ground_spec(spec)
        assert len(ground_specs) == 1
