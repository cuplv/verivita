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

from cbverifier.encoding.grounding import GroundSpecs, Assignments, bottom_value, TraceSpecConverter
from cbverifier.encoding.grounding import AssignmentsSet, TraceMap
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
    def _get_null():
        v = CValue()
        v.is_null = True
        v.type = None
        v.value = None
        return v

    @staticmethod
    def _get_true():
        v = CValue()
        v.is_null = False
        v.type = TraceSpecConverter.JAVA_BOOLEAN
        v.value = "true"
        return v

    @staticmethod
    def _get_false():
        v = CValue()
        v.is_null = False
        v.type = TraceSpecConverter.JAVA_BOOLEAN
        v.value = "false"
        return v


    @staticmethod
    def _get_fmwkov(cname, mname, is_int):
        return FrameworkOverride(cname, mname, is_int)

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

    def _check_val(self, a, variables, values):
        assert len(values) == len(variables)
        for v,l in zip(variables, values):
            self.assertTrue(a.get(v) == l)
        return a

    def test_assignments(self):
        a = TestGrounding.newAssign(['x','y'],[1,2])
        self._check_val(a, ['x','y'],[1,2])

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        # NOTE: [],[] is Top
        a2 = TestGrounding.newAssign([],[])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y'],[1,2])

        a1 = TestGrounding.newAssign(['x','y'],[1,2])
        a2 = TestGrounding.newAssign(['x'],[3])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x','y'],[bottom_value,2])

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

        a1 = TestGrounding.newAssign(['x'],[1])
        a2 = TestGrounding.newAssign(['x'],[bottom_value])
        a3 = a1.intersect(a2)
        a4 = a2.intersect(a1)
        self._check_val(a3, ['x'],[bottom_value])
        self._check_val(a4, ['x'],[bottom_value])

        a1 = TestGrounding.newAssign(['x'],[bottom_value])
        a2 = TestGrounding.newAssign([],[])
        a3 = a1.intersect(a2)
        self._check_val(a3, ['x'],[bottom_value])


    def test_assignments_set(self):
        # test combination of two sets containing two Top assignements
        aset1 = TestGrounding.newBinding([])
        aset2 = TestGrounding.newBinding([])
        aset1 = aset1.combine(aset2)
        assert(aset1.assignments == TestGrounding.newBinding([]).assignments)

        # test combination with empty set
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
            [['x','y'],[1,2]],
            [['x','y'],[bottom_value,2]]])
        assert(aset1 == res)


    def test_trace_map(self):
        trace = CTrace()
        cb1 = CCallback(1, 1, "", "doSomethingCb()",
                        [TestGrounding._get_obj("1","string")],
                        None, [TestGrounding._get_fmwkov("","doSomethingCb()",False)])
        trace.add_msg(cb1)
        ci1 = CCallin(1, 1, "", "doSomethingCi()",
                      [TestGrounding._get_obj("1","string")],
                      None)
        cb1.add_msg(ci1)
        cb2 = CCallback(1, 1, "", "doSomethingCb()",
                        [],
                        None, [TestGrounding._get_fmwkov("","doSomethingCb()",False)])
        trace.add_msg(cb2)
        ci2 = CCallin(1, 1, "", "doSomethingCi(int)",
                      [TestGrounding._get_obj("1","string"),
                       TestGrounding._get_int(2)],
                      None)
        cb1.add_msg(ci2)
        cb3 = CCallback(1, 1, "", "doSomethingCb()",
                        [TestGrounding._get_obj("2","string")],
                        None, [TestGrounding._get_fmwkov("","doSomethingCb()",False)])
        trace.add_msg(cb3)

        cb4 = CCallback(1, 1, "", "doSomethingCb()",
                        [TestGrounding._get_obj("2","string")],
                        TestGrounding._get_obj("3","string"),
                        [TestGrounding._get_fmwkov("","doSomethingCb()",False)])
        trace.add_msg(cb4)

        cb5 = CCallback(1, 1, "package.MyClass", "testClassName()",
                        [TestGrounding._get_obj("2","string")],
                        TestGrounding._get_obj("3","string"),
                        [TestGrounding._get_fmwkov("package.MyClass","testClassName()",False)])
        trace.add_msg(cb5)

        cb6 = CCallback(1, 1, "package.MyClass", "testAssignConstant()",
                        [TestGrounding._get_obj("2","string")],
                        TestGrounding._get_int(3),
                        [TestGrounding._get_fmwkov("package.MyClass","testAssignConstant()",False)])
        trace.add_msg(cb6)

        # Test first framework type
        cb7 = CCallback(1, 1, "package.MyClass", "testClassName()",
                        [TestGrounding._get_obj("2","string")],
                        TestGrounding._get_obj("3","string"),
                        [TestGrounding._get_fmwkov("android.Button",
                                                   "testClassName()", False),
                         TestGrounding._get_fmwkov("android.ButtonInterface",
                                                   "testClassName()", True),
                         TestGrounding._get_fmwkov("android.ButtonInner",
                                                   "testClassName()", False)])
        trace.add_msg(cb7)

        tmap = TraceMap(trace)

        assert (len(tmap.lookup_methods(new_ci(), "other()", 0, False)) == 0)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCb()", 0, False)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCb()", 1, False)) == 2)
        assert (len(tmap.lookup_methods(new_ci(), "doSomethingCi()", 1, False)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCi()", 1, False)) == 0)
        assert (len(tmap.lookup_methods(new_ci(), "doSomethingCi(int)", 2, False)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "doSomethingCb()", 1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(), "package.MyClass.testClassName()",
                                        1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "android.Button.testClassName()",
                                        1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "android.ButtonInner.testClassName()",
                                        1, True)) == 0)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "android.ButtonInterface.testClassName()",
                                        1, True)) == 1)
        assert (len(tmap.lookup_methods(new_cb(),
                                        "package.MyClass.testAssignConstant()",
                                        1, True)) == 1)

        cnode = new_call(new_nil(), new_cb(),
                         new_id("l"), new_id("doSomethingCb"),
                         new_nil())
        res = tmap.lookup_assignments(cnode)

        res_2 = TestGrounding.newBinding([
            [[new_id('l'), cnode],[TestGrounding._get_obj("1","string"), cb1]],
            [[new_id('l'), cnode],[TestGrounding._get_obj("2","string"), cb3]]])
        self.assertTrue(res == res_2)

        cnode = new_call(new_nil(), new_cb(),
                         new_dontcare(),
                         new_id("doSomethingCb"),
                         new_nil())
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([[[cnode],[cb1]],
                                          [[cnode],[cb3]]])
        cnode = new_call(new_nil(), new_ci(),
                 new_dontcare(), new_id("doSomethingCi"),
                 new_param(new_id('z'), new_id("int"), new_nil()))
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([[[new_id('z'), cnode],
                                           [TestGrounding._get_int(2),
                                            ci2]]])
        self.assertTrue(res == res_2)

        cnode = new_call(new_id("z"), new_cb(),
                         new_id("l"), new_id("doSomethingCb"),
                         new_nil())
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([
            [[new_id('z'),new_id('l'), cnode],
             [TestGrounding._get_obj("3","string"),
              TestGrounding._get_obj("2","string"),
              cb4]]])
        self.assertTrue(res == res_2)

        cnode = new_call(new_id("z"), new_cb(),
                         new_id("l"), new_id("package.MyClass.testClassName"),
                         new_nil())
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([
            [[new_id('z'), new_id('l'), cnode],
             [TestGrounding._get_obj("3","string"),
              TestGrounding._get_obj("2","string"),
              cb5]]])
        self.assertTrue(res == res_2)


        cnode = new_call(new_int(3), new_cb(),
                         new_id("l"), new_id("package.MyClass.testAssignConstant"),
                         new_nil())
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([
            [[new_id('l'),
              cnode],
             [TestGrounding._get_obj("2","string"),
              cb6]]])
        assert (res == res_2)

    def test_ground_bindings(self):
        trace = CTrace()
        cb1 = CCallback(1, 1, "", "void doSomethingCb()",
                        [TestGrounding._get_obj("1","string")],
                        None,
                        [TestGrounding._get_fmwkov("",
                                                  "void doSomethingCb()", False)])
        trace.add_msg(cb1)

        ci1 = CCallin(1, 1, "", "void doSomethingCi(string)",
                      [TestGrounding._get_obj("1","string"),
                       TestGrounding._get_obj("2","string")],
                      None)
        cb1.add_msg(ci1)

        ci2 = CCallin(1, 1, "", "void otherCi(string)",
                      [TestGrounding._get_obj("4","string"),
                       TestGrounding._get_obj("1","string")],
                      None)
        cb1.add_msg(ci2)

        ci3 = CCallin(1, 1, "", "void doSomethingCi(string)",
                      [TestGrounding._get_obj("1","string"),
                       TestGrounding._get_obj("4","string")],
                      None)
        cb1.add_msg(ci3)

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC [CI] [l] void doSomethingCi(z : string) |- [CI] [z] void otherCi(f  : string)")
        something_node = get_regexp_node(spec.ast)
        other_node = get_spec_rhs(spec.ast)
        bindings = gs._get_ground_bindings(spec)
        res = TestGrounding.newBinding([
            [[new_id('l'), new_id('z') , new_id('f'),
              something_node,
              other_node],
             [TestGrounding._get_obj("1","string"),
              TestGrounding._get_obj("4","string"),
              TestGrounding._get_obj("1","string"),
              ci3,
              ci2]],
            [[new_id('l'),
              new_id('z'),
              new_id('f'),
              something_node,
              other_node],
             [TestGrounding._get_obj("1","string"),
              bottom_value,
              TestGrounding._get_obj("1","string"),
              ci1,
              ci2]]
        ])
        self.assertTrue(bindings == res)
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(len(ground_specs) == 1)

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC [CI] [l] void doSomethingCi(# : string) |- [CI] [#] void otherCi(# : string)")
        something_node = get_regexp_node(spec.ast)
        other_node = get_spec_rhs(spec.ast)
        bindings = gs._get_ground_bindings(spec)
        res = TestGrounding.newBinding([
            [[new_id('l'),
              something_node, other_node],
             [TestGrounding._get_obj("1","string"),
              ci1, ci2]],
            [[new_id('l'),
             something_node, other_node],
            [TestGrounding._get_obj("1","string"),
             ci3, ci2]]])
        self.assertTrue(bindings == res)
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(len(ground_specs) == 2)

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC [CB] [l] void doSomethingCb() |- [CI] [#] void otherCi(l : string)")
        something_node = get_regexp_node(spec.ast)
        other_node = get_spec_rhs(spec.ast)
        bindings = gs._get_ground_bindings(spec)
        res = TestGrounding.newBinding([
            [[new_id('l'), something_node, other_node],
             [TestGrounding._get_obj("1","string"),cb1, ci2]]])
        self.assertTrue(bindings == res)
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(len(ground_specs) == 1)

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC TRUE |- [CI] [l1] void doSomethingCi(l1 : string)")
        true_node= get_regexp_node(spec.ast)
        something_node = get_spec_rhs(spec.ast)
        bindings = gs._get_ground_bindings(spec)
        res = TestGrounding.newBinding([[[something_node],[bottom_value]]])

        # doSomethingCi will be instantiated to FALSE
        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC [CI] [l1] void doSomethingCi(l1 : string) |- [CI] [z] void otherCi(l : string)")
        bindings = gs._get_ground_bindings(spec)
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(len(ground_specs) == 0)


    def test_method_assignment(self):
        trace = CTrace()

        cb = CCallback(1, 1,
                       "edu.colorado.test",
                       "int inheritedMethod()",
                       [TestGrounding._get_obj("1","android.widget.Button")],
                       None,
                       [TestGrounding._get_fmwkov("android.widget.Button",
                                                  "int inheritedMethod()", False)])
        trace.add_msg(cb)
        tmap = TraceMap(trace)

        cnode = new_call(new_nil(),
                         new_cb(),
                         new_id("l"),
                         new_id("int android.widget.Button.inheritedMethod"),
                         new_nil())
        res = tmap.lookup_assignments(cnode)
        res_2 = TestGrounding.newBinding([
            [[new_id('l'),
              cnode],
             [TestGrounding._get_obj("1","android.widget.Button"),
              cb]]])
        self.assertTrue(res == res_2)

    def test_constants(self):
        trace = CTrace()
        cb = CCallback(1, 1,
                       "edu.colorado.test",
                       "void inheritedMethodMethod(int)",
                       [TestGrounding._get_null(),
                        TestGrounding._get_int(2)],
                       None,
                       [TestGrounding._get_fmwkov("android",
                                                  "void inheritedMethod(int)",
                                                  False)])
        trace.add_msg(cb)

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC ! ([CB] void android.inheritedMethodA(3 : int)) |- [CB] void android.inheritedMethod(2 : int)")
        bindings = gs._get_ground_bindings(spec)
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(len(ground_specs) == 1)


        # add call with 3 as constant
        cb = CCallback(1, 1,
                       "edu.colorado.test",
                       "void inheritedMethodMethod(int)",
                       [TestGrounding._get_null(),
                        TestGrounding._get_int(3)],
                       None,
                       [TestGrounding._get_fmwkov("android",
                                                  "void inheritedMethod(int)",
                                                  False)])
        trace.add_msg(cb)
        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC ! ([CB] void android.inheritedMethodA(3 : int)) |- [CB] void android.inheritedMethod(2 : int)")
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(len(ground_specs) == 1)


    def test_only_methods(self):
        trace = CTrace()
        cb = CCallback(1, 1, "", "void m1()", [TestGrounding._get_null()], None,
                       [TestGrounding._get_fmwkov("", "void m1()", False)])
        ci1 = CCallin(1, 1, "", "void m2()", [TestGrounding._get_null()], None)
        ci2 = CCallin(1, 1, "", "void m2()", [TestGrounding._get_null()], None)
        ci3 = CCallin(1, 1, "", "void m2()", [TestGrounding._get_null()], None)
        cb.add_msg(ci1)
        cb.add_msg(ci2)
        cb.add_msg(ci3)
        trace.add_msg(cb)

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC [CI] void m2() |- [CB] void m1()")
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(3 == len(ground_specs))

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC ! ([CB] void m3()) |- [CB] void m1()")
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(1 == len(ground_specs))
        self.assertTrue(new_true() == get_regexp_node(ground_specs[0].ast))

        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC [CB] void m3() |- [CB] void m1()")
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(0 == len(ground_specs))

    def test_boolean(self):
        trace = CTrace()
        cb = CCallback(1, 1, "", "void m1(%s)" % TraceSpecConverter.JAVA_BOOLEAN,
                       [TestGrounding._get_null(), TestGrounding._get_true()], None,
                       [TestGrounding._get_fmwkov("", "void m1(%s)" % TraceSpecConverter.JAVA_BOOLEAN, False)])
        trace.add_msg(cb)
        cb = CCallback(1, 1, "", "void m2(%s)" % TraceSpecConverter.JAVA_BOOLEAN,
                       [TestGrounding._get_null(), TestGrounding._get_false()], None,
                       [TestGrounding._get_fmwkov("", "void m2(%s)" % TraceSpecConverter.JAVA_BOOLEAN, False)])
        trace.add_msg(cb)
        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC TRUE |- [CB] void m2(FALSE : %s)" % TraceSpecConverter.JAVA_BOOLEAN)
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(1 == len(ground_specs))

    def test_int(self):
        trace = CTrace()
        cb = CCallback(1, 1, "", "void m1(%s)" % TraceSpecConverter.JAVA_INT,
                       [TestGrounding._get_null(), TestGrounding._get_int(2)], None,
                       [TestGrounding._get_fmwkov("", "void m1(%s)" % TraceSpecConverter.JAVA_INT, False)])
        trace.add_msg(cb)
        gs = GroundSpecs(trace)
        spec = Spec.get_spec_from_string("SPEC TRUE |- [CB] void m1(2 : %s)" % TraceSpecConverter.JAVA_INT)
        ground_specs = gs.ground_spec(spec)
        self.assertTrue(1 == len(ground_specs))
