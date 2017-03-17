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
from cbverifier.utils.bimap import BiMap


from pysmt.logics import QF_BV
from pysmt.environment import get_env
from pysmt.typing import BVType
from pysmt.shortcuts import Symbol, FreshSymbol, BV
from pysmt.shortcuts import Solver, substitute
from pysmt.shortcuts import TRUE as TRUE_PYSMT
from pysmt.shortcuts import FALSE as FALSE_PYSMT
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne
from pysmt.shortcuts import Equals, GE, LE
from pysmt.shortcuts import BVULE, BVUGE

import math


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
        ast_set = set() # avoid duplicate specs - memo works at ast level
        ground_specs = []
        sg = SymbolicGrounding(self.trace_map)

        for substitution in sg.get_substitutions(spec):
            new_spec_ast = GroundSpecs._substitute(spec, substitution)

            # skip duplicates
            if new_spec_ast in ast_set:
                continue
            else:
                ast_set.add(new_spec_ast)

            new_spec = Spec(new_spec_ast)

            is_rhs_false = new_spec.is_spec_rhs_false()
            is_lhs_false = new_spec.is_regexp_false()
            # skip the specification if
            #   - the rhs is false
            #   - the regexp is false
            if ((not is_rhs_false) and (not is_lhs_false)):
                ground_specs.append(new_spec)
                self.ground_to_spec[new_spec] = spec
        return ground_specs

    @staticmethod
    def _substitute(spec, substitution):
        # TODO: add memoization

        def substitute_rec(node, substitution):
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

                res = None
                call_var = (is_entry, node)
                if call_var not in substitution:
                    res = new_false()
                else:
                    for call_message in substitution[call_var]:
                        if call_message is bottom_value:
                            if res is None:
                                res = new_false()
                            continue

                        assert call_message is not None

                        # reconstruct the call node from the node in the trace
                        # TODO: Move it in SymbolicGrounding
                        param_types = get_param_types_list(get_call_params(node))
                        new_call_node = GroundSpecs._msg_to_call_node(is_entry, call_message, param_types)
                        if res is None:
                            res = new_call_node
                        else:
                            res = new_or(res, new_call_node)
                return res
            elif (node_type == AND_OP):
                lhs = substitute_rec(node[1], substitution)
                rhs = substitute_rec(node[2], substitution)

                res = simplify_and(lhs, rhs)
                return res
            elif (node_type == OR_OP):
                lhs = substitute_rec(node[1], substitution)
                rhs = substitute_rec(node[2], substitution)
                res = simplify_or(lhs, rhs)
                return res

            elif (node_type == SEQ_OP):
                lhs = substitute_rec(node[1], substitution)
                rhs = substitute_rec(node[2], substitution)
                res = simplify_seq(lhs, rhs)
                return res
            elif (node_type == NOT_OP):
                lhs = substitute_rec(node[1], substitution)
                res = simplify_not(lhs)
                return res
            elif (node_type == STAR_OP):
                lhs = substitute_rec(node[1], substitution)
                res = simplify_star(lhs)
                return res
            elif (node_type == ENABLE_OP or node_type == DISABLE_OP):
                lhs = substitute_rec(node[1], substitution)
                rhs = substitute_rec(node[2], substitution)
                return create_node(node_type, [lhs, rhs])
            elif (node_type == SPEC_SYMB):
                lhs = substitute_rec(node[1], substitution)
                return create_node(SPEC_SYMB, [lhs, new_nil()])
            else:
                raise UnexpectedSymbol(node)

        new_spec_asts = substitute_rec(spec.ast, substitution)

        return new_spec_asts

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

    def get_source_spec(self, ground_spec):
        if ground_spec not in self.ground_to_spec:
            return None
        else:
            return self.ground_to_spec[ground_spec]

class SymbolicGrounding:

    # Maximum dimension for the bitvector
    # Practically we do not expect to have more values for a variable.
    MAX_BV=32

    def __init__(self, trace_map):
        self.pysmt_env = get_env()

        self.trace_map = trace_map

        # Bidireactional map (trace symbol, var in the encoding)
        self.fvars2encvars = BiMap()
        # Map from trace symbols to their maximum value in the encoding
        self.fvars_maxval = {}
        # Map from trace symbol to a bidirectional map (trace value, encoding value)
        self.fvars2values = {}
        # set of fvar that represents call nodes
        self.fvar_is_call = set()

        # standard initial value
        self.init_val = 0

        # Map from (entry_type, call_node) to (bindings, message)
        self.binding2message = {}


    def add_free_var(self, free_var):
        """ Creates the encoding for free_var """
        # We create a BV variable
        enc_val = FreshSymbol(BVType(SymbolicGrounding.MAX_BV))
        self.fvars2encvars.add(free_var, enc_val)
        return enc_val

    def add_val(self, free_var, val):
        """ Add val to free_var """
        # Update the maximum value
        if free_var in self.fvars_maxval:
            current_val = self.fvars_maxval[free_var]
            next_val = current_val + 1
        else:
            next_val = 0
        self.fvars_maxval[free_var] = next_val

        # Update the variable encoding map
        if free_var in self.fvars2values:
            fvals2encvalues = self.fvars2values[free_var]
        else:
            fvals2encvalues = BiMap()
            self.fvars2values[free_var] = fvals2encvalues
        enc_val = BV(next_val, SymbolicGrounding.MAX_BV)
        fvals2encvalues.add(val, enc_val)

        return enc_val

    def find_or_add_var(self, fvar):
        """ Finds or add the encoding for fvar """
        try:
            enc_var = self.fvars2encvars.lookup_a(fvar)
        except KeyError:
            enc_var = self.add_free_var(fvar)

        return enc_var

    def find_or_add_val(self, fvar, fval):
        """ Finds or add the value to the variable encoding """
        try:
            fvals2enc = self.fvars2values[fvar]
            try:
                enc_val = fvals2enc.lookup_a(fval)
            except KeyError:
                enc_val = self.add_val(fvar,fval)
        except KeyError:
            enc_val = self.add_val(fvar,fval)
        return enc_val


    def process_assignments_formula(self, is_entry, call_node, asets):
        """
        For each call node and for each concrete assignment creates the label
        that must be used in the regular expression.

        Each assignment to the formula represent an assignment to the free
        variables and the set of symbols in the trace that must be recognized by
        the regular expression.
        """

        # Group the messages by the same variable assigment
        a_map = {}
        for aset in asets:
            complete_assignment = True
            message = None
            bindings_set = set()

            for (fvar, fval) in aset.assignments.iteritems():
                if fval == bottom_value:
                    complete_assignment = False
                elif (get_node_type(fvar) == ID):
                    # ensure to add the bottom value for the variable
                    self.find_or_add_var(fvar)
                    self.find_or_add_val(fvar, bottom_value)

                    bindings_set.add((fvar, fval))
                elif (type(fvar) == tuple):
                    assert (is_entry, call_node) == fvar
                    call_var = (is_entry, call_node)

                    call_var_enc = self.find_or_add_var(call_var)
                    self.fvar_is_call.add(call_var)
                    self.find_or_add_val(call_var, frozenset([bottom_value]))

                    message = fval

            if complete_assignment and message is not None:
                bindings_set = frozenset(bindings_set)
                if bindings_set not in a_map:
                    a_map[bindings_set] = set()
                a_map[bindings_set].add(message)

        # Skip non-existing mappings
        # This is the case for constants calls that do not exist
        # in the original trace
        if (len(a_map) == 0):
            return TRUE_PYSMT()

        # Creates the formula that represents the assignment
        call_var = (is_entry, call_node)
        call_var_enc = self.find_or_add_var(call_var)
        call_encoding = TRUE_PYSMT()
        complement = TRUE_PYSMT()
        for (bindings_set, messages) in a_map.iteritems():
            antecedent = TRUE_PYSMT()
            for (fvar, fval) in bindings_set:
                # Get or add the variable encoding
                enc_var = self.find_or_add_var(fvar)
                # Find or add the value to the variable encoding
                enc_val = self.find_or_add_val(fvar, fval)
                antecedent = And(antecedent, Equals(enc_var, enc_val))

            complement = And(complement, Not(antecedent))
            msg_set_val = self.find_or_add_val(call_var,
                                               frozenset(messages))
            call_encoding = And(call_encoding,
                                Implies(antecedent,
                                        Equals(call_var_enc, msg_set_val)))

        # add the complement
        call_bottom_val_enc = self.find_or_add_val(call_var, frozenset([bottom_value]))
        call_encoding = And(call_encoding,
                            Implies(complement,
                                    Equals(call_var_enc, call_bottom_val_enc)))
        return call_encoding

    def get_messages(self, is_entry, node, bindings):
        # TODO: REMOVE
        messages = []
        try:
            for res in self.binding2message[(is_entry, node)]:
                (msg_bindings, message) = res

                found = True
                for (var, val) in msg_bindings:
                    try:
                        bind_val = bindings.get(var)
                        if (not (bind_val == val)):
                            found = False
                            break
                    except KeyError:
                        found = False
                        break

                # if find one it is ok
                if found:
                    messages.append(message)

            return messages
        except KeyError:
            return messages

    def get_var_val(self, enc_var, enc_value):
        """ Returns the trace value given an (encoding) variable and an encoding
        value"""
        fvar = self.fvars2encvars.lookup_b(enc_var)
        fvals2encvalues = self.fvars2values[fvar]
        fvalue = fvals2encvalues.lookup_b(enc_value)
        return (fvar, fvalue)

    def get_size(self, max_val):
        """ Returns the bv_size needed to represent values in the range
        [0...max_val]
        """
        bv_size = int(math.floor(math.log(max_val, 2))) + 1
        return bv_size

    def resize_bvs(self, formula):
        """ Resize the bitvector variables wrt to the maximum domain size """
        subs_map = {}
        for (fvar, max_value) in self.fvars_maxval.iteritems():
            old_enc_var = self.fvars2encvars.lookup_a(fvar)
            bv_size = self.get_size(max_value+1)
            new_enc_var = FreshSymbol(BVType(bv_size))

            self.fvars2encvars.add(fvar, new_enc_var)

            val2val = self.fvars2values[fvar]

            for i in range(max_value + 1):
                old_value = BV(i, SymbolicGrounding.MAX_BV)
                new_value = BV(i, bv_size)

                fval = val2val.lookup_b(old_value)
                val2val.add(fval, new_value)

                old_f = Equals(old_enc_var,  old_value)
                new_f = Equals(new_enc_var,  new_value)
                subs_map[old_f] = new_f

        formula = substitute(formula, subs_map)
        return formula

    def get_domain_formula(self):
        """ Returns the formula that encodes the domains of each
        variable in the encoding.

        Note: the size of the BV is not enough.
        """
        domain = TRUE_PYSMT()
        for (fvar, max_value) in self.fvars_maxval.iteritems():
            enc_var = self.fvars2encvars.lookup_a(fvar)
            bv_size = self.get_size(max_value+1)
            # WARNING: must use the unsigned comparison of bitvectors
            lb = BVUGE(enc_var, BV(self.init_val, bv_size))
            ub = BVULE(enc_var, BV(max_value, bv_size))

            domain = And(domain, And(ub,lb))

        return domain

    def _get_ground_bindings_formula(self, spec):
        ground_enc = self._ground_bindings_formula_rec(spec.ast, {})
        ground_enc = self.resize_bvs(ground_enc)
        ground_enc = And(ground_enc, self.get_domain_formula())
        return ground_enc

    def _ground_bindings_formula_rec(self, spec_node, memo):
        """ Returns a formula that encodes the set of all the possible bindings
        and assignments to CALL nodes
        """

        if (spec_node in memo):
            return memo[spec_node]

        node_type = get_node_type(spec_node)
        if (node_type in leaf_nodes):
            # ground set do not change in these cases
            res = TRUE_PYSMT()
        elif (node_type == AND_OP or
            node_type == SEQ_OP or
            node_type == ENABLE_OP or
            node_type == DISABLE_OP or
            node_type == OR_OP):

            # create the global constraints
            res = And(self._ground_bindings_formula_rec(spec_node[2], memo),
                      self._ground_bindings_formula_rec(spec_node[1], memo))
        elif (node_type == STAR_OP or node_type == SPEC_SYMB or
              node_type == NOT_OP):
            res = self._ground_bindings_formula_rec(spec_node[1], memo)
        elif (node_type == CALL_ENTRY or node_type == CALL_EXIT):
            spec_res = self.trace_map.lookup_assignments(spec_node)
            assert spec_res is not None

            res = self.process_assignments_formula(node_type == CALL_ENTRY, spec_node, spec_res)
        else:
            # WARNING: we handle one spec at a time (node_type != SPEC_LIST)
            raise UnexpectedSymbol(spec_node)

        memo[spec_node] = res
        return res


    def get_substitutions(self, spec):
        """ Returns the list of all the possible substitutions for the
        CALL nodes.
        """

        ground_formula = self._get_ground_bindings_formula(spec)

        substitutions = []

        # ALL SAT on assignments - the model is finite
        solver = self.pysmt_env.factory.Solver(quantified=False,
                                               name="z3",
                                               logic=QF_BV)
        solver.add_assertion(ground_formula)
        while (solver.solve()):
            model = solver.get_model()

            # Cut all the models that produces the same substitutions
            to_cut = TRUE_PYSMT()
            substitution = {}
            for (fvar, enc_var) in self.fvars2encvars.iteritems_a_b():
                if (fvar in self.fvar_is_call):
                    enc_value = model.get_value(enc_var, True)
                    (fvar1, fvalue) = self.get_var_val(enc_var, enc_value)
                    assert fvar1 == fvar
                    assert frozenset == type(fvalue)
                    substitution[fvar] = fvalue
                    to_cut = And(to_cut,Equals(enc_var, enc_value))
            substitutions.append(substitution)

            # rule out the current assignment
            solver.add_assertion(Not(to_cut))

        return substitutions


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

        # print TraceSpecConverter.traceval2specnode(actual)
        # print type(actual)
        # print formal
        # print type(formal)
        # print ""

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

