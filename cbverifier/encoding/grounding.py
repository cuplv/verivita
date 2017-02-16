
""" Implements the function that ground the free variables contained
in a set of rules given a concrete trace.

TODO:

TraceMap:
  - cache the result (assignment set) for a given method call
  - represent sets of messages with the same assignments for a given method call
    in the same assignment (the splitting is necessary if there are different
    assignments)
    This allows for a more compact representation, and hence possibly less
    grounded specifications
"""

import logging
import collections

from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback
from cbverifier.encoding.conversion import TraceSpecConverter
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

            # skip the false specification on the rhs
            if (not new_spec.is_spec_rhs_false()):
                # optimization: skip the spec if the regexp is false:
                if (not new_spec.is_regexp_false()):
                    ground_specs.append(new_spec)
                    self.ground_to_spec[new_spec] = spec

        return ground_specs

    @staticmethod
    def _substitute(spec, binding):
        # TODO: add memoization

        def substitute_rec(node, binding):

            def has_binding(leaf, binding):
                """ Given a leaf node, substitute it """

                leaf_type = get_node_type(leaf)

                if (leaf_type == DONTCARE):
                    # Leave the DONTCARE in the node
                    return True
                elif (leaf_type == ID):
                    # Replace the free variables
                    if binding.has_key(leaf):
                        bind_value = binding.get(leaf)
                        return bind_value != bottom_value
                else:
                    # constant
                    return True

            def check_param_bindings(param_node, binding):
                """ Check that all the parameters have a binding.
                """
                all_bind = True

                node_type = get_node_type(param_node)
                if (node_type == PARAM_LIST):
                    formal_param = get_param_name(param_node)
                    p_type = get_param_type(param_node)
                    res = has_binding(formal_param, binding)
                    assert res is not None

                    return (res and
                            check_param_bindings(get_param_tail(param_node), binding))
                else:
                    assert node_type == NIL
                    return True

            def get_param_types_list(node):
                types_list = []
                app = node
                while (get_node_type(app) == PARAM_LIST):
                    types_list.append(get_param_type(app))
                    app = get_param_tail(app)
                return types_list

            node_type = get_node_type(node)
            if (node_type in leaf_nodes): return node
            elif (node_type == CALL_ENTRY or node_type == CALL_EXIT):
                is_entry = True if node_type == CALL_ENTRY else False

                # not found any message that can match the call
                if not binding.has_key((is_entry, node)):
                    return new_false()

                call_message = binding.get((is_entry,node))
                if bottom_value == call_message:
                    return new_false()

                # reconstruct the call node,
                # finding the assignments to the free variables
                #
                # At this point we may have that a free variable is
                # assigned to bottom. In that case, we did not find a
                # message that can be substituted to this call and
                # thus we replace it with false
                #
                no_bind_assignee = (not is_entry) and (not has_binding(get_call_assignee(node), binding))
                if (not check_param_bindings(get_call_params(node), binding) or
                    no_bind_assignee or
                    not has_binding(get_call_receiver(node), binding)):
                    # when the instantiation fails we replace the call node with
                    # false
                    new_call_node = new_false()
                else:
                    param_types = get_param_types_list(get_call_params(node))
                    new_call_node = GroundSpecs._msg_to_call_node(is_entry, call_message, param_types)
                return new_call_node

            elif (node_type == AND_OP):
                lhs = substitute_rec(node[1], binding)
                rhs = substitute_rec(node[2], binding)

                if (get_node_type(lhs) == FALSE or
                    get_node_type(lhs) == FALSE):
                    return new_false()
                elif (get_node_type(lhs) == TRUE):
                    return rhs
                elif (get_node_type(rhs) == TRUE):
                    return lhs
                else:
                    return create_node(node_type, [lhs, rhs])

            elif (node_type == OR_OP):
                lhs = substitute_rec(node[1], binding)
                rhs = substitute_rec(node[2], binding)

                if (get_node_type(lhs) == TRUE or
                    get_node_type(lhs) == TRUE):
                    return new_true()
                elif (get_node_type(lhs) == FALSE):
                    return rhs
                elif (get_node_type(rhs) == FALSE):
                    return lhs
                else:
                    return create_node(node_type, [lhs, rhs])

            elif (node_type == SEQ_OP or
                  node_type == ENABLE_OP or
                  node_type == DISABLE_OP or
                  node_type == SPEC_LIST):
                lhs = substitute_rec(node[1], binding)
                rhs = substitute_rec(node[2], binding)
                return create_node(node_type, [lhs, rhs])

            elif (node_type == NOT_OP):
                lhs = substitute_rec(node[1], binding)

                if (get_node_type(lhs) == FALSE):
                    return new_true()
                elif (get_node_type(lhs) == TRUE):
                    return new_false()
                else:
                    return create_node(node_type, [lhs])

            elif (node_type == STAR_OP):
                lhs = substitute_rec(node[1], binding)
                return create_node(node_type, [lhs])
            elif (node_type == SPEC_SYMB):
                lhs = substitute_rec(node[1], binding)
                return create_node(SPEC_SYMB, [lhs])
            else:
                raise UnexpectedSymbol(node)

        new_spec_ast = substitute_rec(spec.ast, binding)

        return new_spec_ast

    @staticmethod
    def _msg_to_call_node(is_entry, msg, param_types):
        """ Builds a call node from a message.

        is_entry determines if the call node must be an entry or an exit node.
        """
        if (is_entry or msg.return_value is None):
            new_assignee = new_nil()
        else:
            new_assignee = TraceSpecConverter.traceval2specnode(msg.return_value)

        if (isinstance(msg, CCallback)):
            call_type = new_cb()
        else:
            assert isinstance(msg, CCallin)
            call_type = new_ci()

        receiver_msg = msg.get_receiver()
        if receiver_msg is None:
            new_receiver = new_nil()
        else:
            new_receiver = TraceSpecConverter.traceval2specnode(receiver_msg)

        # rebuild the params
        msg_params = msg.get_other_params()
        assert (len(param_types) == len(msg_params))
        new_params_stack = []
        for (p,t) in zip(msg_params, param_types):
            new_p = TraceSpecConverter.traceval2specnode(p)
            new_params_stack.append((new_p, t))
        call_param_list = new_nil()
        while len(new_params_stack) != 0:
            p = new_params_stack.pop()
            (new_p, t) = p
            call_param_list = new_param(new_p, t, call_param_list)

        new_call_method = new_id(msg.get_msg_no_params())

        if (is_entry):
            call_node = new_call_entry(call_type,
                                       new_receiver,
                                       new_call_method,
                                       call_param_list)
        else:
            call_node = new_call_exit(new_assignee,
                                      call_type,
                                      new_receiver,
                                      new_call_method,
                                      call_param_list)
        return call_node

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
        assert bindings is not None
        node_type = get_node_type(spec_node)
        if (node_type in leaf_nodes):
            # ground set do not change in these cases
            return bindings
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
        elif (node_type == CALL_ENTRY or node_type == CALL_EXIT):
            # get the set of all the possible assignments
            # TODO pass bindings to perform directly the
            # product intersection while doing the lookup

            spec_res = self.trace_map.lookup_assignments(spec_node)
            assert spec_res is not None

            res = bindings.combine(spec_res)
            assert res is not None

            return res
        else:
            raise UnexpectedSymbol(spec_node)

    def get_source_spec(self, ground_spec):
        if ground_spec not in self.ground_to_spec:
            return None
        else:
            return self.ground_to_spec[ground_spec]


class AssignmentsBottom(object):
    """ Object used to represent the bottom value inside Assignemnts """

# global variable to be used as bottom
bottom_value = AssignmentsBottom()

class Assignments(object):
    """ Represent a set of assignments derived from a single
    method call (messasge)

    Implicitly all the variables are assigned to top.

    The set can assign bottom to some variables.
    """
    def __init__(self):
        self.assignments = {}
        self._is_frozen = False
        self._hash = None
        self.assignments_set = None

    def add(self, variable, value, reassign=False):
        assert reassign or variable not in self.assignments
        assert self._is_frozen == False
        assert type(value) != list
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

        for (key, value) in my_map.iteritems():
            if key in other_map:
                if other_map[key] == value:
                    # add common elements
                    result.add(key, value)
                else:
                    # do not agree on the value for key - no
                    # compatible assignment
                    result.add(key, bottom_value)
            else:
                # assume that value for key in my_map
                # to be Top
                result.add(key, value)

        # add the missing elements from other
        for (key, value) in other_map.iteritems():
            if key not in my_map:
                # assume that value for key in my_map
                # to be Top
                result.add(key, value)

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

            eq_sets = (self.assignments_set.issubset(other.assignments_set) and
                       self.assignments_set.issuperset(other.assignments_set))

            return eq_sets
        else:
            eq_hash = _contained(self.assignments, other.assignments)
            if eq_hash:
                eq_hash = _contained(other.assignments, self.assignments)
            return eq_hash


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
      - the type of the method (entry/exit)
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

    ENTRY_TYPE = "ENTRY"
    EXIT_TYPE = "EXIT"

    def __init__(self, trace):
        # 3-level index with method name and arity of paramters
        self.trace_map = {}
        for child in trace.children:
            self.trace_map = self._fill_map(child, self.trace_map)

        # if (logging.getLogger().getEffectiveLevel() == logging.DEBUG):
        #     logging.debug("--- Trace map --- ")
        #     logging.debug(str(self.trace_map))


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
        Creates the n-level index.
        """
        if (isinstance(msg, CCallin)):
            msg_type = CI
        elif (isinstance(msg, CCallback)):
            msg_type = CB
        else:
            assert False

        # 1. Type of the message
        message_name_map = self._get_inner_elem(trace_map, msg_type)
        assert (type(message_name_map) == type({}))

        # We insert the same method multiple times in the case of callbacks.
        #
        # In practice we insert in the index all the possible variants that may
        # match a rule, due to implemented interfaces and classes
        #
        # 2. Name of the method
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


        has_retval = msg.return_value is not None
        for method_name in method_names:
            # Arity of the method
            arity_map = self._get_inner_elem(message_name_map, method_name)
            assert (type(arity_map) == type({}))

            # Type (entry/exit)
            entry_map = self._get_inner_elem(arity_map, len(msg.params))
            assert (type(entry_map) == type({}))

            # Process ENTRY
            ret_val_map = self._get_inner_elem(entry_map, TraceMap.ENTRY_TYPE)
            assert (type(ret_val_map) == type({}))
            method_list = []
            # An entry does not have a return value
            method_list = self._get_inner_elem(ret_val_map, False, method_list)
            assert (type(method_list) == type([]))
            method_list.append(msg)

            ret_val_map = self._get_inner_elem(entry_map, TraceMap.EXIT_TYPE)
            assert (type(ret_val_map) == type({}))
            method_list = []
            method_list = self._get_inner_elem(ret_val_map, has_retval, method_list)
            assert (type(method_list) == type([]))
            method_list.append(msg)

        for child in msg.children:
            trace_map = self._fill_map(child, trace_map)

        return trace_map

    def lookup_methods(self, is_entry, msg_type_node, method_name, arity, has_retval):
        """ Find all the messages in the trace that match the above signature:
          - is_entry (entry or exit message)
          - msg_type_node (CI or CB)
          - method_name
          - aritity
          - has_retval
        """
        assert ((not has_retval) or (not is_entry))

        method_list = []

        msg_type = get_node_type(msg_type_node)
        entry_val = TraceMap.ENTRY_TYPE if is_entry else TraceMap.EXIT_TYPE
        keys = [msg_type, method_name, arity, entry_val, has_retval]
        current_map = self.trace_map

        key_index = 0
        for key in keys:
            lookupres = self._lookup_inner_elem(current_map, key)

            if key_index == len(keys) - 1:
                # last element
                if lookupres is None:
                    break
                else:
                    key_index = key_index + 1
                    method_list = lookupres
            else:
                key_index += 1
                # exit the loop if the element was not found
                if lookupres is None:
                    break
                else:
                    current_map = lookupres

        if (logging.getLogger().getEffectiveLevel() == logging.DEBUG):
            # find where the lookup got stuck
            if key_index == 0:
                stop_lookup = "message type"
            elif key_index == 1:
                stop_lookup = "method_name"
            elif key_index == 2:
                stop_lookup = "arity"
            elif key_index == 3:
                stop_lookup = "entry type"
            elif key_index == 4:
                stop_lookup = "return value"
            elif key_index == 5:
                stop_lookup = None

            logging.debug("Lookup %s for %s" \
                          "%s %s %s with arity %d: %s"
                          % ("succeded" if stop_lookup is None else "failed",
                             "retval = " if has_retval else "",
                             msg_type_node,
                             "ENTRY" if is_entry else "EXIT",
                             method_name,
                             arity,
                             ",".join([str(m.message_id) for m in method_list])))
        return method_list

    def _get_formal_assignment(self, method_assignments, formal, actual):
        """ Add the assignement to formal given by actual """
        formal_type = get_node_type(formal)

        assert formal_type in leaf_nodes
        assert formal_type != NIL

        if (formal_type == DONTCARE):
            return True
        elif (formal_type == ID and method_assignments.has_key(formal)):
            if not method_assignments.contains(formal, actual):
                # Formal is already in the assignment
                # the pair (formal, actual) is not
                # Hence, the value already inserted for formal is
                # different from actual
                #
                # We have a mismatch, hence we assign the
                # bottom value
                method_assignments.add(formal, bottom_value, True)
                return False
            else:
                return True
        elif (formal_type == ID):
            method_assignments.add(formal, actual)
            return True
        elif (TraceSpecConverter.traceval2specnode(actual) == formal):
            # constants
            return True
        else:
            return False

    def lookup_assignments(self, call_node):
        """ Given a node that represent a call in a specification,
        returns the set of all the assignments from free variables
        in the call node to concrete values found in the trace.

        The method returns an AssignmentsSet object.
        """
        node_type = get_node_type(call_node)
        assert (node_type == CALL_ENTRY or
                node_type == CALL_EXIT)

        set_assignments = AssignmentsSet()

        # Build the list of formal parameters
        if (node_type == CALL_EXIT):
            is_entry = False
            retval = get_call_assignee(call_node)
        else:
            assert node_type == CALL_ENTRY
            is_entry = True
            retval = None

        call_type = get_call_type(call_node)
        method_name_node = get_call_method(call_node)
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

        matching_methods = self.lookup_methods(is_entry,
                                               call_type,
                                               method_signature,
                                               arity,
                                               (retval is not None) and (retval != new_nil()))
        # For each method, find:
        #   - the assignments to the variables in params
        #   - the assignment to the return value
        no_assignments = True
        for method in matching_methods:
            match = True
            method_assignments = Assignments()

            # Replace the call node with the
            # method message that was matched
            #
            # Track what methods have been found so far
            # Distinguish between entry and exit
            method_assignments.add((is_entry, call_node), method)

            # parameters
            for formal, actual in zip(param_list, method.params):
                match = match and self._get_formal_assignment(method_assignments,
                                                              formal, actual)
            # return value (only for exit
            if (not is_entry) and match and retval != new_nil():
                match = match and self._get_formal_assignment(method_assignments,
                                                              retval,
                                                              method.return_value)

            if match:
                no_assignments = False
                set_assignments.add(method_assignments)

        if no_assignments:
            method_assignments = Assignments()
            method_assignments.add((is_entry, call_node), bottom_value)
            set_assignments.add(method_assignments)

        return set_assignments

