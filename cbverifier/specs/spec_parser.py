"""
Parser for the lifestate specifications.

STD ISSUE WITH THIS: it is non-rentrant (e.g. issue if we span
multiple verifiers from the same python interpreter)

While parsing we build an AST to represent the SPEC.

WARNING: rhs of spec now is an atom, wich also contains the assign token.
What does it mean for a spec?
"""

import ply.lex as lex
from cbverifier.specs.spec_lex import lexer
from cbverifier.specs.spec_lex import tokens
from cbverifier.specs.spec_ast import *
import ply.yacc as yacc



precedence = (
    ('left','TOK_SPEC'),
    ('left','TOK_REGEXP'),
    ('left','TOK_ALIASES'),
    ('left','TOK_ENABLE','TOK_DISABLE'),
    ('left','TOK_SEQUENCE'),
    ('left','TOK_AND','TOK_OR'),
    ('left','TOK_STAR'),
    ('right','TOK_NOT'),
    ('left','TOK_TRUE'),
    ('left','TOK_FALSE'),
    )

def p_specs(t):
    '''specs : spec
             | named_expr
             | spec TOK_SEQUENCE specs
             | named_expr TOK_SEQUENCE specs
    '''
    if (len(t) == 2):
        t[0] = new_spec_list(t[1], new_nil())
    else:
        t[0] = new_spec_list(t[1], t[3])

def p_spec(t):
    '''spec : TOK_SPEC regexp TOK_DISABLE atom
            | TOK_SPEC regexp TOK_ENABLE atom
            | TOK_SPEC regexp TOK_DISABLE atom TOK_ALIASES aliases
            | TOK_SPEC regexp TOK_ENABLE atom TOK_ALIASES aliases
    '''

    if (len(t) >= 6):
        aliases = t[6]
    else:
        aliases = new_nil()

    if '|-' == t[3]:
        t[0] = new_disable_spec(t[2], t[4], aliases)
    elif '|+' == t[3]:
        t[0] = new_enable_spec(t[2], t[4], aliases)
    else:
        p_error(t)

def p_named_expr(t):
    ''' named_expr : TOK_REGEXP TOK_ID TOK_LPAREN varlist TOK_RPAREN TOK_ASSIGN regexp
                   | TOK_REGEXP TOK_ID TOK_LPAREN TOK_RPAREN TOK_ASSIGN regexp
    '''
    if len(t) == 8:
        vlist = t[4]
        regexp = t[7]
    else:
        vlist = []
        regexp = t[6]

    t[0] = new_named_regexp(new_id(t[2]), vlist, regexp)

def p_aliases(t):
    '''aliases : alias
               | alias TOK_COMMA aliases
    '''
    # return a list of aliases
    if (len(t) == 4):
        t[0] = new_alias(t[1], t[3])
    else:
        t[0] = new_alias(t[1], new_nil())


def p_alias(t):
    '''alias : composed_id TOK_ASSIGN TOK_LSQUARE cid_list TOK_RSQUARE
    '''
    assert t[4] is not None

    t[0] = (t[1], t[4])

def p_cid_list(t):
    ''' cid_list : composed_id
                 | composed_id TOK_COMMA cid_list
    '''
    if (len(t) == 2):
        t[0] = [t[1]]
    else:
        t[0] = [t[1]]
        t[0].extend(t[3])

def p_regexp(t):
    '''regexp : atom
    '''
    t[0] = t[1]

def p_regexp_star(t):
    '''regexp : regexp TOK_STAR
    '''
    t[0] = new_star(t[1])

def p_regexp_sequence(t):
    '''regexp : regexp TOK_SEQUENCE regexp
    '''
    t[0] = new_seq(t[1], t[3])

def p_regexp_not(t):
    '''regexp : TOK_NOT atom
    '''
    t[0] = new_not(t[2])

def p_regexp_binary(t):
    '''regexp : regexp TOK_AND regexp
              | regexp TOK_OR regexp
    '''

    if (t[2] == '|'):
        t[0] = new_or(t[1], t[3])
    else:
        t[0] = new_and(t[1], t[3])

def p_atom_paren(t):
    '''atom : TOK_LPAREN atom TOK_RPAREN
    '''
    t[0] = t[2]

def p_regexp_paren(t):
    '''regexp : TOK_LPAREN regexp TOK_RPAREN
    '''
    t[0] = t[2]

def p_atom_named_regexp(t):
    '''atom : TOK_ID TOK_LPAREN untyped_paramlist TOK_RPAREN
            | TOK_ID TOK_LPAREN TOK_RPAREN'''
    if (len(t) == 5):
        t[0] = new_named_regexp_inst(new_id(t[1]),t[3])
    else:
        t[0] = new_named_regexp_inst(new_id(t[1]),[])


def p_atom_no_ret_val(t):
    '''atom : TOK_LSQUARE method_type TOK_RSQUARE TOK_LSQUARE entry_type TOK_RSQUARE method_call
    '''

    # for i in range(len(t)):
    #     print str(i) + ": " + str(t[i])

    assert len(t) == 8
    assignee = new_nil()
    call_type = t[2]
    entry_type = t[5]
    method_call = t[7]

    receiver = method_call[0]
    inner_call = method_call[1]
    ret_type = inner_call[0]
    method_name = inner_call[1]
    method_param = inner_call[2]

    # Method signature
    # return_type method_name(type_p1, type_p2, ..., type_pn)
    assert (get_node_type(ret_type) == ID and
            get_node_type(method_name) == ID)
    method_name = new_id("%s %s" % (get_id_val(ret_type),
                                    get_id_val(method_name)))

    if (entry_type == "ENTRY"):
        t[0] = new_call_entry(call_type, receiver, method_name, method_param)
    elif (entry_type == "EXIT"):
        t[0] = new_call_exit(assignee, call_type, receiver,
                             method_name, method_param)
    else:
        assert False

def p_atom_ret_val(t):
    '''atom : param TOK_ASSIGN TOK_LSQUARE method_type TOK_RSQUARE TOK_LSQUARE TOK_EXIT TOK_RSQUARE method_call
    '''
    assert len(t) == 10
    assignee = t[1]
    call_type = t[4]
    entry_type = t[7]
    method_call = t[9]

    receiver = method_call[0]
    inner_call = method_call[1]
    ret_type = inner_call[0]
    method_name = inner_call[1]
    method_param = inner_call[2]

    # Method signature
    # return_type method_name(type_p1, type_p2, ..., type_pn)
    assert (get_node_type(ret_type) == ID and
            get_node_type(method_name) == ID)
    method_name = new_id("%s %s" % (get_id_val(ret_type),
                                    get_id_val(method_name)))

    t[0] = new_call_exit(assignee, call_type, receiver, method_name, method_param)


def p_atom_const(t):
    '''atom : TOK_TRUE
            | TOK_FALSE
    '''

    if (t[1] == 'TRUE'):
        t[0] = new_true()
    else:
        t[0] = new_false()

def p_method_call(t):
    '''method_call : TOK_LSQUARE param TOK_RSQUARE inner_call
                   | inner_call '''
    if (t[1] == '['):
        t[0] = (t[2], t[4])
    else:
        t[0] = (new_nil(), t[1])

def p_inner_call(t):
    '''inner_call : type_id composed_id TOK_LPAREN paramlist TOK_RPAREN
                  | type_id composed_id TOK_LPAREN TOK_RPAREN'''
    if (t[4] != ')'):
        t[0] = (t[1], t[2], t[4])
    else:
        t[0] = (t[1], t[2], new_nil())

def p_paramlist_param(t):
    '''paramlist : param TOK_COLON type_id
                 | param TOK_COLON type_id TOK_COMMA paramlist
    '''
    if (len(t) == 4):
        t[0] = new_param(t[1], t[3], new_nil())
    else:
        t[0] = new_param(t[1], t[3], t[5])

def p_untyped_paramlist_param(t):
    '''untyped_paramlist : param
                         | param TOK_COMMA untyped_paramlist
    '''
    t[0] = [t[1]]
    if (len(t) > 2):
        t[0].extend(t[3])


def p_varlist(t):
    '''varlist : TOK_ID
               | TOK_ID TOK_COMMA varlist
    '''
    v = new_id(t[1])
    if (len(t) == 2):
        t[0] = [v]
    else:
        t[0] = [v]
        t[0].extend(t[3])

def p_param_id(t):
    '''param : TOK_ID
             | TOK_ID_ADDRESS '''
    t[0] = new_id(t[1])

def p_param_true(t):
    '''param : TOK_TRUE'''
    t[0] = new_true()

def p_param_false(t):
    '''param : TOK_FALSE'''
    t[0] = new_false()

def p_param_null(t):
    '''param : TOK_NULL'''
    t[0] = new_null()

def p_param_float(t):
    '''param : TOK_FLOAT'''
    t[0] = new_float(t[1])

def p_param_int(t):
    '''param : TOK_INT'''
    t[0] = new_int(t[1])

def p_param_dontcare(t):
    '''param : TOK_DONTCARE'''
    t[0] = new_dontcare()

def p_param_string(t):
    '''param : TOK_STRING_LITERAL'''
    t[0] = new_string(t[1])

def p_type_id(t):
    '''type_id : composed_id
               | type_id TOK_LSQUARE TOK_RSQUARE'''
    if (len(t) == 2):
        t[0] = t[1]
    else:
        assert (len(t) == 4)
        assert (t[2] == '[' and t[3] == ']')
        assert (get_node_type(t[1]) == ID)
        t[0] = new_id("%s[]" % get_id_val(t[1]))

def p_composed_id(t):
    '''composed_id : TOK_ID
                   | TOK_ID TOK_DOT composed_id'''
    if (len(t) == 2):
        t[0] = new_id(t[1])
    else:
        assert (t[2] == '.')
        t[0] = new_id("%s.%s" % (t[1], t[3][1]))

def p_method_type(t):
    ''' method_type : TOK_CI
                    | TOK_CB
    '''
    if (t[1] == 'CI'):
        t[0] = new_ci()
    elif (t[1] == 'CB'):
        t[0] = new_cb()

def p_entry_type(t):
    ''' entry_type : TOK_ENTRY
                   | TOK_EXIT
    '''
    if (t[1] == 'ENTRY'):
        t[0] = 'ENTRY'
    elif (t[1] == 'EXIT'):
        t[0] = 'EXIT'



def p_error(t):
    for handler in handlers:
        if (t is not None):
            handler.set_in_error(t.value, t.lineno)
        else:
            handler.set_in_error("unknown", -1)

handlers = []

parser = yacc.yacc(debug=0)

class SpecParser(object):
    """ Parse a textual specification and returns its AST
    representation
    """

    def __init__(self, parser):
        self.parser = None
        self.in_error = False
        self.error_value = None
        self.error_line = -1

    def parse(self, spec_str):
        self.in_error = False
        spec_list = parser.parse(spec_str)
        if (self.in_error): spec_list = None
        return spec_list

    def set_in_error(self, t_value, t_lineno):
        # DEBUG
        print("Syntax error at '%s' at line %d." % (t_value, t_lineno))

        # store the error status
        self.in_error = True
        self.error_value = t_value
        self.error_line = t_lineno


spec_parser = SpecParser(parser)
handlers.append(spec_parser)



