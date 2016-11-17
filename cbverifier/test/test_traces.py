""" Test the traces package.

Test to add:
  - read a callback
  - read a callin
  - read a sequence of callbacks
  - read a nested callback/callin

  - read an unbalanced tree of cb/ci
"""

import logging
import unittest


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import io
from google.protobuf.internal import encoder

import cbverifier.traces.tracemsg_pb2 as tracemsg_pb2
from  cbverifier.traces.tracemsg_pb2 import TraceMsgContainer
from cbverifier.traces.ctrace import CTraceSerializer, MalformedTraceException


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

        ci = cont.msg.callinEntry

        ci.signature = "signature"
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

        ci = cont.msg.callinExit
        ci.signature = "signature"
        ci.method_name = "method_name"
        self._get_value(ci.return_value)

        return cont

    def _get_cb_entry(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLBACK_ENTRY
        cont.msg.message_id = 1
        cont.msg.thread_id = 2

        cb = cont.msg.callbackEntry

        cb.signature = "signature"
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

        return cont

    def _get_cb_exit(self):
        cont = tracemsg_pb2.TraceMsgContainer()

        cont.msg.type = TraceMsgContainer.TraceMsg.CALLBACK_EXIT
        cont.msg.message_id = 1
        cont.msg.thread_id = 2

        cb = cont.msg.callbackExit
        cb.signature = "signature"
        cb.method_name = "method_name"
        self._get_value(cb.return_value)

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

        ci_entry = self._get_ci_entry()
        ci_exit = self._get_ci_exit()

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


