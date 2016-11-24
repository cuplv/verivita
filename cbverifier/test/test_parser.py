""" Test the specification parser

"""

import logging
import unittest


from ply.lex import LexToken
import ply.yacc as yacc

from cStringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.specs.spec_lex import lexer, reset
from cbverifier.specs.spec_parser import spec_parser
from cbverifier.specs.spec_ast import *


class TestSpecParser(unittest.TestCase):

    def setUp(self):
        reset()

    @staticmethod
    def new_tok(lexpos, tok_type, lineno, value):
        # Create a token for return
        tok = LexToken()
        tok.value = value
        tok.lineno = lineno
        tok.lexpos = lexpos
        tok.type = tok_type
        return tok

    def _test_multiple_token(self, token_list, string):
        # clean the lexer state
        # for f in lexer: None

        lexer.input(string)

        i = 0
        tok = lexer.token()
        while (tok is not None):
            if i > len(token_list):
                raise Exception("Found more tokens than expeced")

            self.assertTrue(tok.value == token_list[i].value)
            self.assertTrue(tok.lineno == token_list[i].lineno)
            self.assertTrue(tok.lexpos == token_list[i].lexpos)
            self.assertTrue(tok.type == token_list[i].type)

            i = i + 1
            tok = lexer.token()

        # did not parse anything else
        with self.assertRaises(StopIteration):
            lexer.next()

    def _test_single_token(self, lexpos, tok_type, lineno, value, string):
        tok_ref = TestSpecParser.new_tok(lexpos,tok_type,lineno,value)

        return self._test_multiple_token([tok_ref], string)


    def test_lexer(self):
        self._test_single_token(0,'TOK_ID',1,'ciao','ciao')
        self._test_single_token(0,'TOK_ID',1,'<ciao>','<ciao>')
        self._test_single_token(0,'TOK_INT',1,2,'2')
        self._test_single_token(0,'TOK_FLOAT',1,0.0,'0.0')

        self._test_single_token(0, 'TOK_NOT', 1, '!', '!')
        self._test_single_token(0, 'TOK_AND', 1, '&', '&')
        self._test_single_token(0, 'TOK_OR', 1, '|', '|')
        self._test_single_token(0, 'TOK_SEQUENCE', 1, ';', ';')
        self._test_single_token(0, 'TOK_STAR', 1, '*', '*')
        self._test_single_token(0, 'TOK_ENABLE', 1, '|+', '|+')
        self._test_single_token(0, 'TOK_DISABLE', 1, '|-', '|-')
        self._test_single_token(0, 'TOK_DOT', 1, '.', '.')
        self._test_single_token(0, 'TOK_COMMA', 1, ',', ',')
        self._test_single_token(0, 'TOK_LPAREN', 1, '(', '(')
        self._test_single_token(0, 'TOK_RPAREN', 1, ')', ')')
        self._test_single_token(0, 'TOK_DONTCARE', 1, '#', '#')

        self._test_single_token(0, 'TOK_TRUE', 1, 'TRUE', 'TRUE')
        self._test_single_token(0, 'TOK_FALSE', 1, 'FALSE', 'FALSE')
        self._test_single_token(0, 'TOK_CB', 1, 'CB', 'CB')
        self._test_single_token(0, 'TOK_CI', 1, 'CI', 'CI')
        self._test_single_token(0, 'TOK_ASSIGN', 1, '=', '=')

        self._test_single_token(0, 'TOK_STRING_LITERAL', 1,
                                '"dita nel naso"',
                                '"dita nel naso"')
        self._test_single_token(0, 'TOK_STRING_LITERAL', 1,
                                '"abc \\" asfds \\""',
                                '"abc \\" asfds \\""')

        self._test_single_token(0, 'TOK_SPEC', 1, 'SPEC', 'SPEC')


        # TestSpecParser.new_tok(lexpos,tok_type,lineno,value)
        res = [TestSpecParser.new_tok(0,'TOK_ID',1,'l'),
               TestSpecParser.new_tok(1,'TOK_DOT',1,'.'),
               TestSpecParser.new_tok(2,'TOK_ID',1,'l'),
               TestSpecParser.new_tok(3,'TOK_LPAREN',1,'('),
               TestSpecParser.new_tok(4,'TOK_RPAREN',1,')')]
        self._test_multiple_token(res, "l.l()"),

        # TestSpecParser.new_tok(lexpos,tok_type,lineno,value)
        res = [TestSpecParser.new_tok(0,'TOK_ID',1,'l'),
               TestSpecParser.new_tok(1,'TOK_DOT',1,'.'),
               TestSpecParser.new_tok(2,'TOK_ID',1,'l'),
               TestSpecParser.new_tok(3,'TOK_LPAREN',1,'('),
               TestSpecParser.new_tok(4,'TOK_DONTCARE',1,'#'),
               TestSpecParser.new_tok(5,'TOK_RPAREN',1,')')]
        self._test_multiple_token(res, "l.l(#)"),


    def _test_parse(self, specs):
        res = spec_parser.parse(specs)
        self.assertTrue(res is not None)
        # test the printing of the spec ast
        stringio = StringIO()
        pretty_print(res, stringio)


    def _test_parse_error(self, specs):
        res = spec_parser.parse(specs)
        self.assertTrue(res is None)

    def test_parser(self):
        correct_expr = ["SPEC [CB] [l] type l() |- [CB] [l] type l(b)",
                        "SPEC [CB] [l] type l(l1,l2) |- [CB] [l] type l(b)",
                        "SPEC [CB] [l] type l(l1,l2) |- [CI] [l] type l(b); SPEC [CB] [l] type l(l1,l2) |- [CI] [l] type l(b)",
                        "SPEC [CB] [l] type l(l1,l2); [CB] [l] type l(l1,l2) |- [CI] [l] type l(b)",
                        "SPEC [CB] [l] type l(l1,l2)[*] |- [CI] [l] type l(b)",
                        "SPEC [CB] [l] type l(l1,l2)[*] |+ [CI] [l] type l(b)",
                        "SPEC [CB] [l] type l(l1,l2)[*] |- [CI] [l] type l(b)",
                        "SPEC [CB] [l] type b(l1,l2)[*] |- [CI] [l] type l(b)",
                        "SPEC [CB] [l] void <init>(l1,l2)[*] |- [CI] [l] type l(b)",
                        "SPEC TRUE |- TRUE",
                        "SPEC TRUE[*] |- TRUE",
                        "SPEC (TRUE)[*] |- TRUE",
                        "SPEC [CB] [l] type m1()[*] |- TRUE",
                        "SPEC (TRUE & FALSE)[*] |- TRUE",
                        "SPEC (TRUE & FALSE | ! FALSE)[*] |- TRUE",
                        "SPEC [CB] [l1] type methodName(TRUE) |- [CI] [l2] type methodName(bparam,TRUE)",
                        "SPEC [CB] [l1] type methodName(#) |- [CI] [l2] type methodName(bparam,TRUE)",
                        "SPEC foo = [CB] [l1] type methodName(#) |- [CI] [l2] type methodName(bparam,TRUE)",
                        "SPEC foo = [CB] [l1] type methodName(a); foo = [CB] [l1] type methodName(a) |- [CI] [l2] type methodName(bparam,TRUE)",
                        "SPEC 1 = [CB] [l1] type methodName(#) |- [CI] [l2] type methodName(bparam,TRUE)",
                        "SPEC # = [CB] [l1] type methodName(#) |- [CI] [l2] type methodName(bparam,TRUE)",
                        "SPEC TRUE = [CB] [l1] type methodName(#) |- [CI] [l2] type methodName(bparam,TRUE)",
                        'SPEC [CB] [l] type l(l1,"foo")[*] |- [CI] [l] type l(b)']

        for expr in correct_expr:
            self._test_parse(expr)

        wrong_expr = ["SPEC TRUE "]
        for expr in wrong_expr:
            self._test_parse_error(expr)

    def test_ast(self):
        def test_ast_inner(specs, expected):
            parse_res = spec_parser.parse(specs)
            self.assertTrue(parse_res == expected)

        res = [("SPEC [CB] [l] void package.method_name() |- TRUE",
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (NIL,), (CB,), (ID,'l'), (ID, 'void package.method_name'), (NIL,)),
                   (0,))), (NIL,))),
               ("SPEC [CB] [l] void package.method_name() |- TRUE",
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (NIL,), (CB,), (ID,'l'), (ID, 'void package.method_name'), (NIL,)),
                   (0,))), (NIL,))),
               ("SPEC [CI] [l] void method_name(0,1,f) |- TRUE",
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (NIL,), (CI,), (ID,'l'), (ID, 'void method_name'), (PARAM_LIST, (INT, 0), (PARAM_LIST, (INT, 1), (PARAM_LIST, (ID, 'f'), (NIL,))))),
                   (0,))), (NIL,))),
               ("SPEC var = [CI] [l] void method_name(0,1,f) |- TRUE",
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (ID,'var'), (CI,), (ID,'l'), (ID, 'void method_name'), (PARAM_LIST, (INT, 0), (PARAM_LIST, (INT, 1), (PARAM_LIST, (ID, 'f'), (NIL,))))),
                   (0,))), (NIL,))),
               ('SPEC var = [CI] [l] void method_name(0,"foobar",f) |- TRUE',
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (ID,'var'), (CI,), (ID,'l'), (ID, 'void method_name'),
                    (PARAM_LIST, (INT, 0), (PARAM_LIST, (STRING, '"foobar"'), (PARAM_LIST, (ID, 'f'), (NIL,))))),
                   (0,))), (NIL,)))]

        for r in res:
            test_ast_inner(r[0], r[1])


