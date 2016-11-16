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
  a. compute the ground specifications                                DONE
  b. create the symbolic automata for the specifications              DONE
  c. declare the variables of the TS
  d. encode the trace and the error conditions
  e. encode the automata in the symbolic TS


NOTE:
We cannot statically encode the effect of each callback and
callin, since it depends on the whole history, and not on the
callin/callback that we are computing.
Hence, we need to encode one callin/callback per step and let the
model checker figure out the state of the system.


Issues:
- The length of the sequence that must be explored can be quite high.
We need to optimize the encoding as much as we can.

- Logarithmic encoding for the input variables
They are in mutex now.

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

  - Encode a callback and its descendant messages in a single transition
  This is similar to SSA construction

"""

import logging
from cStringIO import StringIO

from pysmt.environment import reset_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from pysmt.shortcuts import Solver
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL

from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback
from cbverifier.encoding.automata import Automaton, AutoEnv
from cbverifier.encoding.counter_enc import CounterEnc
from cbverifier.helpers import Helper

class TransitionSystem:
    """ (symbolic) Transition system"""
    def __init__(self):
        # internal representation of the transition system
        self.state_vars = set()
        self.input_vars = set()
        self.init = TRUE()
        self.trans = TRUE()

    def _add_var(self, var):
        self.state_vars.append(var)

    def _add_ivar(self, var):
        self.input_vars.append(var)

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
        self.r2a = RegExpToAuto()
        self.cenc = CounterEnc()

        (trace_length, msgs, cb_set, ci_set) = self.get_trace_stats()
        self.trace_length = trace_length
        self.msgs = msgs
        self.cb_set = cb_set
        self.ci_set = ci_set

    def get_ts_encoding(self):
        """ Returns the transition system encoding of the dynamic
        verification problem.
        """
        if (self.ts is None): self._encode()
        return self.ts

    def _encode(self):
        """ Function that performs the actual encoding of the TS.

        The function performs the following steps:

        1. Encode all the variables of the system
        2. Encode the effects of the specifications
        3. Encode the execution of the top-level callbacks and the
        error conditions
        """
        self.ts = TransitionSystem()

        # 1. Encode all the variables of the system
        vars_ts = self._encode_vars()
        self.ts.product(vars_ts)

        # 2. Encode the effects of the specifications
        disabled_ci = {}
        spec_id = 0

        # TODO: now the ground spec may still contain wild cards
        logging.warning("DONTCARE are still not handled " \
                        "in the grounding of the specifications")
        # raise Exception("Not implemented")
        # (e.g. DONTCARE values)

        updates = {}
        for ground_spec in self.ground_specs:
            msg = get_spec_rhs(ground_spec.ast)
            key = TSEncoder.get_key_from_call(msg)

            if ground_spec.is_disable():
                if key in self.ci_set():
                    disabled_ci.add(key)

            # for a key, updates contains the list of formulas where.
            # key is changed
            #
            # On the negation of the disjunction of these formulas
            # the variable do not change, so we must encode the frame
            # condition
            if key not in updates: updates[key] = []

            gs_ts = self._get_ground_spec_ts(ground_spec,
                                             spec_id,
                                             updates[key])
            self.ts.product(gs_ts)

        # encodes the frame conditions when there are no updates
        # the frame conditions must be encoded globally
        # TODO
        raise Exception("Not implemented")


        # 3. Encode the execution of the top-level callbacks
        (cb_ts, errors) = self._encode_cbs(disabled_ci)
        self.error_prop = FALSE()
        for e in errors:
            self.error_prop = Or(self.error_prop, e)


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


    def _get_ground_spec_ts(self, ground_spec, spec_id, update):
        """ Given a ground specification, returns the transition
        system that encodes the updates implied by the specification.

        updates is a map 
        """
        def _get_pc_value(auto2ts_map, current_pc_val, auto_state):
            if not auto_state in auto2ts_map:
                current_pc_val += 1
                auto2ts_map[auto_state] = current_pc_val
            else:
                current_pc_val = auto2ts_map[auto_state]
            return current_pc_val

        ts = TransitionSystem()
        updates = []

        # map from ids of automaton states to the value used in the
        # counter for the transition system
        auto2ts_map = {}

        auto = self.r2a.get_from_regexp(ground_spec)
        # TODO: ensure to prune the unreachable states in the automaton

        # program counter of the automaton
        auto_pc = "spec_pc_%d" % spec_id
        self.cenc.add(auto_pc, auto.count_state() - 1)
        for v in self.cenc.get_counter_var(auto_pc):
            ts.add_var(v)

        # initial states
        current_pc_val = -1
        for a_init in auto.initial_states:
            current_pc_val = _get_pc_value(auto2ts_map,
                                           current_pc_val,
                                           a_init)

            # auto_pc = current_pc_val
            eq_current = self.cenc.eq_val(auto_pc,
                                          current_pc_val)
            ts.init = And(ts.init, eq_current)

        # automata transitions
        for a_s in auto.states:
            current_pc_val = _get_pc_value(auto2ts_map,
                                           current_pc_val,
                                           a_s)
            ts_s = current_pc_val
            eq_current = self.cenc.eq_val(auto_pc, ts_s)

            s_trans = FALSE()
            for (a_dst, label) in auto.trans[a_s]:
                current_pc_val = _get_pc_value(auto2ts_map,
                                               current_pc_val,
                                               a_dst)
                ts_dst = current_pc_val

                eq_next = self.cenc.eq_val(auto_pc, ts_dst)
                eq_next = Helper.get_next_formula(eq_next)

                t = And([eq_next, label.get_formula()])
                s_trans = Or(s_trans, t)

            s_trans = Or(Not(eq_current), s_trans)
            ts.trans = And(ts.trans, s_trans)

        # Record the final states - on these states the value of the
        # rhs of the specifications change
        for a_s in auto.final_states:
            ts_s = auto2ts_map[a_s]
            eq_current = self.cenc.eq_val(auto_pc, ts_s)
            updates.add(eq_current)

        return ts


    def _encode_vars(self):
        """ Encode the state and input variables of the system.

        We create a state and an input variable for each message in
        the trace.
        """
        var_ts = TransitionSystem()

        for msg in self.trace_msgs:
            # create the state variable
            key = TSEncoder.get_msg_key(msg)
            var = TSEncoder._get_state_var(msg)
            var_ts.add_var(var)

            # create the input variable
            ivar = TSEncoder._get_input_var(msg)
            var_ts.add_ivar(ivar)

            # add the constraint on the input variable
            var_ts.trans = And(var_ts.trans,
                               And(Not(ivar), var))
        return var_ts


    def _encode_cbs(self, disabled_ci):
        """ Encodes the callbacks.

        The system picks a top-level callback in the trace to execute.

        At that point, the system encodes the sequence of callins and
        callbacks executed in the same stack trace of the top-level
        callback.

        We keep a program counter to encode each inner state.
        This determines the next callin/callback to be executed.
        The sequence is deterministic once the scheduler pick a
        top-level callback.

        Returns a transition system and a list of error states
        """

        ts = TransitionSystem()
        errors = []

        # Create the pc variable
        length = len(self.trace_msgs)
        num_tl_cb = len(self.trace.children)
        pc_size = (length - num_tl_cb) + 1
        pc_name = TSEncoder._get_pc_name()
        self.cenc.add_var(pc_name, length-1) # starts from 0

        # add all bit variables
        for v in self.cenc.get_counter_var(pc_name):
            ts.add_var(v)

        # start from the initial state
        ts.init = self.cenc.eq_val(pc_name, 0)

        # encode each cb
        for tl_cb in self.trace.children:
            # dfs on the tree of messages
            current_state = 0
            stack = [tl_cb]
            while (len(stack) != 0):
                msg = stack.pop()
                msg_key = TSEncoder.get_key_from_call(msg)

                # Fill the stack in reverse order
                for i in reversed(range(len(msg.children))):
                    stack.push(msg.children[i])

                # encode the transition
                if (len(stack) == 0):
                    next_state = 0 # go back to 0
                else:
                    next_state = prev_state + 1

                label = self._get_message_label(msg_key)
                s0 = self.cenc.eq_val(pc_name, current_state)
                snext = self.cenc.eq_val(pc_name, next_state)
                snext = Helper.get_next_formula(snext)
                ts.trans = And([ts.trans, s0, label, snext])
                current_state = next_state

                msg_enabled = TSEncoder._get_state_var(msg_key)
                error_condition = And(s0, msg_enabled)
                errors.add(error_condition)

        return (ts, errors)


    def _get_message_label(self, msg_key):
        # TODO
        raise Exception("Not implemented")
        # encode the label for msg and the negation of all the
        # other messages

    @staticmethod
    def _get_pc_name():
        atom_name = "pc"
        return atom_name

    @staticmethod
    def _get_state_var(key):
        atom_name = "enabled_" + key
        return Symbol(atom_name, BOOL)

    @staticmethod
    def _get_input_var(key):
        atom_name = key
        return Symbol(atom_name, BOOL)

    @staticmethod
    def get_key(method_name, params):
        key = "%s(%s)" % (method_name,
                          ",".join(params))
        return key

    @staticmethod
    def get_msg_key(msg):
        params = []
        for p in msg.params:
            params.add(TSEncoder.get_value_key(p))
        return TSEncoder.get_key(msg.method_name, params)

    @staticmethod
    def get_key_from_call(call_node):
        """ Works for grounded call node """
        assert get_node_type(call_node) == CALL

        method_name_node = get_call_method(call_node)
        assert (ID == get_node_type(method_name_node))
        method_name = method_name_node[1]

        receiver = get_call_receiver(call_node)

        if (new_nil() != receiver):
            assert VALUE == get_node_type(receiver)
            params = [TSEncoder.get_value_key(receiver[1])]
        else:
            params = []

        node_params = get_call_params(call_node)
        while (PARAM_LIST == params):
            p = TSEncoder.get_value_key(node_params[1])
            params.append(p)
            node_params = node_params[2]

        return TSEncoder.get_key(method_name, params)


    @staticmethod
    def get_value_key(value):
        assert (isinstance(value, CValue))
        if value.is_null:
            value_repr = "NULL"
        elif value.value is not None:
            value_repr = str(value.value)
        elif value.object_id is not None:
            value_repr = str(value.object_id)
        else:
            raise Exception("Cannot find a unique identifier for the value "\
                            "%s" % (str(value)))
        return value_repr

    def get_trace_stats(self):
        # count the total number of messages
        trace_length = 0
        msgs = set()
        cb_set = set()
        ci_set = set()

        stack = []
        for msg in self.trace.children:
            stack.append(msg)

        while (len(stack) != 0):
            msg = stack.pop()

            trace_length = trace_length + 1
            key = TSEncoder.get_msg_key(msg)

            msgs.add(key)
            if (isinstance(msg, CCallback)):
                cb_set.add(key)
            if (isinstance(msg, CCallin)):
                ci_set.add(key)

            for msg2 in msg.children:
                stack.append(msg2)

        return (trace_length, msgs, cb_set, ci_set)


class RegExpToAuto():
    """ Utility class to convert a regular expression in an automaton.

    TODO: We can implement memoization of the intermediate results

    TODO: all the recursive functions should become iterative

    """
    def __init__(self, auto_env=None):
        if auto_env is None:
            auto_env = AutoEnv.get_global_auto_env()
        self.auto_env = auto_env

    def get_atom_var(self, call_node):
        key = TSEncoder.get_key_from_call(call_node)
        ivar = TSEncoder._get_input_var(key)
        return ivar

    def get_from_regexp(self, regexp, env=None):
        node_type = get_node_type(regexp)

        if (node_type in [TRUE,FALSE,CALL,AND_OP,OR_OP,NOT_OP]):
            # base case
            # accept the atoms in the bexp
            formula = self.get_be(regexp)
            label = self.auto_env.new_label(formula)
            automaton = Automaton.get_singleton(label)
            return automaton
        elif (node_type == SEQ_OP):
            lhs = self.get_from_regexp(regexp[1])
            rhs = self.get_from_regexp(regexp[2])
            automaton = lhs.concatenate(rhs)
            lhs = None
            rhs = None
            return automaton
        elif (node_type == STAR_OP):
            lhs = self.get_from_regexp(regexp[1])
            automaton = lhs.klenee_star()
            lhs = None
            return automaton
        else:
            # Should not see them, the boolean atoms are the CALLS node
            # ID, INT, FLOAT, PARAM_LIST, NIL, DONTCARE, STRING, VALUE
            #
            # Should not even see the higher level nodes:
            # SPEC_SYMB
            # ENABLE_OP
            # DISABLE_OP
            # SPEC_LIST
            raise UnexpectedSymbol(regexp)

    def get_be(self, be_node):
        """ Given a node that represent a Boolean expression returns
        the correspondent formula in PySMT """
        node_type = get_node_type(be_node)

        if (node_type == TRUE):
            return TRUE()
        elif (node_type == FALSE):
            return FALSE()
        elif (node_type == CALL):
            # generate a boolean atom for the call
            atom_var = self.get_atom_var(be_node)
            return atom_var
        elif (node_type == AND_OP):
            return And(self.get_be(be_node[1]),
                       self.get_be(be_node[2]))
        elif (node_type == OR_OP):
            return Or(self.get_be(be_node[1]),
                      self.get_be(be_node[2]))
        elif (node_type == NOT_OP):
            return Not(self.get_be(be_node[1]))
        else:
            raise UnexpectedSymbol(be_node)

