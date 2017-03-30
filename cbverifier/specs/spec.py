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

    @staticmethod
    def _solve_aliases(spec_ast):
        """ Given a specification creates n specification, one
        for each possible instantiation of the aliases"""
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
    def _solve_named_regexp(list_of_list_of_spec_asts):
        """ substitute each named regexp inside a specification """
        res_spec_ast = []

        # build a map of named regexp
        # (name, arity) -> regexp
        named_regexp_map = {}
        spec_ast_list = []
        for iter_list_of_specs in list_of_list_of_spec_asts:
            while (iter_list_of_specs != new_nil()):
                spec_ast = iter_list_of_specs[1]
                if (get_node_type(spec_ast) == SPEC_SYMB):
                    spec_ast_list.append(spec_ast)
                elif (get_node_type(spec_ast) == NAMED_REGEXP):
                    rid = get_named_regexp_id(spec_ast)
                    rvars = get_named_regexp_vars(spec_ast)
                    named_regexp_map[(rid,len(rvars))] = spec_ast

                iter_list_of_specs = iter_list_of_specs[2]

        for spec_ast in spec_ast_list:
            # bv = get_bound_vars(spec_ast)
            # replaced_ast = subs_named_regexp_inst(spec_ast, bv)
            replaced_ast = spec_ast
            res_spec_ast.append(replaced_ast)

        return res_spec_ast

    @staticmethod
    def process_ast_list(list_spec_asts):
        # 1. Instantiate all the named regular expression
        spec_list = []
        solved_spec_list = Spec._solve_named_regexp(list_spec_asts)

        for spec_ast in solved_spec_list:
            # 2. Instantiate the specifications for each possible alias combination
            for spec_ast_2 in Spec._solve_aliases(spec_ast):
                spec = Spec(spec_ast_2)
                spec_list.append(spec)

        return spec_list

    @staticmethod
    def get_specs_from_string(spec_list_string, spec_list=None):
        spec_list_ast = spec_parser.parse(spec_list_string)

        if None != spec_list_ast:
            return Spec.process_ast_list([spec_list_ast])
        else:
            return None

    @staticmethod
    def get_spec_from_string(spec_string):
        spec_list = []
        spec_list = Spec.get_specs_from_string(spec_string, spec_list)
        return spec_list

    @staticmethod
    def get_specs_from_file(spec_file):
        return get_specs_from_files([spec_file])

    @staticmethod
    def get_specs_from_files(files_list):
        assert type(files_list) == list

        spec_ast_list = []

        # parse all the files
        for spec_file in files_list:
            with open(spec_file, "r") as f:
                data = f.read()
                spec_ast = spec_parser.parse(data)
                # Fail if at least one spec file fails
                if spec_ast == None:
                    logging.error("Error parsing the specification " \
                                  "file %s" % spec_file)
                    return None
                spec_ast_list.append(spec_ast)

        # process all the specs
        spec_list = Spec.process_ast_list(spec_ast_list)

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
