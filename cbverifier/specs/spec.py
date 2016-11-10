""" Data structure to represent a specification.

Now we internally represent a specification with its syntax tree and
we provide methods to access its information.

"""

import logging

from cbverifier.specs.spec_parser import spec_parser
from cbverifier.specs.spec_ast import *

class Spec:
    def __init__(self, spec_ast):
        self.spec_ast = spec_ast

    @staticmethod
    def get_specs_from_string(spec_list_string):
        spec_list_ast = spec_parser.parse(spec_list_string)
        if None != spec_list_ast:
            assert get_node_type(spec_list_ast) == SPEC_LIST

            spec_list = []
            while (spec_list_ast != new_nil()):
                spec_ast = spec_list_ast[1]
                assert get_node_type(spec_ast) == SPEC_SYMB
                spec = Spec(spec_ast)
                spec_list.append(spec)

                spec_list_ast = spec_list_ast[2]

            return spec_list

        else:
            return None


