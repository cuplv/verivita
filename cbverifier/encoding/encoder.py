""" Encode and solve the verification problem

The input are:
  - a concrete trace
  - a specification

The verifier finds a possible (spurious) permutation of the events in
the concrete trace that may cause a bug (a bug arises a disabled
callin is called).

The possible permutation of the events depend on the enabled/disabled
status of events/callins.



PLAN:
  a. compute the ground specifications
    - TEST
  b. create the symbolic automata for the specifications
    - TEST
  b. create the encoding for the event transitions
  We cannot statically encode the effect of each callback and
  callin, since it depends on the whole history, and not on the
  callin/callback that we are computing.
  Hence, we need to encode one callin/callback per step and let the
  model checker figure out the state of the system.


OPTIMIZATIONS
The length of the sequence that must be explored can be quite high.
We need to optimize the encoding as much as we can.

Ideas:
  - Cone of influence reduction (harder due to regexp)

  - Merge (union) the regexp automata and reduce the state space
  Same settings of the CIAA 10 for PSL
  (From Sequential Extended Regular Expressions to NFA with Symbolic Labels, CIAA 10)
    - Automata with symbolic labels
    - The size of the alphabet is huge

  - Group the execution of callins and callbacks:
    - If two callin must be executed in sequence and they are
    independent one from each other, then there is no reason to not
    group them togheter.
    TODO: define when two callins and callbacks are independent.

"""

# TODOs:
# - implement pre for the simplification
# - fix encoding (and trace construction) using the simplification

import logging
import collections

from pysmt.environment import reset_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from pysmt.shortcuts import Solver
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL

from cbverifier.specs.spec import Spec
from cbverifier.traces.ctrace import CTrace


from cbverifier.helpers import Helper

Instance = collections.namedtuple("Instance", ["symbol", "args", "msg"],
                                  verbose=False,
                                  rename=False)

class TransitionSystem:
    """ (symbolic) Transition system"""
    def __init__(self):
        # internal representation of the transition system
        self.state_vars = set()
        self.input_vars = set()
        self.init = TRUE()
        self.trans = TRUE()


    def product(self, other_ts):
        """ Computes the synchronous product of self with other_ts,
        storing the product in self.

        Given TS1 = <V1, W1, I1, T1> and TS2 = <V2, W2, I2, T2>
        the product is the transition system
        TSP = <V1 union V2, W1 union W2, I1 and I2, T1 and T2>

        (V are the state variables, W the input variables,
        I is the initial condition, T the transition relation)
        """

        self.state_vars.update(other_ts.state_vars)
        self.input_vars.update(other_ts.input_vars)
        self.init = And(self.init, other_ts.init)
        self.trans = And(self.trans, other_ts.trans)


class TSEncoder:
    """
    Encodes the dynamic verification problem in a transition system.

    """

    def __init__(self, trace, specs):
        self.trace = trace
        self.specs = specs
        self.ts = None
        self.error_prop = None

        self.ground_specs = self._compute_ground_spec()

    def get_ts_encoding(self):
        """ Returns the transition system encoding of the dynamic
        verification problem.
        """
        if (self.ts is None): self._encode()
        return self.ts


    def _encode(self):
        """ Function that performs the actual encoding of the TS.

        The function performs the following steps:

        """
        self.ts = TransitionSystem()

        # Disjunctino of the error states
        self.error_prop = FALSE()

        for ground_spec in self.ground_specs:
            (gs_ts, error_condition) = self.get_ground_spec_ts(ground_spec)
            self.ts.product(gs_ts)
            self.error_prop = Or(self.error_prop, error_condition)

    def _compute_ground_spec(self):
        """ Computes all the ground specifications from the
        specifications with free variables in self.spec and the
        concrete trace self.trace

        Return a list of ground specifications.
        """

        ground_specs = []

        gs = GroundSpecs(self.trace)

        for spec in self.specs:
            tmp = gs.ground_spec(spec)
            ground_specs.extend(tmp)

        return ground_specs


    def _get_ground_spec_ts(self, ground_spec):
        """ Given a ground specification, returns the transition
        system that encodes the updates implied by the specification.
        """
        raise Exception("Not implemented")



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
            new_spec = self.substitute(spec, binding)
            ground_specs.append(new_spec)

        return ground_specs

    def _substitute(self, spec, binding):
        # TODO: add memoization

        def substitute_rec(self, node, binding):
            def sub_leaf(self, leaf, binding):
                leaf_type = get_node_type(leaf)

                if (leaf_type == DONTCARE): return leaf
                elif leaf_type != ID: return leaf
                else:
                    assert leaf in binding
                    return binding[leaf]


            def process_param(param_node):
                node_type = node_get_type(param_node)
                if (node_type != PARAM_LIST):
                    assert node_type == NIL
                    pass
                else:
                    # the binding should be there
                    res = bindings(param_node[1])
                    new_param(sub_leaf(self, node[1], binding),
                              process_param(param_node[2]))


            node_type = get_node_type(node)
            if (node_type in spec_ast.leaf_nodes): return node
            elif (node_type == CALL):
                new_params = process_param(get_call_params(node))

                new_call_node = new_call(sub_leaf(self, get_call_receiver(node),
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

                lhs = substitute_rec(self, node[1], binding)
                rhs = substitute_rec(self, node[2], binding)
                return create_node(node_type, [lhs, rhs])
            elif (node_type == STAR_OP or node_type == NOT_OP):
                lhs = substitute_rec(self, node[1], binding)
                return create_node(node_type, [lhs])
            else:
                raise UnexpectedSymbol(spec_node)


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
        def _ground_bindings_rec(self, spec_node, bindings):
            node_type = get_node_type(spec_node)
            if (node_type in spec_ast.leaf_nodes):
                # ground set do not change in these cases
                pass
            elif (node_type == AND_OP or
                node_type == OR_OP or
                node_type == SEQ_OP or
                node_type == ENABLE_OP or
                node_type == DISABLE_OP or
                node_type == SPEC_LIST):
                self._ground_bindings_rec(spec_node[2],
                                          self._ground_bindings_rec(spec_node[1],
                                                                    bindings))
            elif (node_type == STAR_OP or node_type == NOT_OP):
                self._ground_bindings_rec(spec_node[1], bindings)
            elif (node_type == CALL):
                # get the set of all the possible assignments
                # TODO pass bindings to perform directly the
                # product intersection while doing the lookup
                bindings.combine(self.lookup_assignments(node))
            else:
                raise UnexpectedSymbol(spec_node)

        binding_set = self._ground_bindings_rec(spec.ast, AssignmentsSet())
        return binding_set


    class Assignments(object):
        """ Represent a set of assignments derived from a single
        method call (messasge)"""
        def __init__(self):
            self.assignments = {}
            self._is_bottom = False

        def add(self, variable, value):
            assert variable not in self.assignments
            self.assignments.add[variable] = value

        def contains(self, formal, actual):
            try:
                return self.assignments[formal] == actual
            except KeyError:
                return False

        def is_bottom(self):
            """ Return true if the set of assignments represents the
            empty set """
            return self._is_bottom

        def intersect(self, other):
            """ Note: this is not a standard intersection.
            If a variable assignment does not exist in one of the two
            set, it is still present in the intersection.

            Side effect on the current set
            """
            new_map = {}

            my_map = self.assignments
            other_map = other.assignments

            if self.is_bottom() or other.is_bottom(): return

            for (key, value) in _map.iteritems():
                if key in other_map:
                    if other_map[key] == value:
                        # add common elements
                        new_map[key] = value
                    else:
                        # do not agree on the value for key - no
                        # compatible assignment
                        result = Assignments()
                        result._is_bottom = True
                        result.assignments = None
                        return result
                else:
                    new_map[key] = value

            # add the missing elements from other
            for (key, value) in _map.iteritems():
                if key not in my_map: new_map[key] = value

            result = Assignments()
            result.assignments = new_map
            return result


    class AssignmentsSet(object):
        """ Represent a set of assignments (or bindings) from free
        variables to actual values derived from a set of concrete
        method calls.
        """
        def __init__(self):
            self.assignments = set()

        def add(self, assignments):
            """ Add an assignment to the set of assignments.

            Assignment is a map from variables to values.
            """
            self.assignments.add(assignments)

        def combine(self, other):
            new_set = set()

            for assignments in self.assignments():
                for assignments_other in self.other():
                    new_a = assignments.intersect(assignments_other)
                    new_set,add(new_a)

            result = AssignmentsSet()
            result.assignements = new_a

            assert result


    class TraceMap(object):
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

            arity = len(msg.paramters)
            method_list = None
            try:
                method_list = arity_map[arity]
            except KeyError:
                method_list = []
                arity_map[arity] = method_list
            method_list.append(msg)

            for child in msg.children:
                trace_map = self._fill_map(msg, trace_map)

            return trace_map

        def lookup_methods(self, method_name, arity):
            """ Given the name of a method and its arity, returns the
            list of messages in the trace that
            match the method name and have the same number of
            parameters,
            """
            method_list = None
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
            """
            assert (get_node_type(call_node) == CALL)

            assignments = AssignmentsSet()

            try:
                # Build the list of formal parameters
                # (CALL, receiver, method_name, params)
                method_name_node = get_call_method(call_node)
                method_name = get_id_val(method_name_node)
                receiver = get_call_receiver(call_node)
                params = get_call_params(call_node)
                param_list = []
                if (node_get_type(receiver) != NIL):
                    param_list.append(receiver)
                while (node_get_type(params) != PARAM_LIST):
                    param_list.append(params[1])
                    params = params[2]

                matching_methods = self.lookup_methods(method_name, len(params))

                # For each method, find the assignments to the variables in params
                for method in matching_methods:
                    match = True
                    method_assignments = Assignments()
                    for formal, actual in zip(param_list, method.params):
                        formal_type = node_get_type(formal)

                        assert formal_type in leaf_nodes
                        assert formal_type != NIL

                        if (formal_type == DONTCARE):
                            continue
                        elif (formal_type in spec_ast.const_nodes):
                            # if the constant nodes do not match, do not consider
                            # this as a binding
                            # this is an optimization, it does not create bindings
                            # that we do not need
                            if str(formal[1]) != actual:
                                match = False
                                break
                        elif formal in method_assignments:
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
                        assignements.add(method_assignment)

                return assignments

            except KeyError:
                return assignments




