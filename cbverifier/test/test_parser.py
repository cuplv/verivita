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
from cbverifier.specs.spec import Spec


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
        self._test_single_token(0, 'TOK_COLON', 1, ':', ':')
        self._test_single_token(0, 'TOK_LPAREN', 1, '(', '(')
        self._test_single_token(0, 'TOK_RPAREN', 1, ')', ')')
        self._test_single_token(0, 'TOK_DONTCARE', 1, '#', '#')

        self._test_single_token(0, 'TOK_TRUE', 1, 'TRUE', 'TRUE')
        self._test_single_token(0, 'TOK_FALSE', 1, 'FALSE', 'FALSE')
        self._test_single_token(0, 'TOK_NULL',1,'NULL','NULL')
        self._test_single_token(0, 'TOK_CB', 1, 'CB', 'CB')
        self._test_single_token(0, 'TOK_CI', 1, 'CI', 'CI')
        self._test_single_token(0, 'TOK_ASSIGN', 1, '=', '=')

        self._test_single_token(0, 'TOK_STRING_LITERAL', 1,
                                '"dita nel naso"',
                                '"dita nel naso"')
        self._test_single_token(0, 'TOK_STRING_LITERAL', 1,
                                '"abc \\" asfds \\""',
                                '"abc \\" asfds \\""')

        # test comment, ignore everything after //
        self._test_single_token(0, 'TOK_ASSIGN', 1, '=', '=//ciao')

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


    def _test_parse(self, spec, same_out=True):
        res = spec_parser.parse(spec)
        self.assertTrue(res is not None)

        # test the printing of the spec ast
        stringio = StringIO()
        pretty_print(res, stringio)
        self.assertTrue((not same_out) or stringio.getvalue() == spec)


    def _test_parse_error(self, specs):
        res = spec_parser.parse(specs)
        self.assertTrue(res is None)

    def test_parser(self):
        correct_expr = ["SPEC [CB] [l] type l() |- [CB] [l] type l(b : type)",
                        "SPEC [CB] [l] type l(l1 : type,l2 : type) |- [CB] [l] type l(b : type)",
                        "SPEC [CB] [l] type l(l1 : type,l2 : type) |- [CI] [l] type l(b : type); SPEC [CB] [l] type l(l1 : type,l2 : type) |- [CI] [l] type l(b : type)",
                        "SPEC ([CB] [l] type l(l1 : type,l2 : type)); ([CB] [l] type l(l1 : type,l2 : type)) |- [CI] [l] type l(b : type)",
                        "SPEC ([CB] [l] type l(l1 : type,l2 : type))[*] |- [CI] [l] type l(b : type)",
                        "SPEC ([CB] [l] type l(l1 : type,l2 : type))[*] |+ [CI] [l] type l(b : type)",
                        "SPEC ([CB] [l] type l(l1 : type,l2 : type))[*] |- [CI] [l] type l(b : type)",
                        "SPEC ([CB] [l] type b(l1 : type,l2 : type))[*] |- [CI] [l] type l(b : type)",
                        "SPEC ([CB] [l] void <init>(l1 : type,l2 : type))[*] |- [CI] [l] type l(b : type)",
                        "SPEC TRUE |- TRUE",
                        "SPEC (TRUE)[*] |- TRUE",
                        "SPEC ([CB] [l] type m1())[*] |- TRUE",
                        "SPEC (((TRUE & FALSE) | ! (FALSE)))[*] |- TRUE",
                        "SPEC [CB] [l1] type methodName(TRUE : boolean) |- [CI] [l2] type methodName(bparam : type,TRUE : boolean)",
                        "SPEC [CB] [l1] type methodName(# : boolean) |- [CI] [l2] type methodName(bparam : type,TRUE : boolean)",
                        "SPEC foo = [CB] [l1] type methodName(# : boolean) |- [CI] [l2] type methodName(bparam : type,TRUE : boolean)",
                        "SPEC (foo = [CB] [l1] type methodName(a : type)); (foo = [CB] [l1] type methodName(a : type)) |- [CI] [l2] type methodName(bparam : type,TRUE : boolean)",
                        "SPEC 1 = [CB] [l1] type methodName(# : boolean) |- [CI] [l2] type methodName(bparam : type,TRUE : boolean)",
                        "SPEC # = [CB] [l1] type methodName(# : boolean) |- [CI] [l2] type methodName(bparam : type,TRUE : boolean)",
                        "SPEC TRUE = [CB] [l1] type methodName(# : boolean) |- [CI] [l2] type methodName(bparam : type,TRUE : boolean)",
                        'SPEC ([CB] [l] type l(l1 : int,"foo" : string))[*] |- [CI] [l] type l(b : type)',
                        "SPEC [CB] [l] type l(NULL : boolean) |- [CB] [l] type l(b : type)",
                        "SPEC [CI] [b] void android.widget.Button.setOnClickListener(l : View.OnClickListener) |+ [CB] [l] void onClick(b : android.widget.Button)",
                        "SPEC ((TRUE)[*]); ([CI] [b] void android.widget.Button.setOnClickListener(l : View.OnClickListener)) |+ [CB] [l] void onClick(b : android.widget.Button)"]

        for expr in correct_expr:
            self._test_parse(expr)

        # do not require the spec read from the parser to be printed
        # and be equal to the input spec
        correct_expr_no_print = ["SPEC [CB] [l] type l() |- [CB] [l] type l(b : type)//foo"]
        for expr in correct_expr_no_print:
            self._test_parse(expr,False)

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
               ("SPEC [CI] [l] void method_name(0 : int,1 : int,f : int) |- TRUE",
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (NIL,), (CI,), (ID,'l'), (ID, 'void method_name'),
                    (PARAM_LIST, (INT, 0), (ID, 'int'),
                     (PARAM_LIST, (INT, 1), (ID, 'int'),
                      (PARAM_LIST, (ID, 'f'), (ID, 'int'), (NIL,))))),
                   (0,))), (NIL,))),
               ("SPEC var = [CI] [l] void method_name(0 : int,1 : int,f : int) |- TRUE",
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (ID,'var'), (CI,), (ID,'l'), (ID, 'void method_name'),
                    (PARAM_LIST, (INT, 0), (ID, 'int'),
                     (PARAM_LIST, (INT, 1), (ID, 'int'),
                      (PARAM_LIST, (ID, 'f'), (ID, 'int'), (NIL,))))),
                   (0,))), (NIL,))),
               ('SPEC var = [CI] [l] void method_name(NULL : string, "foobar" : string, f : int) |- TRUE',
                (SPEC_LIST,
                 (SPEC_SYMB,
                  (DISABLE_OP,
                   (CALL, (ID,'var'), (CI,), (ID,'l'), (ID, 'void method_name'),
                    (PARAM_LIST, (NULL,), (ID, 'string'),
                     (PARAM_LIST, (STRING, '"foobar"'), (ID, 'string'),
                      (PARAM_LIST, (ID, 'f'), (ID, 'int'), (NIL,))))),
                   (0,))), (NIL,)))]

        for r in res:
            test_ast_inner(r[0], r[1])


    def test_spec_creation(self):
        spec_list = Spec.get_specs_from_string("SPEC [CI] [l] void method_name() |- TRUE; " +
                                               "SPEC [CI] [l] void method_name() |- TRUE;" +
                                               "SPEC [CI] [b] void android.widget.Button.setOnClickListener(l : type) |+ [CB] [l] void onClick(b : type);" +
                                               "SPEC TRUE[*]; [CI] [b] void android.widget.Button.setOnClickListener(l : type) |+ [CB] [l] void onClick(b : type)")
        self.assertTrue(len(spec_list) == 4)