""" Data structure to represent a specification.

Now we internally represent a specification with its syntax tree and
we provide methods to access its information.

"""

import logging

from cbverifier.specs.spec_parser import spec_parser
from cbverifier.specs.spec_ast import *
from cStringIO import StringIO

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

    # TODO: replace ALIASES
    @staticmethod
    def _solve_aliases(spec_ast):
        def alias_rec(aliases_list, subs_map, aliased_specs):
            if len(aliases_list) == 0:
                aliased_spec = subs_alias(spec_ast, subs_map)
                aliased_specs.append(aliased_spec)
            else:
                copy = list(aliases_list)
                (old, new_list)  = copy.pop()

                for new in new_list:
                    new_subs_map = subs_map.copy()
                    new_subs_map[old] = new
                    alias_rec(copy, new_subs_map, aliased_specs)

        aliases = get_spec_aliases(spec_ast)

        if new_nil() == aliases:
            return [spec_ast]

        # collect all the aliases in a list
        aliases_list = []
        while new_nil() != aliases:
            old = get_alias_old(aliases)
            new_list = get_alias_new(aliases)
            aliases_list.append((old, new_list))
            aliases = get_alias_tail(aliases)

        aliased_specs = []
        alias_rec(aliases_list, {}, aliased_specs)

        return aliased_specs


    @staticmethod
    def get_specs_from_string(spec_list_string, spec_list=None):
        spec_list_ast = spec_parser.parse(spec_list_string)
        if None != spec_list_ast:
            assert get_node_type(spec_list_ast) == SPEC_LIST

            if spec_list is None: spec_list = []
            while (spec_list_ast != new_nil()):
                spec_ast = spec_list_ast[1]
                assert get_node_type(spec_ast) == SPEC_SYMB

                # Process all the aliases
                for spec_ast_2 in Spec._solve_aliases(spec_ast):
                    spec = Spec(spec_ast_2)
                    spec_list.append(spec)

                spec_list_ast = spec_list_ast[2]

            return spec_list

        else:
            return None

    @staticmethod
    def get_spec_from_string(spec_string):
        spec_list = []
        spec_list = Spec.get_specs_from_string(spec_string, spec_list)
        return spec_list

    @staticmethod
    def get_specs_from_file(spec_file, spec_list=None):
        with open(spec_file, "r") as f:
            data = f.read()
            spec_list = Spec.get_specs_from_string(data,spec_list)
            f.close()
        return spec_list

    @staticmethod
    def get_specs_from_files(files_list, spec_list=None):
        assert type(files_list) == list
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

    def get_spec_calls(self):
        """ Returns a set of all the call atoms used in the spec """
        return get_call_nodes(self.ast)

    def __repr__(self):
        stringio = StringIO()
        self.print_spec(stringio)
        return stringio.getvalue()


    def  __hash__(self):
        return hash(self.ast)

    def  __eq__(self, other):
        return self.ast == other.ast
