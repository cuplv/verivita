""" Implements the function that ground the free variables contained
in a set of rules given a concrete trace.
"""

import logging
import collections

from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace, CValue

from cbverifier.helpers import Helper


class GroundSpecs(object):
    """ Computes all the ground specifications from the
    specifications with free variables in self.spec and the
    concrete trace self.trace

    Return a list of ground specifications.
    """

    def __init__(self, trace):
        self.trace = trace
        self.trace_map = TraceMap(self.trace)


    def ground_spec(self, spec):
        ground_specs = []

        bindings = self._get_ground_bindings(spec)

        # instantiate the bindings
        for binding in bindings:
            new_spec_ast = GroundSpecs._substitute(spec, binding)
            new_spec = Spec(new_spec_ast)
            ground_specs.append(new_spec)

        return ground_specs

    @staticmethod
    def _substitute(spec, binding):
        # TODO: add memoization

        def substitute_rec(node, binding):
            def wrap_value(binding, varname):
                assert binding.has_key(varname)
                bind = binding.get(varname)

                assert bind is not None

                if (isinstance(bind, CValue)):
                    return new_value(bind)
                else:
                    return bind

            def sub_leaf(leaf, binding):
                """ Given a leaf node, substitute it """

                leaf_type = get_node_type(leaf)

                if (leaf_type == DONTCARE):
                    # Leave the DONTCARE in the node
                    assert leaf is not None
                    return leaf
                elif leaf_type != ID:
                    # LEAVE the constants in the node
                    assert leaf is not None
                    return leaf
                else:
                    # Replace the free variables
                    return wrap_value(binding, leaf)

            def process_param(param_node):
                """ Returns the new list of parameters
                Obtained by instantiating the variables contained in
                the binding.

                Return a PARAM_LIST node
                """

                node_type = get_node_type(param_node)
                if (node_type != PARAM_LIST):
                    assert node_type == NIL
                    return new_nil()
                else:
                    formal_param = param_node[1]
                    formal_param_type = get_node_type(formal_param)
                    if (DONTCARE != formal_param_type):
                        # the binding should be there
                        res = wrap_value(binding, formal_param)
                    else:
                        # leave the DONTCARE node there
                        res = formal_param
                    return new_param(res, process_param(param_node[2]))


            node_type = get_node_type(node)
            if (node_type in leaf_nodes): return node
            elif (node_type == CALL):
                new_params = process_param(get_call_params(node))
                assert new_params is not None

                new_call_node = new_call(sub_leaf(get_call_assignee(node), binding),
                                         get_call_type(node),
                                         sub_leaf(get_call_receiver(node),
                                                  binding),
                                         get_call_method(node),
                                         new_params)
                return new_call_node

            elif (node_type == AND_OP or
                node_type == OR_OP or
                node_type == SEQ_OP or
                node_type == ENABLE_OP or
                node_type == DISABLE_OP or
                node_type == SPEC_LIST):

                lhs = substitute_rec(node[1], binding)
                rhs = substitute_rec(node[2], binding)
                return create_node(node_type, [lhs, rhs])
            elif (node_type == STAR_OP or node_type == NOT_OP):
                lhs = substitute_rec(node[1], binding)
                return create_node(node_type, [lhs])
            elif (node_type == SPEC_SYMB):
                lhs = substitute_rec(node[1], binding)
                return create_node(SPEC_SYMB, [lhs])
            else:
                raise UnexpectedSymbol(node)

        return substitute_rec(spec.ast, binding)

    def _get_ground_bindings(self, spec):
        """ Find all the ground specifications for spec.

        The algorithm proceeds recursively on the structure of the
        formula.

        For each subformula, the algorithm keeps a set of sets of
        assignment to variables.

        The final result is this set of sets of assignments.
        For each set of assignment, we have the instantiation of a
        rule.

        NOW: this is the dumbest possible implementation of the
        grounding.
        Possible improvements:
          - as usual, memoize the results for subformulas (it seems an
          effective strategies)
          - use decision diagram like data structure to share the
        common assignemnts to values.

        """

        all_bindings = AssignmentsSet()
        all_assignments = Assignments()
        all_bindings.add(all_assignments)

        binding_set = self._ground_bindings_rec(spec.ast, all_bindings)
        return binding_set

    def _ground_bindings_rec(self, spec_node, bindings):
        node_type = get_node_type(spec_node)
        if (node_type in leaf_nodes):
            # ground set do not change in these cases
            pass
        elif (node_type == AND_OP or
            node_type == OR_OP or
            node_type == SEQ_OP or
            node_type == ENABLE_OP or
            node_type == DISABLE_OP or
            node_type == SPEC_LIST):
            return self._ground_bindings_rec(spec_node[2],
                                             self._ground_bindings_rec(spec_node[1],
                                                                       bindings))
        elif (node_type == STAR_OP or node_type == NOT_OP or
              node_type == SPEC_SYMB):
            return self._ground_bindings_rec(spec_node[1], bindings)
        elif (node_type == CALL):
            # get the set of all the possible assignments
            # TODO pass bindings to perform directly the
            # product intersection while doing the lookup

            spec_res = self.trace_map.lookup_assignments(spec_node)
            assert spec_res is not None

            # print "\n"
            # print spec_node
            # print spec_res

            res = bindings.combine(spec_res)
            assert res is not None

            # print res
            # print "\n"

            return res
        else:
            raise UnexpectedSymbol(spec_node)

class Assignments(object):
    """ Represent a set of assignments derived from a single
    method call (messasge)"""
    def __init__(self):
        self.assignments = {}
        self._is_bottom = False
        self._is_frozen = False
        self._hash = None
        self.assignments_set = None

    def add(self, variable, value):
        assert variable not in self.assignments
        assert self._is_frozen == False
        self.assignments[variable] = value

    def contains(self, formal, actual):
        try:
            return self.assignments[formal] == actual
        except KeyError:
            return False

    def has_key(self, v):
        return self.assignments.has_key(v)

    def get(self, v):
        return self.assignments[v]

    def is_bottom(self):
        """ Return true if the set of assignments represents the
        empty set """
        return self._is_bottom

    def make_frozen(self):
        """ froze the set, not allowing modifications and making it a
        suitable object to be contained in a set """
        self._is_frozen = True
        self.assignments_set = set()
        for k,v in self.assignments.iteritems():
            self.assignments_set.add((k,v))

    def is_frozen(self):
        return self._is_frozen

    def intersect(self, other):
        """ Note: this is not a standard intersection.
        If a variable assignment does not exist in one of the two
        set, it is still present in the intersection.

        Side effect on the current set
        """
        result = Assignments()

        my_map = self.assignments
        other_map = other.assignments

        if self.is_bottom() or other.is_bottom(): return

        for (key, value) in my_map.iteritems():
            if key in other_map:
                if other_map[key] == value:
                    # add common elements
                    result.add(key, value)
                else:
                    # do not agree on the value for key - no
                    # compatible assignment
                    result._is_bottom = True
                    result.assignments = {} # empty
                    return result
            else:
                result.add(key, value)

        # add the missing elements from other
        for (key, value) in other_map.iteritems():
            if key not in my_map: result.add(key, value)

        assert result.assignments is not None

        return result

    def  __eq__(self, other):
        def _contained(h1, h2):
            eq_hash = True
            for k,v in h1.iteritems():
                try:
                    if (h2[k] != v):
                        eq_hash = False
                        break
                except KeyError:
                    eq_hash = False
                    break
            return eq_hash

        if self.is_frozen() and other.is_frozen():
            assert(self.assignments_set != None)
            assert(other.assignments_set != None)

            eq_bottom = self._is_bottom == other._is_bottom
            eq_sets = self.assignments_set.issubset(other.assignments_set) and self.assignments_set.issuperset(other.assignments_set)

            return (eq_bottom and eq_sets)
        else:
            eq_hash = _contained(self.assignments, other.assignments)
            if eq_hash:
                eq_hash = _contained(other.assignments, self.assignments)
            return (self._is_bottom == other._is_bottom and eq_hash)


    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        rep = "["

        first = True
        for pair in self.assignments.iteritems():
            if not first:
                rep += ","
            rep += "[%s := %s]" % pair
            first = False

        rep += "]"
        return rep


    def __hash__(self):
        # provide a has to the object
        if self._hash is None:
            self._hash = 0
            for pair in self.assignments.iteritems():
                self._hash ^= hash(pair)

        return self._hash


class AssignmentsSet(object):
    """ Represent a set of assignments (or bindings) from free
    variables to actual values derived from a set of concrete
    method calls.
    """
    def __init__(self):
        self.assignments = set()
        self._iter = None

    def add(self, assignments):
        """ Add an assignment to the set of assignments.

        Assignment is a map from variables to values.
        """
        # Froze the assignments, otherwise we cannot use it in a set
        assignments.make_frozen()
        self.assignments.add(assignments)

    def __iter__(self):
        self._iter = self.assignments.__iter__()
        return self._iter

    def __next__(self):
        return self._iter.next()

    def combine(self, other):
        """ Given another assignment set, computes the intersection
        of all the assignments in set and all the assignments in
        other.

        The method returns a new AssignmentSet
        """
        result = AssignmentsSet()
        result.assignments = set()

        for assignments in self.assignments:
            for assignments_other in other.assignments:

                new_a = assignments.intersect(assignments_other)

                # Do not add bottom to the set.
                # If the set is empty, then there are no assignments
                # that are compatible with the rule.
                if not new_a.is_bottom():
                    result.add(new_a)

        return result

    def  __eq__(self, other):
        return (self.assignments.issubset(other.assignments) and
                self.assignments.issuperset(other.assignments))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        rep = "AssignmentsSet\n{\n"
        for a in self.assignments:
            rep += "  %s,\n" % str(a)
        rep +="}"
        return rep

class TraceMap(object):
    """ Given a trace, builds an index of the methods called in the
    trace (messages).

    The index is organized in two levels: the first level is the name of
    the method, the second level is the arity of the method.


    The class also implements a lookup methods.

    lookup_methods: given the name of a method and its arity, return
    the set of method calls in the trace that call that specific
    method with the given arity.

    lookup_assignments: given a call_node from the specification AST
    the method reutrns all the possible assignments to the free
    variables in the AST node that can be built by looking at the
    method calls found in the trace.
    """

    def __init__(self, trace):
        # 2-level index with method name and arity of paramters
        self.trace_map = {}
        for child in trace.children:
            self.trace_map = self._fill_map(child, self.trace_map)

    def _fill_map(self, msg, trace_map):
        """ Given a message from the trace fill and a map
        Creates the 2-level index formed by the message name,
        and then the arity of the message to a list of messages.
        """

        arity_map = None
        try:
            arity_map = trace_map[msg.method_name]
        except KeyError:
            arity_map = {}
            trace_map[msg.method_name] = arity_map

        arity = len(msg.params)

        method_list = None
        try:
            method_list = arity_map[arity]
        except KeyError:
            method_list = []
            arity_map[arity] = method_list
        method_list.append(msg)

        for child in msg.children:
            trace_map = self._fill_map(child, trace_map)

        return trace_map

    def lookup_methods(self, method_name, arity):
        """ Given the name of a method and its arity, returns the
        list of messages in the trace that
        match the method name and have the same number of
        parameters,
        """
        method_list = []
        try:
            arity_map = self.trace_map[method_name]
            method_list = arity_map[arity]
        except KeyError:
            pass
        return method_list

    def lookup_assignments(self, call_node):
        """ Given a node that represent a call in a specification,
        returns the set of all the assignments from free variables
        in the call node to concrete values found in the trace.

        The method returns an AssignmentsSet object.
        """
        assert (get_node_type(call_node) == CALL)

        set_assignments = AssignmentsSet()

        try:
            # Build the list of formal parameters
            # (CALL, receiver, method_name, params)
            method_name_node = get_call_method(call_node)
            method_name = get_id_val(method_name_node)
            receiver = get_call_receiver(call_node)
            params = get_call_params(call_node)
            param_list = []

            if (get_node_type(receiver) != NIL):
                param_list.append(receiver)
            while (get_node_type(params) == PARAM_LIST):
                param_list.append(params[1])
                params = params[2]
            arity = len(param_list)

            matching_methods = self.lookup_methods(method_name, arity)

            # For each method, find the assignments to the variables in params
            for method in matching_methods:
                match = True
                method_assignments = Assignments()
                for formal, actual in zip(param_list, method.params):
                    formal_type = get_node_type(formal)

                    assert formal_type in leaf_nodes
                    assert formal_type != NIL

                    if (formal_type == DONTCARE):
                        continue
                    elif (formal_type in const_nodes):
                        # if the constant nodes do not match, do not consider
                        # this as a binding
                        # this is an optimization, it does not create bindings
                        # that we do not need
                        if str(formal[1]) != actual:
                            match = False
                            break
                    elif method_assignments.has_key(formal):
                        assert formal_type == ID
                        if method_assignments.contains(formal, actual):
                            # we have two different assignments
                            # for the same free variable
                            # remove the match
                            match = False
                            break
                    else:
                        assert formal_type == ID
                        method_assignments.add(formal, actual)

                if match:
                    set_assignments.add(method_assignments)

            return set_assignments

        except KeyError:
            return set_assignments

