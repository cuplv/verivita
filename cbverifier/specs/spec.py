""" Data structure to represent a specification.

Now we internally represent a specification with its syntax tree and
we provide methods to access its information.

"""

import logging

from cbverifier.specs.spec_lex import lexer
from cbverifier.specs.spec_lex import tokens
from cbverifier.specs.spec_parser import spec_parser


class Spec:
    def __init__(self, syntax_tree):
        self.syntax_tree





