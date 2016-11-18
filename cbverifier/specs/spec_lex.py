"""
Lexer for the lifestate specifications
"""

# MISSING:
# - STRING
# - brittle on numbers...
#

import ply.lex as lex
import ply.yacc as yacc

keywords = ('TOK_SPEC','TOK_TRUE','TOK_FALSE',)

tokens = keywords + (
    'TOK_ID',
    'TOK_INT',
    'TOK_FLOAT',
    'TOK_NOT',
    'TOK_AND',
    'TOK_OR',
    'TOK_SEQUENCE',
    'TOK_STAR',
    'TOK_ENABLE',
    'TOK_DISABLE',
    'TOK_DOT',
    'TOK_COMMA',
    'TOK_LPAREN',
    'TOK_RPAREN',
    'TOK_DONTCARE'
    )

# Tokens
def t_TOK_ID(t):
    r'[a-zA-Z_$][a-zA-Z0-9_$]*'
    if "TOK_" + t.value in keywords:
        t.type = "TOK_" + t.value
    return t

def t_TOK_FLOAT(t):
    r'-?\d+\.\d*(e-?\d+)?'
    try:
        t.value = float(t.value)
    except ValueError:
        print("Error reading float value %f", t.value)
        t.value = 0
    return t

def t_TOK_INT(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

t_TOK_NOT = r"\!"
t_TOK_AND = r"\&"
t_TOK_OR = r"\|"
t_TOK_SEQUENCE=r";"
t_TOK_STAR=r"\[\*\]"
t_TOK_ENABLE = r"\|\+"
t_TOK_DISABLE = r"\|-"
t_TOK_DOT = r"\."
t_TOK_COMMA = r","
t_TOK_LPAREN  = r'\('
t_TOK_RPAREN  = r'\)'
t_TOK_DONTCARE = r'\#'
# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def reset():
    lexer.lineno = 1
    tok = lexer.token()
    while (tok is not None):
        tok = lexer.token()


# Build the lexer
import ply.lex as lex
lexer = lex.lex(debug=0)



