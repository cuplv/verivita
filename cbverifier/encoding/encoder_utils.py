import string
from pysmt.shortcuts import Symbol
from pysmt.typing import BOOL
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback
from cbverifier.encoding.conversion import TraceSpecConverter

def _substitute(template, substitution):
    return string.Template(template).safe_substitute(substitution)

class EncoderUtils:
    ENTRY = "ENTRY"
    EXIT = "EXIT"

    @staticmethod
    def _get_pc_name():
        atom_name = "pc"
        return atom_name

    @staticmethod
    def _get_state_var(key):
        atom_name = "enabled_" + key
        return Symbol(atom_name, BOOL)

    @staticmethod
    def get_key(retval, call_type, entry_type, method_name, params):
        assert method_name is not None
        assert params is not None
        assert method_name != ""

        assert call_type == "CI" or call_type == "CB"
        assert entry_type == EncoderUtils.ENTRY or entry_type == EncoderUtils.EXIT

        string_params = [str(f) for f in params]

        if (retval != None and entry_type == EncoderUtils.EXIT):
            # ADD return value only for EXIT
            key = "%s=[%s]_[%s]_%s(%s)" % (retval,
                                           call_type,
                                           entry_type,
                                           method_name,
                                           ",".join(string_params))
        else:
            key = "[%s]_[%s]_%s(%s)" % (call_type ,
                                        entry_type,
                                        method_name,
                                        ",".join(string_params))
        return key

    @staticmethod
    def get_key_from_msg(msg, entry_type):
        """ The input is a msg from a concrete trace.
        The output is the key to the message

        The message must also be paired with the entry/exit information.
        """

        if isinstance(msg, CCallin):
            msg_type = "CI"
        elif isinstance(msg, CCallback):
            msg_type = "CB"
        else:
            assert False

        if (msg.return_value is None):
            retval = None
        else:
            retval = EncoderUtils.get_value_key(msg.return_value)

        params = []
        for p in msg.params:
            p_value = EncoderUtils.get_value_key(p)
            params.append(p_value)

        full_msg_name = msg.get_full_msg_name()
        return EncoderUtils.get_key(retval, msg_type, entry_type, full_msg_name, params)

    @staticmethod
    def get_key_from_call(call_node):
        """ Works for grounded call node """
        assert (get_node_type(call_node) == CALL_ENTRY or
                get_node_type(call_node) == CALL_EXIT)

        if (get_node_type(call_node) == CALL_EXIT):
            node_retval = get_call_assignee(call_node)
            if (new_nil() != node_retval):
                retval_val = TraceSpecConverter.specnode2traceval(node_retval)
                retval = EncoderUtils.get_value_key(retval_val)
            else:
                retval = None
        else:
            retval = None

        node_call_type = get_call_type(call_node)
        if (get_node_type(node_call_type) == CI):
            call_type = "CI"
        elif (get_node_type(node_call_type) == CB):
            call_type = "CB"
        else:
            assert False

        entry_type = EncoderUtils.ENTRY if get_node_type(call_node) == CALL_ENTRY else EncoderUtils.EXIT

        method_name_node = get_call_signature(call_node)

        assert (ID == get_node_type(method_name_node))
        method_name = get_id_val(method_name_node)
        receiver = get_call_receiver(call_node)

        if (new_nil() != receiver):
            param_val = TraceSpecConverter.specnode2traceval(receiver)
            params = [EncoderUtils.get_value_key(param_val)]
        else:
            params = []

        node_params = get_call_params(call_node)

        while (PARAM_LIST == get_node_type(node_params)):
            p_node = get_param_name(node_params)
            p = TraceSpecConverter.specnode2traceval(p_node)
            p_value = EncoderUtils.get_value_key(p)
            params.append(p_value)
            node_params = get_param_tail(node_params)

        return EncoderUtils.get_key(retval, call_type, entry_type,
                                    method_name, params)


    @staticmethod
    def get_value_key(value):
        """ Given a value returns its representation
        that will be used in the message key """

        assert (isinstance(value, CValue))

        value_repr = value.get_value()

        return value_repr


    @staticmethod
    def enum_types(src_string, submaps_list):
        # generate all the possible combination of
        # strings from src_string and a list of
        # substitutions map
        # Assume maps to be disjoint

        def enum_types_rec(result, current_subs, submaps_list):
            if len(submaps_list) == 0:
                # base case
                return result
            else:
                current_map = submaps_list[0]
                subs_obj = submaps_list[0]

                assert (isinstance(subs_obj, Subs))

                for list_of_values in subs_obj.val_list:
                    assert len(subs_obj.subs_list) == len(list_of_values)
                    name2val = {}
                    for (key, val) in zip(subs_obj.subs_list, list_of_values):
                        name2val[key] = val
                    new_candidate = _substitute(current_subs, name2val)
                    if (1 == len(submaps_list)):
                        result.add(new_candidate)
                    else:
                        enum_types_rec(result, new_candidate, submaps_list[1:])

        result = set()
        enum_types_rec(result, src_string, submaps_list)
        return result

class Subs():
    def __init__(self, subs_list, val_list):
        # check the right number of substitutions
        for elem in val_list:
            assert(len(elem) == len(subs_list))
        self.subs_list = subs_list
        self.val_list = val_list
