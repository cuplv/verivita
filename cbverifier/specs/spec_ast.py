"""
Defines the AST nodes and structure for a SPEC formula.

TODO: add memoization

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
STAR_OP=11
SPEC_SYMB=12
ENABLE_OP=13
DISABLE_OP=14
SPEC_LIST=15

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
           15 : "SPEC_LIST"}

def new_nil(): return (NIL,)
def new_float(float_num): return (FLOAT, float_num)
def new_int(int_num): return (INT, int_num)
def new_id(id_string): return (ID, id_string)
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


def new_enable_spec(regexp, atom):
    return (SPEC_SYMB, ENABLE_OP, regexp, atom)

def new_disable_spec(regexp, atom):
    return (SPEC_SYMB, DISABLE_OP, regexp, atom)

def new_spec_list(spec, rest):
    return (SPEC_LIST, spec, rest)

def get_node_type(node): return node[0]

# def is_node_leaf(node):
#     """ True if the node is a leaf and do not require
#     to be visited in recursion"""



def pretty_print(ast_node, out_stream=sys.stdout):

    def pretty_print_aux(out_stream, node, sep):
        def my_print(out_stream, string):
            out_stream.write(string)

        node_type = get_node_type(node)
        if (node_type == TRUE): my_print(out_stream, "TRUE")
        elif (node_type == FALSE): my_print(out_stream, "FALSE")
        elif (node_type == ID or node_type == INT or node_type == FLOAT):
            my_print(out_stream, "%s%s" % (sep, str(node[1])))
        elif (node_type == PARAM_LIST):
            pretty_print_aux(out_stream,node[1],"")
            if (get_node_type(node[2]) != new_nil()):
                my_print(out_stream, ",")
                pretty_print_aux(out_stream,node[2],"")
        elif (node_type == CALL):
            if (get_node_type(node[1]) != new_nil()):
                pretty_print_aux(out_stream,node[1],"") # receiver
                my_print(out_stream, ".")
            pretty_print_aux(out_stream,node[2],"")
            my_print(out_stream, "(")
            pretty_print_aux(out_stream,node[3],"") # params
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
            pretty_print_aux(out_stream,node[2],"")

            if (node[1] == ENABLE_OP):
                my_print(out_stream, " |+ ")
            elif (node[1] == DISABLE_OP):
                my_print(out_stream, " |- ")
            else:
                raise Exception("Unkown type of spec")

            pretty_print_aux(out_stream,node[3],"")
        elif (node_type == SPEC_LIST):
            pretty_print_aux(out_stream,node[1],"")
            my_print(out_stream, ";\n")
            if (get_node_type(node[2]) != new_nil()):
                pretty_print_aux(out_stream,node[2],"")

    pretty_print_aux(out_stream, ast_node, "")
