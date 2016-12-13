

from cbverifier.traces.ctrace import CTrace, FrameworkOverride, CCallin, CCallback, CValue, MessageFilter

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cStringIO import StringIO

class TestTracefilter(unittest.TestCase):
    @staticmethod
    def _get_obj(objId, objType):
        v = CValue()
        v.is_null = False
        v.type = objType
        v.value = objId
        return v
    def test_tracefilter(self):
        trace = CTrace()
        cb2 = CCallback(1, 1, "aquaman", "doSomethingCb()",
                        [self._get_obj(2,"mehbar2")],
                        None, [FrameworkOverride("foobarbaz", "somemethodname", True)])
        ci2 = CCallin(1, 1, "batman", "doSomethingCi(int)",
                      [self._get_obj(3,"watbar2")],None)
        cb2.add_msg(ci2)
        trace.add_msg(cb2)
        # def typeFilter(cMessage):
        #     if isinstance(cMessage, CCallin) or isinstance(cMessage, CCallback):
        #         printme = cMessage.return_value != None and cMessage.return_value.type == "mehbar2"
        #         for param in cMessage.params:
        #             param_type = param.type
        #             if param_type == "mehbar2":
        #                 printme = True
        #                 break
        #         return printme
        #     else:
        #         return False
        stringio = StringIO()
        trace.print_trace(stringio, True, MessageFilter.typeFilterFrom("mehbar2"))
        print "-"
        print stringio.getvalue()
        print "-"
        self.assertTrue("aquaman" in stringio.getvalue())
        self.assertFalse("batman" in stringio.getvalue())

