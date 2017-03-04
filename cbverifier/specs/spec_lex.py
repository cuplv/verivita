"""
Lexer for the lifestate specifications
"""

# MISSING:
# - STRING
# - brittle on numbers...
#

import ply.lex as lex
import ply.yacc as yacc

keywords = ('TOK_SPEC','TOK_TRUE','TOK_FALSE','TOK_NULL','TOK_CB','TOK_CI','TOK_ENTRY','TOK_EXIT','TOK_ALIASES')

tokens = keywords + (
    'TOK_ID',
    'TOK_ID_ADDRESS',
    'TOK_INT',
    'TOK_FLOAT',
    'TOK_NOT',
    'TOK_STAR',
    'TOK_AND',
    'TOK_OR',
    'TOK_SEQUENCE',
    'TOK_ENABLE',
    'TOK_DISABLE',
    'TOK_DOT',
    'TOK_COMMA',
    'TOK_COLON',
    'TOK_LPAREN',
    'TOK_RPAREN',
    'TOK_LSQUARE',
    'TOK_RSQUARE',
    'TOK_DONTCARE',
    'TOK_ASSIGN',
    'TOK_STRING_LITERAL',
    )

# Tokens
def t_TOK_ID(t):
    r'[a-zA-Z_$<>][a-zA-Z0-9_$<>]*'
    if "TOK_" + t.value in keywords:
        t.type = "TOK_" + t.value
    return t

# Allows also numbers in the first character
# It is needed to parse object addresses
def t_TOK_ID_ADDRESS(t):
    r'[a-zA-Z0-9_$<>][a-zA-Z0-9_$<>]+'
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

# Add BSD license from: https://github.com/eliben/pycparser (or rewrite it)
simple_escape = r"""([a-zA-Z._~!=&\^\-\\?'"])"""
decimal_escape = r"""(\d+)"""
hex_escape = r"""(x[0-9a-fA-F]+)"""
escape_sequence = r"""(\\("""+simple_escape+'|'+decimal_escape+'|'+hex_escape+'))'
string_char = r"""([^"\\\n]|"""+escape_sequence+')'
t_TOK_STRING_LITERAL = '"'+ string_char +'*"'

t_TOK_NOT = r"\!"
t_TOK_AND = r"\&"
t_TOK_OR = r"\|"
t_TOK_SEQUENCE=r";"
t_TOK_STAR=r"\*"
t_TOK_ENABLE = r"\|\+"
t_TOK_DISABLE = r"\|-"
t_TOK_DOT = r"\."
t_TOK_COMMA = r","
t_TOK_COLON = r":"
t_TOK_LPAREN  = r'\('
t_TOK_RPAREN  = r'\)'
t_TOK_LSQUARE  = r'\['
t_TOK_RSQUARE  = r'\]'
t_TOK_DONTCARE = r'\#'
t_TOK_ASSIGN = r'\='
# Ignored characters
t_ignore = " \t"
t_ignore_COMMENT = r'\/\/.*'


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def reset():
    lexer.lineno = 1
    if lexer.lexdata is None:
        return
    tok = lexer.token()
    while (tok is not None):
        tok = lexer.token()


# Build the lexer
import ply.lex as lex
lexer = lex.lex(debug=0)



