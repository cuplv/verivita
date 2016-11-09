"""
Parser for the lifestate specifications

STD ISSUE WITH THIS: it is non-rentrant (e.g. issue if we span
multiple verifiers from the same python interpreter)

BNF grammar

specs   : spec
        | spec TOK_SEQUENCE specs

spec    : TOK_SPEC regexp TOK_DISABLE atom
        | TOK_SPEC regexp TOK_ENABLE atom

regexp  : bexp
        | bexp TOK_STAR
        | regexp TOK_SEQUENCE regexp


bexp    : atom
        | TOK_NOT bexp
        | bexp TOK_AND bexp
        | bexp TOK_OR bexp


atom    : TOK_ID DOT TOK_ID TOK_LPAREN TOK_RPAREN
        | TOK_ID TOK_LPAREN TOK_RPAREN
        | TOK_ID DOT TOK_ID (paramlist)
        | TOK_ID (paramlist)

paramlist : TOK_ID
          | TOK_TRUE
          | TOK_FALSE
          | TOK_FLOAT
          | TOK_INT
          | paramlist, paramlist

"""

import ply.lex as lex
from cbverifier.specs.spec_lex import lexer
from cbverifier.specs.spec_lex import tokens
import ply.yacc as yacc



precedence = (
    ('left','TOK_SPEC'),
    ('left','TOK_ENABLE','TOK_DISABLE'),
    ('left','TOK_SEQUENCE'),
    ('left','TOK_STAR'),
    ('left','TOK_AND','TOK_OR'),
    ('right','TOK_NOT'),
    )


def p_specs(t):
    '''specs : spec
             | spec TOK_SEQUENCE specs
    '''
    # DEBUG: just return something
    t[0] = (1)

def p_spec(t):
    '''spec : TOK_SPEC regexp TOK_DISABLE atom
            | TOK_SPEC regexp TOK_ENABLE atom
    '''

def p_regexp(t):
    '''regexp : bexp
              | bexp TOK_STAR
              | regexp TOK_SEQUENCE regexp
    '''

def p_bexp(t):
    '''bexp : atom
            | TOK_NOT bexp
            | bexp TOK_AND bexp
            | bexp TOK_OR bexp
    '''

def p_atom(t):
    '''atom : TOK_ID TOK_DOT TOK_ID TOK_LPAREN TOK_RPAREN
            | TOK_ID TOK_LPAREN TOK_RPAREN
            | TOK_ID TOK_DOT TOK_ID TOK_LPAREN paramlist TOK_RPAREN
            | TOK_ID TOK_LPAREN paramlist TOK_RPAREN
    '''

def p_param(t):
    '''paramlist : param
                 | param TOK_COMMA paramlist
    '''

def p_paramlist(t):
    '''param : TOK_ID
             | TOK_TRUE
             | TOK_FALSE
             | TOK_FLOAT
             | TOK_INT
    '''

handlers = []

def p_error(t):
    for handler in handlers:
        handler.set_in_error(t_value)

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



