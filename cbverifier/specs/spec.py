""" Data structure to represent a specification.

Now we internally represent a specification with its syntax tree and
we provide methods to access its information.

"""

import logging

from cbverifier.specs.spec_parser import spec_parser
from cbverifier.specs.spec_ast import *

class Spec:
    def __init__(self, spec_ast):
        self.ast = spec_ast

    # TODO: we need to fill the spec with fields and methods from the AST
    #
    # The implementation depends on what we have to do in the verification
    # algorithm
    #

    # TODO: do we need to typecheck the specifications?

    def print_spec(self, stream):
        pretty_print(self.ast, stream)

    def is_disable(self):
        return is_spec_disable(self.ast)

    def is_enable(self):
        return is_spec_enable(self.ast)

    @staticmethod
    def get_specs_from_string(spec_list_string, spec_list=None):
        spec_list_ast = spec_parser.parse(spec_list_string)
        if None != spec_list_ast:
            assert get_node_type(spec_list_ast) == SPEC_LIST

            if spec_list is None: spec_list = []
            while (spec_list_ast != new_nil()):
                spec_ast = spec_list_ast[1]
                assert get_node_type(spec_ast) == SPEC_SYMB
                spec = Spec(spec_ast)
                spec_list.append(spec)

                spec_list_ast = spec_list_ast[2]

            return spec_list

        else:
            return None

    @staticmethod
    def get_spec_from_string(spec_string):
        spec_list = []
        spec_list = Spec.get_specs_from_string(spec_string, spec_list)
        return spec_list[0]

    @staticmethod
    def get_specs_from_file(spec_file, spec_list=None):
        with open(spec_file, "r") as f:
            data = f.read()
            spec_list = Spec.get_specs_from_string(data,spec_list)
            f.close()
        return spec_list

    @staticmethod
    def get_specs_from_files(files_list, spec_list=None):
        for spec_file in files_list:
            spec_list = Spec.get_specs_from_file(spec_file, spec_list)

            # Fail if at least one spec file fails
            if spec_list == None:
                logging.error("Error parsing the specification " \
                              "file %s" % spec_file)

                return None

        return spec_list

    def is_spec_rhs_false(self):
        """ Note: the check is just syntactic on the constant FALSE """
        spec_rhs = get_spec_rhs(self.ast)
        return get_node_type(spec_rhs) == FALSE

    def is_regexp_false(self):
        """ Note: the check is just syntactic on the constant FALSE """
        spec_regexp = get_regexp_node(self.ast)
        return get_node_type(spec_regexp) == FALSE
