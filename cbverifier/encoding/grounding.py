
""" Implements the function that ground the free variables contained
in a set of rules given a concrete trace.
"""

import logging
import collections

from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback

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
        self.ground_to_spec = {}


    def ground_spec(self, spec):
        ground_specs = []

        bindings = self._get_ground_bindings(spec)

        # instantiate the bindings
        for binding in bindings:
            new_spec_ast = GroundSpecs._substitute(spec, binding)
            new_spec = Spec(new_spec_ast)
            ground_specs.append(new_spec)

            self.ground_to_spec[new_spec] = spec

        return ground_specs

    @staticmethod
    def _substitute(spec, binding):
        # TODO: add memoization

        def substitute_rec(node, binding):

            def replace_consts(node):
                assert isinstance(node, tuple)
                assert len(node) > 0

                node_type = get_node_type(node)
                if (node_type == TRUE):
                    return new_id("TRUE")
                elif (node_type == FALSE):
                    return new_id("FALSE")
                elif (node_type == NULL):
                    return new_id("NULL")
                elif (node_type == NIL):
                    return node
                elif (node_type == ID):
                    return node
                elif (node_type == STRING or
                      node_type == INT or
                      node_type == FLOAT):
                    return new_id(get_id_val(node))
                else:
                    return None

            def wrap_value(binding, varname):
                assert binding.has_key(varname)
                bind = binding.get(varname)

                assert bind is not None

                # unpack the different types of values in a string
                # (an id at the end)
                if (isinstance(bind, CValue)):
                    return new_id(bind.get_value())
                elif (isinstance(bind, tuple)):
                    ret_val = replace_consts(bind)
                    assert ret_val is not None
                    return ret_val

            def sub_leaf(leaf, binding):
                """ Given a leaf node, substitute it """

                leaf_type = get_node_type(leaf)

                if (leaf_type == DONTCARE):
                    # Leave the DONTCARE in the node
                    assert leaf is not None
                    return leaf
                elif (leaf_type == ID):
                    # Replace the free variables
                    return wrap_value(binding, leaf)
                else:
                    ret_val = replace_consts(leaf)
                    assert ret_val is not None
                    return ret_val

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
                    formal_param = get_param_name(param_node)
                    p_type = get_param_type(param_node)
                    res = sub_leaf(formal_param, binding)
                    return new_param(res, p_type,
                                     process_param(get_param_tail(param_node)))

            node_type = get_node_type(node)
            if (node_type in leaf_nodes): return node
            elif (node_type == CALL):
                new_params = process_param(get_call_params(node))
                assert new_params is not None

                new_call_node = new_call(sub_leaf(get_call_assignee(node),
                                                  binding),
                                         get_call_type(node),
                                         sub_leaf(get_call_receiver(node),
                                                  binding),
                                         sub_leaf(get_call_method(node), binding),
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

    def get_source_spec(self, ground_spec):
        if ground_spec not in self.ground_to_spec:
            return None
        else:
            return self.ground_to_spec[ground_spec]

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

    The index is organized in levels:
      - the type of the call (callin or callback)
      - the name of the method
      - the arity of the method
      - if the method returns a value

    The class implements two lookup functions.

    1. lookup_methods: given the type, name, arity, and
    it there is a return value of a method,
    returns the set of method calls in the trace that call that specific
    method with the given arity.

    2. lookup_assignments: given a call_node from the specification AST
    the method returns all the possible assignments to the free
    variables in the AST node that can be built by looking at the
    method calls found in the trace.
    """

    def __init__(self, trace):
        # 3-level index with method name and arity of paramters
        self.trace_map = {}
        for child in trace.children:
            self.trace_map = self._fill_map(child, self.trace_map)

    def _get_inner_elem(self, hash_map, key, default=None):
        assert (type(hash_map) == type({}))

        try:
            inner_element = hash_map[key]
        except KeyError:
            if (default is None):
                inner_element = {}
            else:
                inner_element = default
            hash_map[key] = inner_element

        return inner_element

    def _lookup_inner_elem(self, hash_map, key):
        inner_elem = None
        try:
            inner_elem = hash_map[key]
        except KeyError:
            pass
        return inner_elem

    def _fill_map(self, msg, trace_map):
        """ Given a message from the trace fill and a map
        Creates the 2-level index formed by the message name,
        and then the arity of the message to a list of messages.
        """
        if (isinstance(msg, CCallin)):
            msg_type = CI
        elif (isinstance(msg, CCallback)):
            msg_type = CB
        else:
            assert False
        has_retval = msg.return_value is not None

        message_name_map = self._get_inner_elem(trace_map, msg_type)
        assert (type(message_name_map) == type({}))

        # We insert the same method multiple times in the case of callbacks.
        #
        # In practice we insert in the index all the possible variants that may
        # match a rule, due to implemented interfaces and classes
        method_names = []
        if (isinstance(msg, CCallin)):
            method_name = msg.get_full_msg_name()

            method_names.append(method_name)
        elif (isinstance(msg, CCallback)):
            # for callbacks we look at the framework types

            first_fmwk_type = True

            for override in msg.fmwk_overrides:
                assert override is not None
                # Note: method names may change in the overriden methods due
                # to generics
                if (not override.is_interface):
                    if (first_fmwk_type):
                        # first class
                        method_name = override.get_full_msg_name()
                        method_names.append(method_name)
                        first_fmwk_type = False
                else:
                    method_name = override.get_full_msg_name()
                    method_names.append(method_name)
        else:
            assert False


        for method_name in method_names:
            arity_map = self._get_inner_elem(message_name_map, method_name)
            assert (type(arity_map) == type({}))
            ret_val_map = self._get_inner_elem(arity_map, len(msg.params))
            assert (type(ret_val_map) == type({}))
            method_list = []
            method_list = self._get_inner_elem(ret_val_map, has_retval, method_list)
            assert (type(method_list) == type([]))
            method_list.append(msg)

        for child in msg.children:
            trace_map = self._fill_map(child, trace_map)

        return trace_map

    def lookup_methods(self, msg_type_node, method_name, arity, has_retval):
        """ Given the name of a method and its arity, returns the
        list of messages in the trace that
        match the method name and have the same number of
        parameters,
        """
        method_list = []


        msg_type = get_node_type(msg_type_node)
        keys = [msg_type, method_name, arity, has_retval]
        current_map = self.trace_map

        key_index = 0
        for key in keys:
            lookupres = self._lookup_inner_elem(current_map, key)

            if key_index == len(keys) - 1:
                # last element
                if lookupres is None:
                    break
                else:
                    method_list = lookupres
            else:
                key_index += 1
                # exit the loop if the element was not found
                if lookupres is None:
                    break
                else:
                    current_map = lookupres

        return method_list

    def _get_formal_assignment(self, method_assignments, formal, actual):
        """ Add the assignement to formal given by actual """
        formal_type = get_node_type(formal)

        assert formal_type in leaf_nodes
        assert formal_type != NIL

        match = True

        if (formal_type == DONTCARE):
            return match
        elif (formal_type in const_nodes):
            # if the constant nodes do not match, do not consider
            # this as a binding
            # this is an optimization, it does not create bindings
            # that we do not need
            assert isinstance(actual, CValue)
            if str(formal[1]) != str(actual.get_value()):
                match = False
                return match
        elif method_assignments.has_key(formal):
            assert formal_type == ID
            if method_assignments.contains(formal, actual):
                # we have two different assignments
                # for the same free variable
                # remove the match
                match = False
                return match
        else:
            assert formal_type == ID
            method_assignments.add(formal, actual)

        return match

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
            # (CALL, retval, call_type, receiver, method_name, params)
            retval = get_call_assignee(call_node)
            call_type = get_call_type(call_node)
            method_name_node = get_call_method(call_node)
            # method_name = get_id_val(method_name_node)
            method_signature = get_id_val(get_call_signature(call_node))
            receiver = get_call_receiver(call_node)
            params = get_call_params(call_node)
            param_list = []

            if (get_node_type(receiver) != NIL):
                param_list.append(receiver)
            else:
                # we require to always have the receiver in the trace
                #
                # if there are no receiver in the spec, the correspondent receiver
                # in the trace should be the NULL value
                #
                param_list.append(new_null())

            while (get_node_type(params) == PARAM_LIST):
                param_list.append(get_param_name(params))
                params = get_param_tail(params)
            arity = len(param_list)

            matching_methods = self.lookup_methods(call_type, method_signature,
                                                   arity,
                                                   retval != new_nil())
            # For each method, find:
            #   - the assignments to the variables in params
            #   - the assignment to the return value
            for method in matching_methods:
                match = True
                method_assignments = Assignments()

                # Replace the name of the atom in the call with the concrete name
                # of the method that was matched.
                method_assignments.add(method_name_node,
                                       new_id(method.get_msg_no_params()))

                # parameters
                for formal, actual in zip(param_list, method.params):
                    match = self._get_formal_assignment(method_assignments,
                                                        formal, actual)
                    if not match:
                        break

                # return value
                if match and retval != new_nil():
                    match = self._get_formal_assignment(method_assignments,
                                                        retval,
                                                        method.return_value)

                if match:
                    set_assignments.add(method_assignments)

            return set_assignments

        except KeyError:
            return set_assignments

