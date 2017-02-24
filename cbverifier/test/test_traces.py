""" Test the traces package.

"""

import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import io
import os
from google.protobuf.internal import encoder


import cbverifier.test.examples
import cbverifier.traces.tracemsg_pb2 as tracemsg_pb2
from  cbverifier.traces.tracemsg_pb2 import TraceMsgContainer
from cbverifier.traces.ctrace import CTraceSerializer, MalformedTraceException, FrameworkOverride, TraceConverter


class TestTraces(unittest.TestCase):

    def _get_value(self, val):
        val.is_null = False
        val.type = "java.lang.Object"
        val.fmwk_type = "java.lang.Object"
        val.object_id = "object_id"
        val.value = "@1234"

        return val

    def _get_ci_entry(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLIN_ENTRY
        cont.msg.message_id = 1
        cont.msg.thread_id = 2
        cont.msg.is_activity_thread = 1

        ci = cont.msg.callinEntry

        ci.class_name = "class_name"
        ci.method_name = "method_name"
        self._get_value(ci.param_list.add())
        self._get_value(ci.param_list.add())
        self._get_value(ci.param_list.add())

        self._get_value(ci.caller)

        return cont

    def _get_ci_exit(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLIN_EXIT
        cont.msg.message_id = 1
        cont.msg.thread_id = 2
        cont.msg.is_activity_thread = 1

        ci = cont.msg.callinExit
        ci.class_name = "class_name"
        ci.method_name = "method_name"
        self._get_value(ci.return_value)

        return cont

    def _get_ci_exception(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLIN_EXEPION
        cont.msg.message_id = 1
        cont.msg.thread_id = 2
        cont.msg.is_activity_thread = 1

        cie = cont.msg.callinException
        cie.throwing_class_name = "class_name"
        cie.throwing_method_name = "method_name"
        cie.type = "type"
        cie.exception_message = "exception message"
        stack_trace1 = cie.stack_trace.add()
        stack_trace1.method = "m1"
        stack_trace1.class_name = "c1"

        return cont

    def _get_cb_entry(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLBACK_ENTRY
        cont.msg.message_id = 1
        cont.msg.thread_id = 2
        cont.msg.is_activity_thread = 1

        cb = cont.msg.callbackEntry

        cb.class_name = "class_name"
        cb.method_name = "method_name"
        self._get_value(cb.param_list.add())
        self._get_value(cb.param_list.add())
        self._get_value(cb.param_list.add())

        cb.callback_caller_class = "cb caller class"
        cb.callback_caller_method = "cb caller method"
        cb.method_parameter_types.append("param 1")
        cb.method_parameter_types.append("param 2")
        cb.method_parameter_types.append("param 3")

        cb.method_returnType = "return type"
        # repeated FrameworkOverride framework_overrides = 9;
        cb.receiver_first_framework_super = "fwk super"

        override = cb.framework_overrides.add()
        override.method = "method_name"
        override.class_name = "first"
        override.is_interface = False

        override = cb.framework_overrides.add()
        override.method = "method_name"
        override.class_name = "second"
        override.is_interface = False

        override = cb.framework_overrides.add()
        override.method = "method_name"
        override.class_name = "interface"
        override.is_interface = True

        return cont

    def _get_cb_exit(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLBACK_EXIT
        cont.msg.message_id = 1
        cont.msg.thread_id = 2
        cont.msg.is_activity_thread = 1

        cb = cont.msg.callbackExit
        cb.class_name = "class_name"
        cb.method_name = "method_name"
        self._get_value(cb.return_value)

        return cont

    def _get_cb_exception(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLBACK_EXCEPTION
        cont.msg.message_id = 1
        cont.msg.thread_id = 2
        cont.msg.is_activity_thread = 1

        cbe = cont.msg.callbackException
        cbe.throwing_class_name = "class_name"
        cbe.throwing_method_name = "method_name"
        cbe.type = "type"
        stack_trace1 = cbe.stack_trace.add()
        stack_trace1.method = "m1"
        stack_trace1.class_name = "c1"

        return cont


    def write_proto(self, buff, msgs):
        out = None
        for msg in msgs:
            serializedMessage = msg.SerializeToString()
            delimiter = encoder._VarintBytes(len(serializedMessage))
            if out is None:
                out = delimiter + serializedMessage
            else:
                out = out + delimiter + serializedMessage

        buff.write(out)

    def write_and_get(self, msgs):
        # write the data
        f = io.BytesIO()
        self.write_proto(f, msgs)

        # read the data
        f.seek(0)
        trace = CTraceSerializer.read_trace(f)
        assert trace is not None
        return trace

    def test_read_cb(self):
        cb_entry = self._get_cb_entry()
        cb_exit = self._get_cb_exit()
        cb_exception = self._get_cb_exception()

        ci_entry = self._get_ci_entry()
        ci_exit = self._get_ci_exit()
        ci_exception = self._get_ci_exception()

        self.write_and_get([cb_entry, ci_entry, ci_exit, cb_exit])

        self.write_and_get([cb_entry,
                            cb_entry,
                            cb_entry,
                            ci_entry,
                            cb_entry,
                            cb_exit,
                            ci_exit,
                            cb_exit,
                            cb_exit,
                            cb_exit])

        with self.assertRaises(MalformedTraceException):
            self.write_and_get([cb_entry,
                                cb_entry,
                                cb_entry,
                                ci_entry,
                                cb_entry,
                                cb_exit,
                                cb_exit,
                                cb_exit,
                                ci_exit,
                                cb_exit])

        with self.assertRaises(MalformedTraceException):
            # missing an exit
            self.write_and_get([cb_entry,
                                cb_entry,
                                cb_entry,
                                ci_entry,
                                cb_entry,
                                cb_exit,
                                cb_exit,
                                ci_exit,
                                cb_exit])

        with self.assertRaises(MalformedTraceException):
            # missing an entry
            self.write_and_get([cb_entry,
                                cb_entry,
                                cb_entry,
                                ci_entry,
                                cb_entry,
                                cb_exit,
                                cb_exit,
                                cb_exit,
                                ci_exit,
                                cb_exit])


        self.write_and_get([cb_entry, ci_entry, ci_exception, cb_exit])


    def test_cb_override(self):
        def eq_override(ctrace_o, msg_o):
            return (ctrace_o.method_name == msg_o.method_name and
                    ctrace_o.class_name == msg_o.class_name and
                    ctrace_o.is_interface == msg_o.is_interface)

        cb_entry = self._get_cb_entry()
        cb_exit = self._get_cb_exit()

        ctrace = self.write_and_get([cb_entry,cb_exit])
        self.assertTrue(1 == len(ctrace.children))

        cb = ctrace.children[0]
        self.assertTrue(3 == len(cb.fmwk_overrides))


        self.assertTrue(eq_override(cb.fmwk_overrides[0],
                                    FrameworkOverride("first",
                                                      "method_name",
                                                      False)))

        self.assertTrue(eq_override(cb.fmwk_overrides[1],
                                    FrameworkOverride("second",
                                                      "method_name",
                                                      False)))

        self.assertTrue(eq_override(cb.fmwk_overrides[2],
                                    FrameworkOverride("interface",
                                                      "method_name",
                                                      True)))

    def test_non_ui_threads(self):
        cb_entry = self._get_cb_entry()
        cb_exit = self._get_cb_exit()
        cb_exception = self._get_cb_exception()
        ci_entry = self._get_ci_entry()
        ci_exit = self._get_ci_exit()
        ci_exception = self._get_ci_exception()

        cb_entry_non_ui = self._get_cb_entry()
        cb_entry_non_ui.msg.is_activity_thread = False
        cb_exit_non_ui = self._get_cb_exit()
        cb_exit_non_ui.msg.is_activity_thread = False
        cb_exception_non_ui = self._get_cb_exception()
        cb_exception_non_ui.msg.is_activity_thread = False
        ci_entry_non_ui = self._get_ci_entry()
        ci_entry_non_ui.msg.is_activity_thread = False
        ci_exit_non_ui = self._get_ci_exit()
        ci_exit_non_ui.msg.is_activity_thread = False
        ci_exception_non_ui = self._get_ci_exception()
        ci_exception_non_ui.msg.is_activity_thread = False

        # ignore the message on the non-ui thread
        read_trace = self.write_and_get([cb_entry,
                                         cb_entry_non_ui,
                                         cb_exit_non_ui,
                                         cb_exit])
        self.assertTrue(1 == read_trace.get_total_msg())

    def test_init_workaround(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)
        t1 = os.path.join(test_path, "trace_init.json")

        trace = CTraceSerializer.read_trace_file_name(t1, True)
        self.assertTrue(trace is not None)
        self.assertTrue(len(trace.children) > 0)
        cb = trace.children[0]
        self.assertTrue(len(cb.fmwk_overrides) == 1)
        self.assertTrue(cb.fmwk_overrides[0].class_name == "android.support.v7.app.AppCompatActivity")


    def test_primitive_conversion_bool(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)
        t1 = os.path.join(test_path, "trace_boolean.json")

        trace = CTraceSerializer.read_trace_file_name(t1, True)
        self.assertTrue(trace is not None)
        self.assertTrue(len(trace.children) > 0)
        cb = trace.children[0]

        self.assertTrue(len(cb.params) == 4)

        pa = cb.params[1]
        self.assertTrue(pa.type == TraceConverter.JAVA_BOOLEAN_PRIMITIVE)
        self.assertTrue(pa.value == TraceConverter.TRUE_CONSTANT)

        pb = cb.params[3]
        self.assertTrue(pb.type == TraceConverter.JAVA_BOOLEAN_PRIMITIVE)
        self.assertTrue(pb.value == TraceConverter.FALSE_CONSTANT)

        self.assertTrue(cb.return_value is not None)
        self.assertTrue(cb.return_value.type == TraceConverter.JAVA_BOOLEAN_PRIMITIVE)
        self.assertTrue(cb.return_value.value == TraceConverter.FALSE_CONSTANT)


    def test_primitive_conversion_int(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)
        t1 = os.path.join(test_path, "trace_int.json")

        trace = CTraceSerializer.read_trace_file_name(t1, True)
        self.assertTrue(trace is not None)
        self.assertTrue(len(trace.children) > 0)
        cb = trace.children[0]

        self.assertTrue(len(cb.params) == 4)

        pa = cb.params[1]
        self.assertTrue(pa.type == TraceConverter.JAVA_INT_PRIMITIVE)
        self.assertTrue(pa.value == "1")

        pb = cb.params[3]
        self.assertTrue(pb.type == TraceConverter.JAVA_INT_PRIMITIVE)
        self.assertTrue(pb.value == "0")

        self.assertTrue(cb.return_value is not None)
        self.assertTrue(cb.return_value.type == TraceConverter.JAVA_INT_PRIMITIVE)
        self.assertTrue(cb.return_value.value == "0")

    def test_truncated(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace_truncated_recoverable")
        trace = CTraceSerializer.read_trace_file_name(t1, False)
        self.assertTrue(len(trace.children) == 3)

        with self.assertRaises(Exception):
            t2 = os.path.join(test_path, "trace_truncated_non_recoverable")
            trace = CTraceSerializer.read_trace_file_name(t2, False)

    def test_missing_return(self):
        test_path = os.path.dirname(cbverifier.test.examples.__file__)

        t1 = os.path.join(test_path, "trace_missing_return.json")
        trace = CTraceSerializer.read_trace_file_name(t1, True)
        self.assertTrue(len(trace.children) == 1)
        cb = trace.children[0]

        self.assertTrue(cb.return_value is not None and
                        cb.return_value.is_null)

        t1 = os.path.join(test_path, "trace_missing_return_void.json")
        trace = CTraceSerializer.read_trace_file_name(t1, True)
        self.assertTrue(len(trace.children) == 1)
        cb = trace.children[0]

        self.assertTrue(cb.return_value is None)

