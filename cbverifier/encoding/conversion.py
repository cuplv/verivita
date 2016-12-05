""" Utility functions used to convert from messages in the trace and
messages in the specification.
"""

from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CValue

class TraceSpecConverter:

    JAVA_INT_PRIMITIVE = "java.lang.int"
    JAVA_INT = "java.lang.Int"
    JAVA_FLOAT_PRIMITIVE = "java.lang.float"
    JAVA_FLOAT = "java.lang.Float"
    JAVA_BOOLEAN_PRIMITIVE = "java.lang.boolean"
    JAVA_BOOLEAN = "java.lang.Boolean"
    JAVA_STRING = "java.lang.String"

    TRUE_CONSTANT = 1
    FALSE_CONSTANT = 0

    @staticmethod
    def traceval2specnode(trace_val):
        assert isinstance(trace_val, CValue)

        # null
        if trace_val.is_null is not None and trace_val.is_null:
            return new_null()
        elif trace_val.type is not None and trace_val.value is not None:
            if (TraceSpecConverter.JAVA_INT_PRIMITIVE == trace_val.type or
                TraceSpecConverter.JAVA_INT == trace_val.type):
                try:
                    return new_int(int(trace_val.value))
                except ValueError as e:
                    raise Exception("Wrong integer value in message!")
            elif (TraceSpecConverter.JAVA_FLOAT_PRIMITIVE == trace_val.type or
                  TraceSpecConverter.JAVA_FLOAT == trace_val.type):
                try:
                    return new_float(float(trace_val.value))
                except ValueError as e:
                    raise Exception("Wrong float value in message!")
            elif (TraceSpecConverter.JAVA_BOOLEAN_PRIMITIVE == trace_val.type or
                  TraceSpecConverter.JAVA_BOOLEAN == trace_val.type):
                enc_value = CValue.enc(trace_val.value)

                if (str(enc_value) == str(TraceSpecConverter.TRUE_CONSTANT)):
                    return new_true()
                elif (str(enc_value) == str(TraceSpecConverter.FALSE_CONSTANT)):
                    return new_false()
                else:
                    raise Exception("Wrong value for Boolean %s" % enc_value)
            elif trace_val.type == TraceSpecConverter.JAVA_STRING:
                enc_value = CValue.enc(trace_val.value)
                return new_string(enc_value)
            else:
                enc_value = CValue.enc(trace_val.value)
                return new_id(enc_value)
        elif trace_val.object_id is not None:
            enc_value = CValue.enc(trace_val.object_id)
            return new_id(enc_value)
        else:
            raise Exception("Message is not null but it does not "\
                            "have any value or object id")

    @staticmethod
    def specnode2traceval(spec_node):
        node_type = get_node_type(spec_node)
        assert (node_type in const_nodes or
                ID == node_type)

        if NULL == node_type:
            v = CValue()
            v.is_null = True
            v.type = None
            v.value = None
            v.object_id = None
            return v
        elif TRUE == node_type:
            v = CValue()
            v.is_null = False
            v.type = TraceSpecConverter.JAVA_BOOLEAN
            v.value = TraceSpecConverter.TRUE_CONSTANT
            v.object_id = None
            return v
        elif FALSE == node_type:
            v = CValue()
            v.is_null = False
            v.type = TraceSpecConverter.JAVA_BOOLEAN
            v.value = TraceSpecConverter.FALSE_CONSTANT
            v.object_id = None
            return v
        elif STRING == node_type:
            v = CValue()
            v.is_null = False
            v.type = TraceSpecConverter.JAVA_STRING
            v.value = get_id_val(spec_node)
            v.object_id = None
            return v
        elif INT == node_type:
            v = CValue()
            v.is_null = False
            v.type = TraceSpecConverter.JAVA_INT
            v.value = get_id_val(spec_node)
            v.object_id = None
            return v
        elif FLOAT == node_type:
            v = CValue()
            v.is_null = False
            v.type = TraceSpecConverter.JAVA_FLOAT
            v.value = get_id_val(spec_node)
            v.object_id = None
            return v
        elif ID == node_type:
            v = CValue()
            v.is_null = False
            v.type = "java.lang.Object"
            v.value = None
            v.object_id = get_id_val(spec_node)
            return v

        assert False
