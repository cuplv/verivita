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
    ('left','TOK_ENABLE','TOK_DISABLE'),
    ('left','TOK_SEQUENCE'),
    ('left','TOK_STAR'),
    ('left','TOK_AND','TOK_OR'),
    ('right','TOK_NOT'),
    ('left','TOK_TRUE'),
    ('left','TOK_FALSE'),
    )


def p_specs(t):
    '''specs : spec
             | spec TOK_SEQUENCE specs
    '''
    if (len(t) == 2):
        t[0] = new_spec_list(t[1], new_nil())
    else:
        t[0] = new_spec_list(t[1], t[3])

def p_spec(t):
    '''spec : TOK_SPEC regexp TOK_DISABLE atom
            | TOK_SPEC regexp TOK_ENABLE atom
    '''
    if '|-' == t[3]:
        t[0] = new_disable_spec(t[2], t[4])
    elif '|+' == t[3]:
        t[0] = new_enable_spec(t[2], t[4])
    else:
        p_error(t)


def p_regexp(t):
    '''regexp : bexp
    '''
    t[0] = t[1]

def p_regexp_star(t):
    '''regexp : bexp TOK_LSQUARE TOK_STAR TOK_RSQUARE
    '''
    t[0] = new_star(t[1])

def p_regexp_sequence(t):
    '''regexp : regexp TOK_SEQUENCE regexp
    '''
    t[0] = new_seq(t[1], t[3])

def p_bexp(t):
    '''bexp : atom
    '''
    t[0] = t[1]

def p_bexp_unary(t):
    '''bexp : TOK_NOT bexp
    '''
    t[0] = new_not(t[2])

def p_bexp_binary(t):
    '''bexp : bexp TOK_AND bexp
            | bexp TOK_OR bexp
    '''

    if (t[2] == '|'):
        t[0] = new_or(t[1], t[3])
    else:
        t[0] = new_and(t[1], t[3])

def p_bexp_paren(t):
    '''bexp : TOK_LPAREN bexp TOK_RPAREN
    '''
    t[0] = t[2]


def p_atom(t):
    '''atom : param TOK_ASSIGN TOK_LSQUARE method_type TOK_RSQUARE method_call
            | TOK_LSQUARE method_type TOK_RSQUARE method_call
    '''
    if (t[2] == '='):
        assert len(t) == 7
        assignee = t[1]
        call_type = t[4]
        method_call = t[6]
    else:
        assert len(t) == 5
        assignee = new_nil()
        call_type = t[2]
        method_call = t[4]

    receiver = method_call[0]
    inner_call = method_call[1]
    method_name = inner_call[0]
    method_param = inner_call[1]

    # print("receiver " + str(method_call[0]) + "call " + str(method_call[1]) + "name " + str(inner_call[0]) + "param " + str(inner_call[1]))

    t[0] = new_call(assignee, call_type, receiver,
                    method_name, method_param)

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
    '''inner_call : composed_id TOK_LSQUARE paramlist TOK_RSQUARE
                  | composed_id TOK_LSQUARE TOK_RSQUARE'''
    if (t[3] != ']'):
        t[0] = (t[1], t[3])
    else:
        t[0] = (t[1], new_nil())

def p_paramlist_param(t):
    '''paramlist : param
                 | param TOK_COMMA paramlist
    '''
    if (len(t) == 2):
        t[0] = new_param(t[1],new_nil())
    else:
        t[0] = new_param(t[1],t[3])

def p_param_id(t):
    '''param : TOK_ID'''
    t[0] = new_id(t[1])

def p_param_true(t):
    '''param : TOK_TRUE'''
    t[0] = new_true()

def p_param_false(t):
    '''param : TOK_FALSE'''
    t[0] = new_false()

def p_param_float(t):
    '''param : TOK_FLOAT'''
    t[0] = new_float(t[1])

def p_param_int(t):
    '''param : TOK_INT'''
    t[0] = new_int(t[1])

def p_param_dontcare(t):
    '''param : TOK_DONTCARE'''
    t[0] = new_dontcare()

def p_composed_id_primary(t):
    '''composed_id : TOK_ID
                   | TOK_ID TOK_DOT composed_id
                   | TOK_ID composed_id'''
    if (len(t) == 2):
        t[0] = new_id(t[1])
    else:
        if (t[2] == '.'):
            t[0] = new_id("%s.%s" % (t[1], t[3][1]))
        else:
            t[0] = new_id("%s %s" % (t[1], t[2][1]))

def p_composed_id_lparens(t):
    '''composed_id : TOK_LPAREN
                   | TOK_LPAREN composed_id'''
    if (len(t) == 2):
        t[0] = new_id("(")
    else:
        t[0] = new_id("(" + t[2][1])

def p_composed_id_rparens(t):
    '''composed_id : TOK_RPAREN
                   | TOK_RPAREN composed_id'''
    if (len(t) == 2):
        t[0] = new_id(")")
    else:
        t[0] = new_id(")" + t[2][1])


def p_method_type(t):
    ''' method_type : TOK_CI
                    | TOK_CB
    '''
    if (t[1] == 'CI'):
        t[0] = new_ci()
    elif (t[1] == 'CB'):
        t[0] = new_cb()



def p_error(t):
    for handler in handlers:
        if (t is not None):
            handler.set_in_error(t.value)
        else:
            handler.set_in_error("unknown")

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

    def parse(self, spec_str):
        self.in_error = False
        spec_list = parser.parse(spec_str)
        if (self.in_error): spec_list = None
        return spec_list

    def set_in_error(self, t_value):
        # DEBUG
        print("Syntax error at '%s'" % t_value)

        # store the error status
        self.in_error = True
        self.error_value = t_value


spec_parser = SpecParser(parser)
handlers.append(spec_parser)



