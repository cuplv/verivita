""" Concrete trace data structure and parsing.

A concrete trace is represented as a forest, where each tree has
messages as nodes and leaves.

Assumptions:
  - all the roots must be callbacks.

"""

import logging
import json # for reading the traces from file
import re

import copy

import StringIO

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

from google.protobuf import message

import tracemsg_pb2

class MessageFilter:
    @staticmethod
    def typeFilterFrom(filter):
        def typeFilter(cMessage):
            if isinstance(cMessage, CCallin) or isinstance(cMessage, CCallback):
                printme = cMessage.return_value != None and cMessage.return_value.type == filter
                for param in cMessage.params:
                    param_type = param.type
                    if param_type == filter:
                        printme = True
                        break
                return printme
            else:
                return False
        return typeFilter

class MalformedTraceException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class TraceEndsInErrorException(Exception):
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
                 return_value = None,
                 exception = None):
        self.message_id = message_id
        self.thread_id = thread_id
        self.class_name = class_name
        self.method_name = method_name
        self.params = params
        self.return_value = return_value
        self.exception = exception

        # messages called inside this message
        self.children = []

    def add_msg(self, msg):
        self.children.append(msg)

    def get_receiver(self):
        if len(self.params) > 0:
            return self.params[0]
        else:
            return None

    def get_other_params(self):
        if len(self.params) > 1:
            return self.params[1:]
        else:
            return []

    def __iter__(self):
        return iter(self.children)

    def _print_entry(self, stream, sep, debug_info=False):
        message_sig = self.get_full_msg_name()
        if isinstance(self, CCallback):
            message_type = "CB"
        else:
            message_type = "CI"

        if self.exception is not None:
            exception = "(raises %s: %s)" % (self.exception.exc_type,
                                             self.exception.message)
        else:
            exception = ""

        stream.write("%s[%d] [%s] [ENTRY] %s (" % (sep,
                                                   self.message_id,
                                                   message_type,
                                                   message_sig))
        for i in range(len(self.params)):
            if (i != 0): stream.write(",")
            stream.write("%s" % self.params[i].get_value())
        stream.write(") %s\n" % exception)

        if debug_info:
            if isinstance(self, CCallback):
                stream.write("%sFramework overrides\n" % sep)
                for override in self.fmwk_overrides:
                    stream.write("%s%s\n" % (sep, str(override)))

    def _print_exit(self, stream, sep, debug_info=False):
        message_sig = self.get_full_msg_name()

        if isinstance(self, CCallback):
            message_type = "CB"
        else:
            message_type = "CI"

        if self.exception is not None:
            exception = "(raises %s: %s)" % (self.exception.exc_type,
                                             self.exception.message)
        else:
            exception = ""

        if self.return_value is None:
            rv_string = ""
        else:
            rv_string = "%s = " % self.return_value.get_value()

        stream.write("%s[%d] [%s] [EXIT] %s%s (" % (sep,
                                                    self.message_id,
                                                    message_type,
                                                    rv_string,
                                                    message_sig))
        for i in range(len(self.params)):
            if (i != 0): stream.write(",")
            stream.write("%s" % self.params[i].get_value())
        stream.write(") %s\n" % exception)


    def _print(self, stream, sep, rec=True, debug_info=False, filter = None):
        self._print_entry(stream, sep, debug_info)

        if rec:
            for child in self.children:
                child._print(stream, "  ", rec, debug_info, filter)

        self._print_exit(stream, sep, debug_info)


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

        # can throw a ValueError if names are not well formed
        opening_paren = full_name.index("(")
        closing_paren = full_name.index(")")

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
                                        return_value,
                                        None)
        # list of FrameworkOverride objects
        # Warning: the order matteres.
        self.fmwk_overrides = fmwk_overrides
    def _print(self, stream, sep, rec=True, debug_info=False, filter=None):
        if filter == None:
            super(CCallback, self)._print(stream, sep, rec, debug_info)
        else:
            if(filter(self)):
                super(CCallback, self)._print(stream, sep, rec, debug_info, filter)


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
                                      return_value,
                                      None)
    def _print(self, stream, sep, rec=True, debug_info=False, filter=None):
        if filter is None:
            super(CCallin, self)._print(stream, sep, rec, debug_info)
        else:
            if filter(self):
                super(CCallin, self)._print(stream, sep, rec, debug_info, filter)
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
            # Workaround: just consider ascii characters.
            # See Issue 113
            stripped = ''.join([i if ord(i) < 128 else ' ' for i in value])
#            return value.encode('utf-8').strip()
            return stripped
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
        return (type(self) == type(other) and
                self.is_null == other.is_null and
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

        return "%s %s" % (desc,
                          self.get_full_msg_name())

    def __eq__(self, other):
        return (self.is_interface == other.is_interface and
                self.class_name == other.class_name and
                self.is_interface == other.is_interface)

class CTraceException:
    """ Store the information of the exception """
    def __init__(self, method_name, class_name, exc_type, message):
        self.method_name = method_name
        self.class_name = class_name
        self.exc_type = exc_type
        self.message = message

class CTrace:
    def __init__(self):
        # forest of message trees
        self.children = []
        self.app_info = None
        self.id_to_cb = None

        self.all_values = None
        # Map from values to their first framework type
        # It is not recorded in the trace, so we have to
        # infer it as much as we can from the method calls
        #
        # WARNING: the map is not complete, since it is inferred
        # from the existing method calls in the trace, so we have to
        # be careful when using it!
        self.val2fmwk_type = None

    def print_trace(self, stream, debug_info=False, filter=None):
        """ Print the trace """
        for child in self.children:
            child._print(stream, "", True, debug_info, filter)

    def add_msg(self, msg):
        self.children.append(msg)

    def __iter__(self):
        return iter(self.children)

    def copy(self, remove_exception=False, callback_bound = None):
        """ Copy the trace, eventually removing the top-level
        callbacks that ends in an exception. """
        new_trace = CTrace()
        copy.app_info = copy.deepcopy(self.app_info)

        maximum = len(self.children)
        if callback_bound is not None:
            maximum = int(callback_bound)
        for ichild in xrange(maximum):
            child = self.children[ichild]
            if not (remove_exception and
                    child.exception is not None):
                new_trace.children.append(copy.deepcopy(child))
            else:
                if (logging.getLogger().getEffectiveLevel() >= logging.WARNING):
                    stringio = StringIO()
                    child._print(stringio, "", rec=False, debug_info=False)
                    logging.info("Removing top-level callback" \
                                 ": %s" % stringio.getvalue())
        return new_trace

    def get_total_msg(self):
        msgs = []
        for m in self.children:
            msgs.append(m)

        count = 0
        while 0 < len(msgs):
            msg = msgs.pop()
            count += 1
            for m in msg.children:
                msgs.append(m)

        return count

    def get_tl_cb_from_id(self, message_id):
        if (self.id_to_cb is None):
            self.id_to_cb = {}
            for cb in self.children:
                self.id_to_cb[cb.message_id] = cb

        try:
            return self.id_to_cb[message_id]
        except KeyError:
            return None

    def get_all_trace_values(self):
        if (self.all_values is None):
            self._collect_all_trace_values()

        return self.all_values

    def _get_fmwk_types(self, value):
        if (self.val2fmwk_type is None):
            self._collect_all_trace_values()

        if value in self.val2fmwk_type:
            return self.val2fmwk_type[value]
        else:
            return None

    def _collect_all_trace_values(self):
        """
        Collect all trace values and try to reconstruct
        the information about the first framework types
        """
        self.all_values = set()
        self.val2fmwk_type = {}

        # Fill the self.all_values set
        #
        msg_stack = [trace_msg for trace_msg in self.children]
        while (0 < len(msg_stack)):
            current = msg_stack.pop()

            rec = current.get_receiver()
            if not rec is None:
                self.all_values.add(rec)
                if not rec in self.val2fmwk_type:
                    fmwk_types_set = set()
                    self.val2fmwk_type[rec] = fmwk_types_set
                fmwk_types = self._get_val_fmwk_overrides(current)
                fmwk_types_set.update(fmwk_types)

            for par in current.get_other_params():
                if not par is None:
                    self.all_values.add(par)

            for c in current.children: # visit the rest
                msg_stack.append(c)

    def _get_val_fmwk_overrides(self, trace_msg):
        overrides_set = set()
        if not (isinstance(trace_msg, CCallback)):
            return overrides_set

        for override in trace_msg.fmwk_overrides:
            assert override is not None
            overrides_set.add(override.class_name)

        return overrides_set

    def _is_in_class_names(self, class_names, obj):
        is_in_class_names = ( ((not obj.type is None) and
                               (obj.type in class_names)) |
                              ((not obj.fmwk_type is None) and
                               (obj.fmwk_type in class_names)))
        if is_in_class_names:
            return is_in_class_names

        # use the framework types inferred from the trace
        obj_fmwk_type = self._get_fmwk_types(obj)
        if (not obj_fmwk_type is None):
            return (not class_names.isdisjoint(obj_fmwk_type))

    def _get_class_names(self, class_names, obj):
        new_set = set()
        if (not obj.type is None) and (obj.type in class_names):
            new_set.add(obj.type)
        if (not obj.fmwk_type is None) and (obj.fmwk_type in class_names):
            new_set.add(obj.fmwk_type)
        else:
            # use the framework types inferred from the trace
            obj_fmwk_type = self._get_fmwk_types(obj)
            if (not obj_fmwk_type is None):
                int_set = obj_fmwk_type.intersection(class_names)
                new_set.update(int_set)
        return new_set


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
    def read_trace_file_name(trace_file_name,
                             is_json=False,
                             allow_exception=True):
        if is_json:
            trace_file = open(trace_file_name, "r")
        else:
            trace_file = open(trace_file_name, "rb")

        return CTraceSerializer.read_trace(trace_file,
                                           is_json,
                                           True,
                                           allow_exception)


    @staticmethod
    def read_trace(trace_file,
                   is_json=False,
                   ignore_non_ui_threads=True,
                   allow_exception = True):
        trace = CTrace()

        if is_json:
            reader = CTraceJsonReader(trace_file)
        else:
            reader = CTraceDelimitedReader(trace_file)

        try:
            CTraceSerializer.read_trace_inner(trace,reader,
                                              ignore_non_ui_threads,
                                              allow_exception)
        except message.DecodeError as e:
            if len(trace.children) > 0:
                # The trace is truncated, but we still read some data
                logging.warning("Protobuf is truncated... parsing terminated.")
            else:
                # This is a non-recoverable error that must be propagated
                raise
        except cbverifier.traces.ctrace.MalformedTraceException as e:
            if len(trace.children) > 0:
                logging.warning("Last callback truncated")
            else:
                raise

        return trace

    @staticmethod
    def read_trace_inner(trace,
                         reader,
                         ignore_non_ui_threads=True,
                         allow_exception = True):
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
            elif ignore_non_ui_threads and (not CTraceSerializer.is_on_ui_thread(recorded_message)):
                logging.debug("Ignoring message executed on a non-UI thread...")
                if (logging.getLogger().getEffectiveLevel() >= logging.WARNING):
                    logging.debug("Ignored message:\n%s\n" % str(recorded_message))
            elif CTraceSerializer.is_entry_message(recorded_message):
                # create the trace message
                trace_message = CTraceSerializer.create_trace_message(recorded_message)
                message_stack.append(trace_message)
            else:
                assert (CTraceSerializer.is_exit_message(recorded_message) or
                        CTraceSerializer.is_exception_message(recorded_message))
                # remove the message from the stack
                trace_message = message_stack.pop()

                # update trace_message with recorded_message
                if (CTraceSerializer.is_exit_message(recorded_message)):
                    CTraceSerializer.update_trace_message(trace_message,
                                                          recorded_message)
                else:
                    assert (CTraceSerializer.is_exception_message(recorded_message))

                    if (not allow_exception and len(message_stack) == 0):
                        raise TraceEndsInErrorException("The trace raises an " \
                                                        "exception inside a callback! "\
                                                        "(the trace already reaches an error)")

                    CTraceSerializer.update_trace_message(trace_message,
                                                          recorded_message)

                if (len(message_stack) == 0):
                    assert (isinstance(trace_message, CCallback))
                    trace.add_msg(trace_message)
                else:
                    last_message = message_stack[len(message_stack)-1]

                    last_message.add_msg(trace_message)

        if len(message_stack) != 0:
            raise MalformedTraceException("The number of entry messages does " \
                                          "match the number of exit/exception " \
                                          "messages.")


    @staticmethod
    def is_app_message(msg):
        return TraceMsgContainer.TraceMsg.APP == msg.type

    @staticmethod
    def is_on_ui_thread(msg):
        return msg.is_activity_thread

    @staticmethod
    def is_entry_message(msg):
        return (TraceMsgContainer.TraceMsg.CALLIN_ENTRY == msg.type or
                TraceMsgContainer.TraceMsg.CALLBACK_ENTRY == msg.type)

    @staticmethod
    def is_exit_message(msg):
        return (TraceMsgContainer.TraceMsg.CALLIN_EXIT == msg.type or
                TraceMsgContainer.TraceMsg.CALLBACK_EXIT == msg.type)

    @staticmethod
    def is_exception_message(msg):
        return (TraceMsgContainer.TraceMsg.CALLIN_EXEPION == msg.type or
                TraceMsgContainer.TraceMsg.CALLBACK_EXCEPTION == msg.type)


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

            (ret_type, param_types) = CTraceSerializer.get_method_types(trace_msg.method_name)
            trace_msg.params = CTraceSerializer.get_params(ci.param_list, param_types)
            trace_msg.return_value = None

        elif (TraceMsgContainer.TraceMsg.CALLBACK_ENTRY == msg.type):
            trace_msg = CCallback()
            cb = msg.callbackEntry

            trace_msg.message_id = msg.message_id
            trace_msg.thread_id = msg.thread_id
            trace_msg.class_name = cb.class_name
            trace_msg.method_name = cb.method_name

            (ret_type, param_types) = CTraceSerializer.get_method_types(trace_msg.method_name)
            trace_msg.params = CTraceSerializer.get_params(cb.param_list, param_types)
            trace_msg.return_value = None

            overrides = []

            # Issue 107 (link to 103)
            # Workaround for trace runner bug 17
            if ("<init>" in trace_msg.method_name):
                trace_override = FrameworkOverride(cb.receiver_first_framework_super,
                                                   cb.method_name,
                                                   False)
                overrides.append(trace_override)

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

        def check_malformed_trace_exception(trace_msg, msg_exit, expected_class, expected_name):
            if (not isinstance(trace_msg, expected_class)):
                raise MalformedTraceException("Found %s for method %s, " \
                                              "while the last message in the stack " \
                                              "is of type %s\n" % (expected_name,
                                                                   msg_exit.throwing_method_name,
                                                                   str(type(trace_msg))))
            elif (not trace_msg.class_name == msg_exit.throwing_class_name):
                raise MalformedTraceException("Found exit for class name \"%s\", " \
                                              "while expecting it for class name " \
                                              "\"%s\"\n" % (msg_exit.throwing_class_name,
                                                            trace_msg.class_name))

            # TEMPORARY HACK: disable the check on callback names
            elif (TraceMsgContainer.TraceMsg.CALLIN_EXEPION == msg.type and not trace_msg.method_name == msg_exit.throwing_method_name):
                raise MalformedTraceException("Found exit for method %s, " \
                                              "while expecting it for method " \
                                              "%s\n" % (trace_msg.method_name,
                                                        msg_exit.throwing_method_name))

        def check_malformed_trace_msg(trace_msg, msg):
            if (trace_msg.thread_id != msg.thread_id):
                raise MalformedTraceException("Found thread id %d for " \
                                              "while the last message in the stack " \
                                              "has thread id %d\n" % (msg.thread_id,
                                                                      trace_msg.thread_id))


        def read_exception(trace_msg, msg):
            trace_msg.exception = CTraceException(msg.throwing_method_name,
                                                  msg.throwing_class_name,
                                                  msg.type,
                                                  msg.exception_message)


        assert (CTraceSerializer.is_exit_message(msg) or
                CTraceSerializer.is_exception_message(msg))

        check_malformed_trace_msg(trace_msg, msg)
        if (TraceMsgContainer.TraceMsg.CALLIN_EXIT == msg.type):
            callinExit = msg.callinExit
            check_malformed_trace(trace_msg, callinExit, CCallin, "CALLIN_EXIT")
            if (callinExit.HasField("return_value")):

                (ret_type, param_types) = CTraceSerializer.get_method_types(trace_msg.method_name)
                trace_msg.return_value = CTraceSerializer.read_value_msg(callinExit.return_value, ret_type)
        elif (TraceMsgContainer.TraceMsg.CALLBACK_EXIT == msg.type):
            callbackExit = msg.callbackExit
            check_malformed_trace(trace_msg, callbackExit, CCallback, "CALLBACK_EXIT")
            if (callbackExit.HasField("return_value")):
                (ret_type, param_types) = CTraceSerializer.get_method_types(trace_msg.method_name)
                trace_msg.return_value = CTraceSerializer.read_value_msg(callbackExit.return_value, ret_type)
            else:
                # HACK FOR ISSUE # OF TRACERUNNER
                # Tracerunner does not record the return value of a callback if it is NULL.
                # We can infer this from the fact that:
                #   - The CALLBACK ENTRY has a non-void return type
                #   - There is no return value in the CALLBACK EXIT message
                #
                (ret_type, param_types) = CTraceSerializer.get_method_types(trace_msg.method_name)
                if (ret_type != "void"):
                    v = CValue()
                    v.is_null = True
                    v.type = ret_type
                    v.value = None
                    trace_msg.return_value = v

        elif (TraceMsgContainer.TraceMsg.CALLIN_EXEPION  == msg.type):
            # check_malformed_trace_exception(trace_msg, msg.callinException, CCallin, "CALLIN_EXCEPTION")
            read_exception(trace_msg, msg.callinException)
        elif (TraceMsgContainer.TraceMsg.CALLBACK_EXCEPTION  == msg.type):
            # check_malformed_trace_exception(trace_msg, msg.callbackException, CCallback, "CALLBACK_EXCEPTION")
            read_exception(trace_msg, msg.callbackException)
        else:
            err = "%s msg type cannot be used to update a node" % msg.type
            raise MalformedTraceException(err)


    @staticmethod
    def get_params(param_list, types_list = None):
        new_param_list = []

        # -1: ignore the receiver, that is not in the types types
        # If this assertion fails, the trace is probably malformed.
        # TODO: raise the exception
        assert types_list is None or len(types_list) == len(param_list) - 1
        if types_list is not None:
            types_list.reverse()
            types_list.append(None) # receiver

        for param in param_list:
            if (types_list is not None):
                param_type = types_list.pop()
            else:
                param_type = None

            param_value = CTraceSerializer.read_value_msg(param, param_type)
            new_param_list.append(param_value)
        return new_param_list

    @staticmethod
    def read_value_msg(value_msg, value_type = None):
        value = CValue(value_msg)

        if (value_type is not None):
            value = TraceConverter.convert_traceval(value, value_type)

        return value


    pattern = re.compile("([\w\.]+) ([\w\.]+)\(([^\)]*)", flags=0)
    @staticmethod
    def get_method_types(method_name):
        ret_type = None
        param_types = None

        res = CTraceSerializer.pattern.match(method_name)

        if res is not None:
            groups = res.groups()
            if (3 == len(groups)):
                ret_type = groups[0]

                if (len(groups[2]) > 0):
                    types_string = groups[2].split(",")
                    param_types = []
                    for p_type in types_string:
                        p_type = p_type.strip()
                        param_types.append(p_type)

        return (ret_type, param_types)


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
        self.list_position = 0
        self.pbufs = []
        class ReadIter:
            def __init__(self,v):
                self.v = v
            def __iter__(self):
                return self
            def next(self):
                return self.v.inext()
        ri = ReadIter(self)

        for msg in ri:
            self.pbufs.append(msg)

        sortpbufs = sorted(self.pbufs, key=lambda m : m.msg.message_id)
        self.pbufs = sortpbufs

    def next(self):
        list_position = self.list_position
        self.list_position += 1
        if list_position < len(self.pbufs):
            return self.pbufs[list_position]
        else:
            raise StopIteration()


    def __iter__(self):
        return self

    def inext(self):
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
        try:
            trace_msg_container.ParseFromString(raw_data)
            pass
        except message.DecodeError as e:
            trace_msg_container == None
            raise

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


class TraceConverter:
    JAVA_INT_PRIMITIVE = "int"
    JAVA_INT = "java.lang.Integer"
    JAVA_FLOAT_PRIMITIVE = "float"
    JAVA_FLOAT = "java.lang.Float"
    JAVA_BOOLEAN_PRIMITIVE = "boolean"
    JAVA_BOOLEAN = "java.lang.Boolean"
    JAVA_STRING = "java.lang.String"

    TRUE_CONSTANT = "true"
    FALSE_CONSTANT = "false"

    @staticmethod
    def convert_traceval(trace_val, declared_type):
        """ Convert the value found in the trace depending
        on its decalred type.

        For example, in the trace we may have an integer type parameter
        with value 0 that is recorded instead of a boolean
        value false.

        The function also change the type of the parameter to its
        declared type.
        """
        assert isinstance(trace_val, CValue)

        # null
        if trace_val.is_null is not None and trace_val.is_null:
            trace_val.type = declared_type

        # Boolean case
        elif (declared_type == TraceConverter.JAVA_BOOLEAN_PRIMITIVE or
              declared_type ==  TraceConverter.JAVA_BOOLEAN):
            if trace_val.value is None:
                raise Exception("Found None value for a primitive type!" \
                                "The trace should contain a value in this " \
                                "case.")
            str_val = str(trace_val.value).strip()

            if (str_val == "0"):
                trace_val.value = TraceConverter.FALSE_CONSTANT
            elif (str_val == "1"):
                trace_val.value = TraceConverter.TRUE_CONSTANT
            # A Boolean must be either TRUE or FALSE
            assert (trace_val.value != TraceConverter.TRUE_CONSTANT or
                    trace_val.value != TraceConverter.FALSE_CONSTANT)
            trace_val.type = declared_type

        # Integer case
        elif (declared_type == TraceConverter.JAVA_INT_PRIMITIVE or
              declared_type ==  TraceConverter.JAVA_INT):
            if trace_val.value is None:
                raise Exception("Found None value for a primitive type!" \
                                "The trace should contain a value in this " \
                                "case.")
            try:
                int_val = int(trace_val.value)
                trace_val.value = str(int_val)
            except ValueError as e:
                raise Exception("Wrong integer value in message!")
            trace_val.type = declared_type

        # Float case
        elif (declared_type == TraceConverter.JAVA_FLOAT_PRIMITIVE or
              declared_type ==  TraceConverter.JAVA_FLOAT):
            if trace_val.value is None:
                raise Exception("Found None value for a primitive type!" \
                                "The trace should contain a value in this " \
                                "case.")
            try:
                # A bit brittle...
                int_val = float(trace_val.value)
                trace_val.value = float(int_val)
            except ValueError as e:
                raise Exception("Wrong float value in message!")
            trace_val.type = declared_type

        # String
        elif declared_type == TraceConverter.JAVA_STRING:
            if trace_val.value is None:
                raise Exception("Found None value for a primitive type!" \
                                "The trace should contain a value in this " \
                                "case.")
            trace_val.type = declared_type

        return trace_val

