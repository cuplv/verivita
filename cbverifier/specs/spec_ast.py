"""
Defines the AST nodes and structure for a SPEC formula.

TODO:
- Do we need a DAG representation for specs instead of a tree?
  TODO: add memoization
  - NOTE: since we are using tuples in python and the inner elements
    are not object, apart string, the formula representation is already
    ok.
- add walkers (e.g. explore the DAG of the formula)
"""
import sys


# SYMBOLS
TRUE=0
FALSE=1
ID=2
INT=3
FLOAT=4
PARAM_LIST=5
NIL=6
CALL=7
AND_OP=8
OR_OP=9
NOT_OP=10
SEQ_OP=11
STAR_OP=19
SPEC_SYMB=12
ENABLE_OP=13
DISABLE_OP=14
SPEC_LIST=15
DONTCARE=16
STRING=17
VALUE=18

inv_map = {0 : "TRUE",
           1 : "FALSE",
           2 : "ID",
           3 : "INT",
           4 : "FLOAT",
           5 : "PARAM_LIST",
           6 : "NIL",
           7 : "CALL",
           8 : "AND_OP",
           9 : "OR_OP",
           10 : "NOT_OP",
           11 : "SEQ_OP",
           11 : "STAR_OP",
           12 : "SPEC_SYMB",
           13 : "ENABLE_OP",
           14 : "DISABLE_OP",
           15 : "SPEC_LIST",
           16 : "DONTCARE",
           17 : "STRING"}


################################################################################
# Node creation
################################################################################

def create_node(node_type, children):
    l = []
    l.append(node_type)
    for c in children: l.append(c)
    return tuple(l)

def new_nil(): return (NIL,)
def new_dontcare(): return (DONTCARE,)
def new_float(float_num): return (FLOAT, float_num)
def new_int(int_num): return (INT, int_num)
def new_id(id_string): return (ID, id_string)
def new_string(string_value): return (STRING, string_value)
def new_false(): return (FALSE,)
def new_true(): return (TRUE,)
def new_param(first, tails): return (PARAM_LIST, first, tails)

def new_call(receiver, method_name, params):
    return (CALL, receiver, method_name, params)

def new_and(p1,p2): return (AND_OP, p1, p2)
def new_or(p1,p2): return (OR_OP, p1, p2)
def new_not(p1): return (NOT_OP, p1)

def new_seq(p1,p2): return (SEQ_OP, p1, p2)
def new_star(p1): return (STAR_OP, p1)

def new_value(value):
    # wraps a trace runner value
    return (VALUE, value)

def new_enable_spec(regexp, atom):
    return (SPEC_SYMB, (ENABLE_OP, regexp, atom))

def new_disable_spec(regexp, atom):
    return (SPEC_SYMB, (DISABLE_OP, regexp, atom))

def new_spec_list(spec, rest):
    return (SPEC_LIST, spec, rest)


################################################################################
# Access node
################################################################################

def get_node_type(node): return node[0]

const_nodes = (TRUE,FALSE,STRING,INT,FLOAT)
leaf_nodes = (TRUE,FALSE,ID,STRING,INT,FLOAT,NIL,DONTCARE)
logic_nodes = (AND_OP, OR_OP,NOT_OP)
regexp_nodes = (SEQ_OP,STAR_OP)
spec_nodes = (SPEC_SYMB,ENABLE_OP,DISABLE_OP)


def get_id_val(node): return node[1]

def get_call_receiver(node):
    assert CALL == get_node_type(node)
    assert node[1] is not None
    return node[1]

def get_call_method(node):
    assert CALL == get_node_type(node)
    assert node[2] is not None
    return node[2]

def get_call_params(node):
    assert CALL == get_node_type(node)
    assert node[3] is not None
    return node[3]

def get_regexp_node(node):
    assert SPEC_SYMB == get_node_type(node)
    assert node[1] is not None
    assert get_node_type(node[1]) in [ENABLE_OP, DISABLE_OP]

    regexpnode = (node[1])[1]
    assert regexpnode is not None
    return regexpnode

def get_spec_rhs(node):
    assert SPEC_SYMB == get_node_type(node)
    assert node[1] is not None
    assert get_node_type(node[1]) in [ENABLE_OP, DISABLE_OP]

    rhs = (node[1])[2]
    assert rhs is not None
    return rhs

def is_spec_enable(node):
    assert SPEC_SYMB == get_node_type(node)
    assert node[1] is not None
    return get_node_type(node[1]) == ENABLE_OP

def is_spec_disable(node):
    assert SPEC_SYMB == get_node_type(node)
    assert node[1] is not None
    return get_node_type(node[1]) == DISABLE_OP


################################################################################
# Node creation
################################################################################


def pretty_print(ast_node, out_stream=sys.stdout):

    def pretty_print_aux(out_stream, node, sep):
        def my_print(out_stream, string):
            out_stream.write(string)

        node_type = get_node_type(node)
        if (node_type == TRUE): my_print(out_stream, "TRUE")
        elif (node_type == FALSE): my_print(out_stream, "FALSE")
        elif (node_type == DONTCARE): my_print(out_stream, "_")
        elif (node_type == ID or node_type == INT or node_type == FLOAT or node_type == STRING):
            my_print(out_stream, "%s%s" % (sep, str(node[1])))
        elif (node_type == VALUE):
            value = node[1]

            if value.is_null:
                value_repr = "NULL"
            elif value.value is not None:
                value_repr = str(value.value)
            elif value.object_id is not None:
                value_repr = str(value.object_id)
            else:
                raise Exception("Cannot find a unique identifier for the value "\
                                "%s%s" % (sep, str(value)))

            my_print(out_stream, "%s" % value_repr)
        elif (node_type == PARAM_LIST):
            pretty_print_aux(out_stream,node[1],"")
            if (get_node_type(node[2]) != new_nil()):
                my_print(out_stream, ",")
                pretty_print_aux(out_stream,node[2],"")
        elif (node_type == CALL):
            receiver = get_call_receiver(node)
            if (get_node_type(receiver) != new_nil()):
                pretty_print_aux(out_stream,receiver,"") # receiver
                my_print(out_stream, ".")
            pretty_print_aux(out_stream,get_call_method(node),"")
            my_print(out_stream, "(")

            param_list = get_call_params(node)
            if (param_list != new_nil()):
                pretty_print_aux(out_stream, param_list, "") # params

            my_print(out_stream, ")")
        elif (node_type == AND_OP or node_type == OR_OP):
            my_print(out_stream, "(")
            pretty_print_aux(out_stream,node[1],"")
            my_print(out_stream, " & ")
            pretty_print_aux(out_stream,node[2],"")
            my_print(out_stream, ")")
        elif (node_type == NOT_OP):
            my_print(out_stream, "! ")
            pretty_print_aux(out_stream,node[1],"")
        elif (node_type == SEQ_OP):
            pretty_print_aux(out_stream,node[1],"")
            if (get_node_type(node[2]) != new_nil()):
                my_print(out_stream, "; ")
                pretty_print_aux(out_stream,node[2],"")
        elif (node_type == STAR_OP):
            pretty_print_aux(out_stream,node[1],"")
            my_print(out_stream, "[*]")
        elif (node_type == SPEC_SYMB):
            my_print(out_stream, "SPEC ")
            pretty_print_aux(out_stream ,node[1], "")
        elif (node_type == ENABLE_OP or
              node_type == DISABLE_OP):

            pretty_print_aux(out_stream ,node[1], "")

            if (node_type == ENABLE_OP):
                my_print(out_stream, " |+ ")
            elif (node_type == DISABLE_OP):
                my_print(out_stream, " |- ")
            else:
                raise Exception("Unknown type of spec")

            pretty_print_aux(out_stream,node[2],"")
        elif (node_type == SPEC_LIST):
            pretty_print_aux(out_stream,node[1],"")
            my_print(out_stream, ";\n")
            if (get_node_type(node[2]) != new_nil()):
                pretty_print_aux(out_stream,node[2],"")
        else:
            raise UnexpectedSymbol(node)

    pretty_print_aux(out_stream, ast_node, "")


class UnexpectedSymbol(Exception):
    def __init__(self, node):
        self.node = node
        node_type = get_node_type(node)
        message = "Unexpected symbol %s" % inv_map[node_type]

        super(Exception, self).__init__(message)


