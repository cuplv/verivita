"""
Parser for the lifestate specifications.

STD ISSUE WITH THIS: it is non-rentrant (e.g. issue if we span
multiple verifiers from the same python interpreter)


While parsing we build an AST to represent the SPEC.
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
    if "|-" == t[3]:
        t[0] = new_disable_spec(t[2], t[4])
    elif "|+" == t[3]:
        t[0] = new_enable_spec(t[2], t[4])
    else:
        p_error(t)


def p_regexp(t):
    '''regexp : bexp
    '''
    t[0] = t[1]

def p_regexp_star(t):
    '''regexp : bexp TOK_STAR
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

    if (t[2] == "|"):
        t[0] = new_or(t[1], t[3])
    else:
        t[0] = new_and(t[1], t[3])

def p_bexp_paren(t):
    '''bexp : TOK_LPAREN bexp TOK_RPAREN
    '''
    t[0] = t[2]


def p_atom_no_param(t):
    '''atom : TOK_ID TOK_DOT TOK_ID TOK_LPAREN TOK_RPAREN
            | TOK_ID TOK_LPAREN TOK_RPAREN
    '''

    if (t[2] == '.'):
        receiver = t[1]
        method_name = t[3]
    else:
        receiver = None
        method_name = t[1]

    t[0] = new_call(new_id(receiver), new_id(method_name), new_nil())

def p_atom_param(t):
    '''atom : TOK_ID TOK_DOT TOK_ID TOK_LPAREN paramlist TOK_RPAREN
            | TOK_ID TOK_LPAREN paramlist TOK_RPAREN
    '''

    if (t[2] == '.'):
        receiver = t[1]
        method_name = t[3]
        params = t[5]
    else:
        receiver = new_nil()
        method_name = t[1]
        params = t[3]

    t[0] = new_call(new_id(receiver), new_id(method_name), params)

def p_atom_const(t):
    '''atom : TOK_TRUE
            | TOK_FALSE
    '''

    if (t[1] == 'TRUE'):
        t[0] = new_true()
    else:
        t[0] = new_false()

def p_paramlist_param(t):
    '''paramlist : param
    '''
    t[0] = new_param(t[1],new_nil())

def p_paramlist(t):
    '''paramlist : param TOK_COMMA paramlist
    '''
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


def p_error(t):
    for handler in handlers:
        if (t is not None):
            handler.set_in_error(t.value)
        else:
            handler.set_in_error("unknown")

handlers = []

parser = yacc.yacc(debug=0)

class SpecParser(object):
    def __init__(self, parser):
        self.parser = None
        self.in_error = False

    def parse(self, spec_str):
        self.in_error = False
        spec_list = parser.parse(spec_str)
        if (self.in_error): spec_list = None
        return spec_list

    def set_in_error(self, t_value):
        # DEBUG
        print("Syntax error at '%s'" % t_value)

        self.in_error = True


spec_parser = SpecParser(parser)
handlers.append(spec_parser)



