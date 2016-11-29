""" Concrete trace data structure and parsing.

A concrete trace is represented as a forest, where each tree has
messages as nodes and leaves.

Assumptions:
  - all the roots must be callbacks.

"""

import logging
import json # for reading the traces from file
import re


import cbverifier.traces.tracemsg_pb2
from  cbverifier.traces.tracemsg_pb2 import TraceMsgContainer

try:
    from google.protobuf.json_format import MessageToJson, Parse
except ImportError as e:
    import sys
    sys.stderr.write("We require at least protobuf version 3.0")
    raise e

# Read a message from Java's writeDelimitedTo:
import google.protobuf.internal.decoder as decoder

import tracemsg_pb2

class MalformedTraceException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class CMessage(object):
    """ Base class that represents a concrete message.
    """

    def __init__(self,
                 message_id = -1,
                 thread_id = None,
                 class_name = None,
                 method_name = None,
                 params = [],
                 return_value = None):
        self.message_id = message_id
        self.thread_id = thread_id
        self.class_name = class_name
        self.method_name = method_name
        self.params = params
        self.return_value = return_value

        # messages called inside this message
        self.children = []

    def add_msg(self, msg):
        self.children.append(msg)

    def __iter__(self):
        return iter(self.children)

    def _print(self, stream, sep, rec=True):
        message_sig = self.get_full_msg_name()

        if isinstance(self, CCallback):
            message_type = "CB"
        else:
            message_type = "CI"

        stream.write("%s[%d] [%s] %s (" % (sep, self.message_id,
                                           message_type,
                                           message_sig))

        for i in range(len(self.params)):
            if (i != 0): stream.write(",")
            stream.write("%s" % self.params[i])
        stream.write(")\n")

        if rec:
            for child in self.children:
                child._print(stream, "  ")

    @staticmethod
    def get_full_msg_name_static(class_name, method_name):
        ret_type = None

        # get the first word
        split_name_by_space = method_name.strip().split(" ")
        if (len(split_name_by_space) == 1):
            ret_type = None
        else:
            ret_type = split_name_by_space[0]
            method_name = " ".join(split_name_by_space[1:])

        res = ""
        if (ret_type != None):
            res += "%s " % ret_type
        if class_name is None or class_name == "":
            res += method_name
        else:
            res += "%s.%s" % (class_name, method_name)
        return res

    def get_full_msg_name(self):
        res = CMessage.get_full_msg_name_static(self.class_name,
                                                self.method_name)
        return res

    def get_msg_no_params(self):
        """ Returns the full name of the message
        without the list of parameters
        """
        full_name = self.get_full_msg_name()

        try:
            opening_paren = full_name.index("(")
            closing_paren = full_name.index(")")
        except ValueError:
            return None

        msg_no_params = full_name[0:opening_paren]

        return msg_no_params


class CCallback(CMessage):
    """ Represents a callback message
    """
    def __init__(self,
                 message_id = -1,
                 thread_id = None,
                 class_name = None,
                 method_name = None,
                 params = [],
                 return_value = None,
                 fmwk_overrides = []):

        super(CCallback, self).__init__(message_id,
                                        thread_id,
                                        class_name,
                                        method_name,
                                        params,
                                        return_value)
        # list of FrameworkOverride objects
        # Warning: the order matteres.
        self.fmwk_overrides = fmwk_overrides


class CCallin(CMessage):
    """ Represents a callin message
    """
    def __init__(self,
                 message_id = -1,
                 thread_id = None,
                 class_name = None,
                 method_name = None,
                 params = [],
                 return_value = None):
        super(CCallin, self).__init__(message_id,
                                      thread_id,
                                      class_name,
                                      method_name,
                                      params,
                                      return_value)

class AppInfo(object):
    """ Info of the app."""
    def __init__(self, app_name):
        self.app_name = app_name


class CValue(object):
    """ Represent the concrete value of an object recorded in a
    concrete trace
    """
    def __init__(self, value_msg=None):
        self._hash = None
        if value_msg is not None:
            # True if it is null
            if value_msg.HasField("is_null"):
                self.is_null = value_msg.is_null
            else:
                self.is_null = None

            if value_msg.HasField("type"):
                self.type = value_msg.type
            else:
                self.type = None

            if value_msg.HasField("fmwk_type"):
                self.fmwk_type = value_msg.fmwk_type
            else:
                self.fmwk_type = None

            if value_msg.HasField("object_id"):
                self.object_id = value_msg.object_id
            else:
                self.object_id = None

            if value_msg.HasField("value"):
                self.value = value_msg.value
            else:
                self.value = None
        else:
            # True if it is null
            self.is_null = True
            # name of the type of the paramter
            self.type = "java.lang.Object"
            # name of the first framework type of the parameter
            self.fmwk_type = None
            # Id of the object
            self.object_id = None
            # Value of the object
            self.value = None

        # at least one must be set
        assert (not ((self.is_null is None or not self.is_null) and
                     self.value is None and
                     self.object_id is None))


    @staticmethod
    def enc(value):
        if isinstance(value, str):
            return value
        elif isinstance(value, unicode):
            return value.encode('utf-8').strip()
        else:
            return str(value)


    def __repr__(self):
        #repr = ""
        val = self.get_value()
        str_repr = "value = %s" % val
        return str_repr

    def get_value(self):
        if self.is_null is not None and self.is_null:
            return "NULL"
        elif self.value is not None:
            return CValue.enc(self.value)
        elif self.object_id is not None:
            return CValue.enc(self.object_id)
        else:
            raise Exception("CValue from trace is empty!")

    def __hash__(self):
        # provide a hash to the object
        # This allow us to use it in a set
        if self._hash is None:
            self._hash = 0

            self._hash ^= hash(self.is_null)
            self._hash ^= hash(self.type)
            self._hash ^= hash(self.fmwk_type)
            self._hash ^= hash(self.object_id)
            self._hash ^= hash(self.value)

        return self._hash

    def __eq__(self, other):
        return (self.is_null == other.is_null and
                self.type == other.type and
                self.fmwk_type == other.fmwk_type and
                self.object_id == other.object_id and
                self.value == other.value)


class FrameworkOverride:
    """ Represents a class or interface in the framework that
    implements or defines a specific method."""
    def __init__(self, class_name, method_name, is_interface):
        self.class_name = class_name
        self.method_name = method_name
        self.is_interface = is_interface

    def get_full_msg_name(self):
        res = CMessage.get_full_msg_name_static(self.class_name,
                                                self.method_name)
        return res

    def __repr__(self):
        if self.is_interface:
            desc = "interface"
        else:
            desc = "class"

        return "%s %s.%s" % (desc,
                             self.get_full_msg_name())

    def __eq__(self, other):
        return (self.is_interface == other.is_interface and
                self.class_name == other.class_name and
                self.is_interface == other.is_interface)

class CTrace:
    def __init__(self):
        # forest of message trees
        self.children = []
        self.app_info = None

    def print_trace(self, stream):
        """ Print the trace """
        for child in self.children:
            child._print(stream, "")

    def add_msg(self, msg):
        self.children.append(msg)

    def __iter__(self):
        return iter(self.children)

class CTraceSerializer:
    """
    Utility functions used to create a trace that can be used by the
    verifier from a trace recorded by trace runner.


    Usage:
    trace = CTraceSerializer.read_trace(<trace_file))

    Exception types are not handled now (they should not be produced
    by TraceRunner.
    """

    @staticmethod
    def read_trace_file_name(trace_file_name, is_json=False):
        if is_json:
            trace_file = open(trace_file_name, "r")
        else:
            trace_file = open(trace_file_name, "rb")

        return CTraceSerializer.read_trace(trace_file, is_json)


    @staticmethod
    def read_trace(trace_file, is_json=False):
        trace = CTrace()

        if is_json:
            reader = CTraceJsonReader(trace_file)
        else:
            reader = CTraceDelimitedReader(trace_file)

        message_stack = []
        for tm_container in reader:
            assert None != tm_container

            recorded_message = tm_container.msg

            if CTraceSerializer.is_app_message(recorded_message):
                # DO NOTHING for now
                # TODO: the APP type of message is NOT used as the
                # other types in the protobuf.
                # To be clarified with Shawn
                trace.app_info = trace.app_info
            if CTraceSerializer.is_entry_message(recorded_message):
                # create the trace message
                trace_message = CTraceSerializer.create_trace_message(recorded_message)
                message_stack.append(trace_message)
            else:
                assert CTraceSerializer.is_exit_message(recorded_message)
                # remove the message from the stack
                trace_message = message_stack.pop()

                # Check the class_name to be the same as the recorded message

                # update trace_message with recorded_message
                CTraceSerializer.update_trace_message(trace_message, recorded_message)

                if (len(message_stack) == 0):
                    assert (isinstance(trace_message, CCallback))
                    trace.add_msg(trace_message)
                else:
                    last_message = message_stack[len(message_stack)-1]

                    last_message.add_msg(trace_message)

        assert len(message_stack) == 0
        return trace


    @staticmethod
    def is_app_message(msg):
        return TraceMsgContainer.TraceMsg.APP == msg.type

    @staticmethod
    def is_entry_message(msg):
        return (TraceMsgContainer.TraceMsg.CALLIN_ENTRY == msg.type or
                TraceMsgContainer.TraceMsg.CALLBACK_ENTRY == msg.type)

    @staticmethod
    def is_exit_message(msg):
        return (TraceMsgContainer.TraceMsg.CALLIN_EXIT == msg.type or
                TraceMsgContainer.TraceMsg.CALLBACK_EXIT == msg.type)

    @staticmethod
    def create_trace_message(msg):
        assert CTraceSerializer.is_entry_message(msg)

        trace_msg = None

        if (TraceMsgContainer.TraceMsg.CALLIN_ENTRY == msg.type):
            trace_msg = CCallin()
            ci = msg.callinEntry

            trace_msg.message_id = msg.message_id
            trace_msg.thread_id = msg.thread_id
            trace_msg.class_name = ci.class_name
            trace_msg.method_name = ci.method_name
            trace_msg.params = CTraceSerializer.get_params(ci.param_list)
            trace_msg.return_value = None
        elif (TraceMsgContainer.TraceMsg.CALLBACK_ENTRY == msg.type):
            trace_msg = CCallback()
            cb = msg.callbackEntry

            trace_msg.message_id = msg.message_id
            trace_msg.thread_id = msg.thread_id
            trace_msg.class_name = cb.class_name
            trace_msg.method_name = cb.method_name
            trace_msg.params = CTraceSerializer.get_params(cb.param_list)
            trace_msg.return_value = None

            # TODO: handle the overrides
            # for overrides in cb.framework_overrides:
            #     trace_msg.overrides.append(None)
            # trace_msg.receiver_first_framework_super =
            # cb.receiver_first_framework_super
            overrides = []
            for override in cb.framework_overrides:
                trace_override = FrameworkOverride(override.class_name,
                                                   override.method,
                                                   override.is_interface)
                overrides.append(trace_override)
            trace_msg.fmwk_overrides = overrides

        else:
            err = "%s msg type cannot be used to create a node" % msg.type
            raise MalformedTraceException(err)

        return trace_msg


    @staticmethod
    def update_trace_message(trace_msg, msg):
        """ Update trace_msg with the exit message msg.

        The function assumes that msg is either a callin exit or a
        callback exit.

        The function assumes that msg is the exit message for
        trace_msg (an assertion fails if the name and class_name of
        trace_msg and msg do not match
        """


        def check_malformed_trace(trace_msg, msg_exit, expected_class, expected_name):
            if (not isinstance(trace_msg, expected_class)):
                raise MalformedTraceException("Found %s for method %s, " \
                                              "while the last message in the stack " \
                                              "is of type %s\n" % (expected_name,
                                                                   msg_exit.method_name,
                                                                   str(type(trace_msg))))
            elif (not trace_msg.class_name == msg_exit.class_name):
                raise MalformedTraceException("Found exit for class name \"%s\", " \
                                              "while expecting it for class name " \
                                              "\"%s\"\n" % (msg_exit.class_name,
                                                            trace_msg.class_name))

            # TEMPORARY HACK: disable the check on callback names
            elif (TraceMsgContainer.TraceMsg.CALLIN_EXIT == msg.type and not trace_msg.method_name == msg_exit.method_name):
                raise MalformedTraceException("Found exit for method %s, " \
                                              "while expecting it for method " \
                                              "%s\n" % (trace_msg.method_name,
                                                        msg_exit.method_name))

        def check_malformed_trace_msg(trace_msg, msg):
            if (trace_msg.thread_id != msg.thread_id):
                raise MalformedTraceException("Found thread id %d for " \
                                              "while the last message in the stack " \
                                              "has thread id %d\n" % (msg.thread_id,
                                                                      trace_msg.thread_id))


        assert CTraceSerializer.is_exit_message(msg)

        check_malformed_trace_msg(trace_msg, msg)
        if (TraceMsgContainer.TraceMsg.CALLIN_EXIT == msg.type):
            callin_exit = msg.callinExit

            check_malformed_trace(trace_msg, callin_exit, CCallin,
                                  "CALLIN_EXIT")

            if (callin_exit.HasField("return_value")):
                trace_msg.return_value = CTraceSerializer.read_value_msg(callin_exit.return_value)
        elif (TraceMsgContainer.TraceMsg.CALLBACK_EXIT == msg.type):
            callback_exit = msg.callbackExit

            check_malformed_trace(trace_msg, callback_exit, CCallback,
                                  "CALLBACK_EXIT")

            if (callback_exit.HasField("return_value")):
                trace_msg.return_value = CTraceSerializer.read_value_msg(callback_exit.return_value)
        else:
            err = "%s msg type cannot be used to update a node" % msg.type
            raise MalformedTraceException(err)


    @staticmethod
    def get_params(param_list):
        new_param_list = []
        for param in param_list:
            new_param_list.append(CTraceSerializer.read_value_msg(param))
        return new_param_list

    @staticmethod
    def read_value_msg(value_msg):
        value = CValue(value_msg)
        return value


class CTraceDelimitedReader(object):
    """
    Read a delimited stream containing trace messages.

    We have to do the hard work, since this does not seem supported
    for python ina clean way:

    https://github.com/google/protobuf/issues/54

    https://groups.google.com/forum/#!topic/protobuf/zjWySHr1L04
    parseDelimitedTo(),


    USAGE:
    ifile = open(protofile, "rb")
    reader = CTraceDelimitedReader(ifile)
    for m in reader:
      m is the message

    """
    def __init__(self,trace_file):
        # ISSUE: read all the data at once
        # limited by _DecodeVarint implementation
        self.data = trace_file.read()
        self.size = len(self.data)
        self.position = 0

    def __iter__(self):
        return self

    def next(self):
        """ Read a single trace msg container object from the input
        file.

        The input file is a fixed-size (?!) file, where each
        fixed-sized message
        """

        if (self.position >= self.size):
            raise StopIteration()

        (size, self.position) = decoder._DecodeVarint(self.data, self.position)

        raw_data = self.data[self.position:self.position + size]
        self.position = self.position + size

        trace_msg_container = tracemsg_pb2.TraceMsgContainer()
        trace_msg_container.ParseFromString(raw_data)

        if trace_msg_container == None:
            raise StopIteration()
        else:
            return trace_msg_container

class CTraceJsonReader(object):
    """
    Read the trace from a json file

    USAGE:
    ifile = open(protofile, "r")
    reader = CTraceJsonReader(ifile)
    for m in reader:
      m is the message

    """
    def __init__(self,trace_file):
        self.data = json.load(trace_file)
        self.position = 0

    def __iter__(self):
        return self

    def next(self):
        if (self.position >= len(self.data)):
            raise StopIteration()

        trace_msg_container = tracemsg_pb2.TraceMsgContainer()

        json_str = json.dumps(self.data[self.position])
        trace_msg_container = Parse(json_str, trace_msg_container)
        self.position = self.position + 1

        return trace_msg_container



class TraceProtoUtils:

    @staticmethod
    def protoToJson(protofile, jsonfile):
        with open(protofile, 'rb') as protof:
            json_msgs = []
            reader = CTraceDelimitedReader(protof)
            for tm_container in reader:
                assert None != tm_container
                json_msgs.append(MessageToJson(tm_container, False))
            protof.close()

        with open(jsonfile, 'w') as jsonf:
            json.dump(json_msgs, jsonf)
            jsonf.flush()
            jsonf.close()

