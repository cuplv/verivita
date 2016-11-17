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
  c. declare the variables of the TS                                  DONE
  d. encode the trace and the error conditions                        DONE
  e. encode the automata in the symbolic TS                           DONE

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

from pysmt.environment import reset_env, get_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol

from pysmt.shortcuts import TRUE as TRUE_PYSMT
from pysmt.shortcuts import FALSE as FALSE_PYSMT

from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from pysmt.shortcuts import Solver
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL

from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback
from cbverifier.encoding.automata import Automaton, AutoEnv
from cbverifier.encoding.counter_enc import CounterEnc
from cbverifier.encoding.grounding import GroundSpecs

from cbverifier.helpers import Helper

class TransitionSystem:
    """ (symbolic) Transition system"""
    def __init__(self):
        # internal representation of the transition system
        self.state_vars = set()
        self.input_vars = set()
        self.init = TRUE_PYSMT()
        self.trans = TRUE_PYSMT()

    def add_var(self, var):
        self.state_vars.add(var)

    def add_ivar(self, var):
        self.input_vars.add(var)

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

    def __repr__(self):
        """ Not efficient, need to use a buffer..."""

        res = "State vars: "
        for v in self.state_vars: res += ", %s" % v
        res += "\nInput vars:"
        for v in self.input_vars: res += ", %s" % v
        res += "\nINIT: "

        res += str(self.init.serialize())
        res += "\nTRANS: "
        res += str(self.trans.simplify().serialize())

        return res

class TSEncoder:
    """
    Encodes the dynamic verification problem in a transition system.

    """

    def __init__(self, trace, specs):
        self.trace = trace
        self.specs = specs
        self.ts = None
        self.error_prop = None

        (trace_length, msgs, cb_set, ci_set) = self.get_trace_stats()
        self.trace_length = trace_length
        self.msgs = msgs
        self.cb_set = cb_set
        self.ci_set = ci_set

        self.ground_specs = self._compute_ground_spec()
        self.pysmt_env = get_env()
        self.helper = Helper(self.pysmt_env)
        self.auto_env = AutoEnv(self.pysmt_env)
        self.cenc = CounterEnc(self.pysmt_env)
        self.r2a = RegExpToAuto(self.cenc, self.msgs, self.auto_env)



    def get_ts_encoding(self):
        """ Returns the transition system encoding of the dynamic
        verification problem.
        """
        if (self.ts is None): self._encode()
        return self.ts

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

        # 2. Specs ts
        (spec_ts, disabled_ci) = self._encode_ground_specs()
        self.ts.product(spec_ts)

        # 3. Encode the execution of the top-level callbacks
        (cb_ts, errors) = self._encode_cbs(disabled_ci)
        self.ts.product(cb_ts)
        self.error_prop = FALSE_PYSMT()
        for e in errors:
            self.error_prop = Or(self.error_prop, e)


    def _encode_ground_specs(self):
        """ Encode the set of ground specifications.

        Returns the transition system that encodes the effects of the
        specification and the set of messages disabled_ci.
        disabled_ci is the set
        of callin messages that can be disabled by some specification.
        """

        ts = TransitionSystem()

        # TODO: now the ground spec may still contain wild cards
        logging.warning("DONTCARE are still not handled " \
                        "in the grounding of the specifications")

        # Accepting is a map from messages to set of states where the
        # message enabled status is changed (because the system matched
        # a regular expression in the specification).
        # In practice, these are the accepting states of the automaton.
        accepting = {}
        disabled_ci = set()
        spec_id = 0
        for ground_spec in self.ground_specs:
            msg = get_spec_rhs(ground_spec.ast)
            key = TSEncoder.get_key_from_call(msg)

            if ground_spec.is_disable():
                if key in self.ci_set:
                    disabled_ci.add(key)

            if key not in accepting: accepting[key] = []
            gs_ts = self._get_ground_spec_ts(ground_spec,
                                             spec_id,
                                             accepting[key])
            ts.product(gs_ts)

        # encodes the frame conditions when there are no accepting
        # the frame conditions must be encoded globally
        #
        # For each key, accepting[key] contains the list of formulas
        # where key is changed.
        #
        # On the negation of the disjunction of these formulas
        # the variable do not change, so we must encode the frame
        # condition
        for (msg_key, accepting_for_var) in accepting.iteritems():
            msg_enabled = TSEncoder._get_state_var(msg_key)

            # msg_enabled <-> msg_enabled'
            fc_msg = Iff(msg_enabled,
                         Helper.get_next_var(msg_enabled,
                                             self.pysmt_env.formula_manager))

            changes = FALSE_PYSMT()
            # If we do not end in the final states of the automata
            # the variable should not change
            #
            # Note: the changes is encoded on the next state (the
            # accepting one)
            for u in accepting_for_var:
                changes = Or(changes, u)
            changes_next = self.helper.get_next_formula(ts.state_vars,changes)
            fc = Implies(changes_next, fc_msg)
            ts.trans = And(ts.trans, fc)

        return (ts, disabled_ci, accepting)


    def _get_ground_spec_ts(self, ground_spec, spec_id, accepting):
        """ Given a ground specification, returns the transition
        system that encodes the updates implied by the specification.

        It returns the ts that encode the acceptance of the language.

        It has side effects on accepting.


        Resulting transition system

        VAR pc : {0, ... num_states -1 };
        INIT:= \bigvee{s in initial} pc = s;
        TRANS
          \bigwedge{s in states}
            pc = s -> ( \bigvee{(dst,label) \in trans(s)} label and (pc' = dst) )

        TRANS
          \bigwedge{s in final}
            (pc' = s ->  enable_msg/not enable_msg)

        enable_msg is the message in the rhs of the spec. It is negated if
        the spec disables it.
        """
        def _get_pc_value(auto2ts_map, current_pc_val, auto_state):
            if not auto_state in auto2ts_map:
                current_pc_val += 1
                state_id = current_pc_val
                auto2ts_map[auto_state] = state_id
            else:
                state_id = auto2ts_map[auto_state]
            return (current_pc_val, state_id)

        assert isinstance(ground_spec, Spec)

        ts = TransitionSystem()

        # map from ids of automaton states to the value used in the
        # counter for the transition system
        auto2ts_map = {}

        # TODO: ensure to prune the unreachable states in the
        # automaton
        regexp = get_regexp_node(ground_spec.ast)
        auto = self.r2a.get_from_regexp(regexp)

        # program counter of the automaton
        auto_pc = "spec_pc_%d" % spec_id
        self.cenc.add_var(auto_pc, auto.count_state() - 1) # -1 since it starts from 0
        for v in self.cenc.get_counter_var(auto_pc): ts.add_var(v)

        # initial states
        # Initially we are in one of the initial states
        # There should be a single initial state though since the automaton
        # is deterministic
        current_pc_val = -1
        ts.init = FALSE_PYSMT()
        for a_init in auto.initial_states:
            (current_pc_val, s_id) = _get_pc_value(auto2ts_map,
                                                   current_pc_val,
                                                   a_init)

            #logging.debug("One of init: %s = %d" % (auto_pc,s_id))

            eq_current = self.cenc.eq_val(auto_pc, s_id)
            ts.init = Or(ts.init, eq_current)

        # automata transitions
        for a_s in auto.states:
            (current_pc_val, ts_s) = _get_pc_value(auto2ts_map,
                                                   current_pc_val,
                                                   a_s)
            eq_current = self.cenc.eq_val(auto_pc, ts_s)

            s_trans = FALSE_PYSMT()
            for (a_dst, label) in auto.trans[a_s]:
                (current_pc_val, ts_dst) = _get_pc_value(auto2ts_map,
                                                         current_pc_val,
                                                         a_dst)

                # logging.debug("Trans: %s = %d ->  %s = %d on %s" % (auto_pc,ts_s,auto_pc,ts_dst,str(label.get_formula())))

                eq_next = self.cenc.eq_val(auto_pc, ts_dst)
                eq_next = self.helper.get_next_formula(ts.state_vars, eq_next)
                t = And([eq_next, label.get_formula()])
                s_trans = Or(s_trans, t)

            s_trans = Implies(eq_current, s_trans)

            ts.trans = And(ts.trans, s_trans)

        # Record the final states - on these states the value of the
        # rhs of the specifications change
        msg = get_spec_rhs(ground_spec.ast)
        key = TSEncoder.get_key_from_call(msg)
        for a_s in auto.final_states:
            ts_s = auto2ts_map[a_s]

            eq_current = self.cenc.eq_val(auto_pc, ts_s)

            # add the current state to the accepting states
            accepting.append(eq_current)

            # encode the fact that the message must be
            # enabled/disabled in this state
            eq_next = self.helper.get_next_formula(ts.state_vars, eq_current)
            msg_enabled = Helper.get_next_var(TSEncoder._get_state_var(key),
                                              self.pysmt_env.formula_manager)

            if (ground_spec.is_disable()):
                effect_in_trans = Not(msg_enabled)
            else:
                assert ground_spec.is_enable()
                effect_in_trans = msg_enabled

            effect_in_trans = Implies(eq_next, effect_in_trans)
            ts.trans = And(ts.trans, effect_in_trans)

        return ts


    def _encode_vars(self):
        """ Encode the state and input variables of the system.

        We create a state variable for each message in the trace.

        We create a single (enumerative) input variable that encodes
        symbolically the alphabet. The enumerative is encoded with a
        set of Boolean variables.
        """
        var_ts = TransitionSystem()

        # add all the input varibles
        for v in self.r2a.get_letter_vars():
            var_ts.add_ivar(v)


        for msg in self.msgs:
            # create the state variable
            var = TSEncoder._get_state_var(msg)
            var_ts.add_var(var)

            # Add the constraint on the msg
            #
            # msg cannot be fired if msg is not enabled
            letter_eq_msg = self.r2a.get_msg_eq(msg)
            var_ts.trans = And(var_ts.trans,
                               Or(Not(letter_eq_msg), var))
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
        tl_callback_count = len(self.trace.children)
        pc_size = (self.trace_length - tl_callback_count) + 1
        pc_name = TSEncoder._get_pc_name()
        self.cenc.add_var(pc_name, pc_size - 1) # starts from 0

        # add all the bit variables
        for v in self.cenc.get_counter_var(pc_name):
            ts.add_var(v)

        # start from the initial state
        ts.init = self.cenc.eq_val(pc_name, 0)
        #logging.debug("Init state: %d" % (0))

        # print "Init: %s\n" % (ts.init)

        ts.trans = FALSE_PYSMT() # disjunction of transitions
        # encode each cb
        for tl_cb in self.trace.children:
            # dfs on the tree of messages
            state_count = 0
            current_state = 0

            stack = [tl_cb]
            while (len(stack) != 0):
                msg = stack.pop()
                msg_key = TSEncoder.get_msg_key(msg)

                # Fill the stack in reverse order
                for i in reversed(range(len(msg.children))):
                    stack.append(msg.children[i])

                # encode the transition
                if (len(stack) == 0):
                    # visited all the cb/ci of the top-level cb
                    next_state = 0
                else:
                    state_count += 1
                    next_state = state_count

                label = self.r2a.get_msg_eq(msg_key)

                s0 = self.cenc.eq_val(pc_name, current_state)
                snext = self.cenc.eq_val(pc_name, next_state)
                snext = self.helper.get_next_formula(ts.state_vars, snext)
                single_trans = And([s0, label, snext])
                ts.trans = Or([ts.trans, single_trans])

#                logging.debug("Trans: %d -> %d on %s" % (current_state, next_state, msg_key))

                # print "Trans: %d -> %d on %s" % (current_state, next_state, msg_key)
                # print label
                # print s0
                # print snext
                # print single_trans
                # print ""

                current_state = next_state

                if (msg_key in disabled_ci and isinstance(msg, CCallin)):
                    msg_enabled = TSEncoder._get_state_var(msg_key)
                    error_condition = And(s0, msg_enabled)
                    errors.add(error_condition)

        return (ts, errors)

    @staticmethod
    def _get_pc_name():
        atom_name = "pc"
        return atom_name

    @staticmethod
    def _get_state_var(key):
        atom_name = "enabled_" + key
        return Symbol(atom_name, BOOL)

    @staticmethod
    def get_key(method_name, params):
        assert method_name is not None
        assert params is not None
        assert method_name != ""

        key = "%s(%s)" % (method_name,
                          ",".join(params))
        return key

    @staticmethod
    def get_msg_key(msg):
        """ The input is a msg from a concrete trace.
        The output is the key to the message
        """
        params = []
        for p in msg.params:
            params.append(TSEncoder.get_value_key(p))
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

        while (PARAM_LIST == get_node_type(node_params)):
            p_node = node_params[1]
            assert (VALUE == get_node_type(p_node))
            p = TSEncoder.get_value_key(p_node[1])
            params.append(p)
            node_params = node_params[2]

        return TSEncoder.get_key(method_name, params)


    @staticmethod
    def get_value_key(value):
        """ Given a value returns its representation
        that will be used in the message key """

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
    def __init__(self, cenc, alphabet, auto_env=None):
        if auto_env is None:
            auto_env = AutoEnv.get_global_auto_env()
        self.auto_env = auto_env

        self.cenc = cenc
        self.alphabet = alphabet

        self.alphabet_list = list(self.alphabet)
        self.letter_to_val = {}
        for i in range(len(self.alphabet_list)):
            self.letter_to_val[self.alphabet_list[i]] = i

        # TODO: get a fresh variable
        self.counter_var = "__msg_var___"
        self.cenc.add_var(self.counter_var, len(self.alphabet))

    def get_letter_vars(self):
        return self.cenc.get_counter_var(self.counter_var)

    def get_msg_eq(self, msg_value):
        value = self.letter_to_val[msg_value]
        return self.cenc.eq_val(self.counter_var, value)

    def get_msg_for_val(self, value):
        assert value >= 0 and len(value) < len(self.alphabet_list) 
        return self.alphabet_list[value]

    def get_atom_var(self, call_node):
        key = TSEncoder.get_key_from_call(call_node)
        eq = self.get_msg_eq(key)
        return eq

    def get_from_regexp(self, regexp):
        """ Return a DETERMINISTIC automaton """
        res = self.get_from_regexp_aux(regexp)
        return res.determinize()

    def get_from_regexp_aux(self, regexp):
        node_type = get_node_type(regexp)

        if (node_type in [TRUE,FALSE,CALL,AND_OP,OR_OP,NOT_OP]):
            # base case
            # accept the atoms in the bexp
            formula = self.get_be(regexp)
            label = self.auto_env.new_label(formula)
            automaton = Automaton.get_singleton(label)
            return automaton
        elif (node_type == SEQ_OP):
            lhs = self.get_from_regexp_aux(regexp[1])
            rhs = self.get_from_regexp_aux(regexp[2])
            automaton = lhs.concatenate(rhs)
            lhs = None
            rhs = None
            return automaton
        elif (node_type == STAR_OP):
            lhs = self.get_from_regexp_aux(regexp[1])
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
            return TRUE_PYSMT()
        elif (node_type == FALSE):
            return FALSE_PYSMT()
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

