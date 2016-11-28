""" Encode and solve the verification problem

The input are:
  - a concrete trace
  - a set of specifications

The output is a transition system that encodes all the possible
repetitions of callbacks and callins that are consistent with the
specifications and an error conditions, that is true when the system
reaches a state where it can invoke a disabled callin.

A path from an initial state to an error state may be spurious in the
Android application.


The encoder performs the following steps:
1. Computes the set of ground specifications
The input specifications contains free variables. In this phase the
encoder takes all the concrete messages found in the trace, and
instantiates all the specifications that match them.

2. Create the symbolic automata for the specifications
For each ground specification, the encoder constructs an automaton
that recognize the language of the specification's regular expression
part.

The "effect" of the specification (e.g. enable a callback) is forced
int he transition system when the system visits a prefix that
matches the regular expression.

Everything is encoded as a set of transition systems.

3. Declare the variables of the transition system
The encoder keeps an enabled/allowed (state) variable for each message
in the concrete trace, and a (input) variable that determines the
message took in every transition of the system.

4. Encode the trace and the error conditions
In the resulting transition system each top-level callback in the
concrete trace can be choosen to be executed non-deterministically.

A top-level callback is a callback that is invoked directly by the
generation of an asynchronous event in Android (it is not nested under
any other callback or callin).

Once a top-level callback is chosen, the system follows the sequence
of callins and callbacks called from the top-level callback (it is a
sequence of fixed order).

The result is a transition system.

5.. Performs the product of the specifications' automata and the
transition system of the trace.

Performs the syncrhonous product of all the transition systems to
obtain the final transition system.



Possible bottlenecks:
a. The length of the sequence that must be explored can be huge.
We need to optimize the encoding as much as we can.

b. We build a single automata for each ground specification.
This can lead to an explosion in the state space.

c. The construction of each automaton can be expensive, since we
perform operations on symbolic labels

d. Other standard bottlenecks: e.g. recursive vs. iterative, no
memoization when visiting specs.


Possible ideas to overcome these issues:

Improvements for a)
- Cone of influence reduction.
  Some messages in the trace are not useful at all to reach a
  particular error condition.
  This is determined from the trace and the set of specifications.

  The idea is to remove these messages from the trace, reducing the
  number of variables in the system and the length of the traces that
  must be explored.

  This may be harder due to the the regular expressions.
  The reduction must preserve the reachability property.

- Group the execution of callins and callbacks:
  If two callin must be executed in sequence and they are
  independent one from each other, then we can execute them together.
  This is similar to step semantic.
  Also here we must be careful with regular expressions.
  The concept of "independent" callins and callback must be defined.

- Encode a top-level callback and all its descendant messages in a
  single transition (this is somehow related to the previous
  simplification).
  After we pick the top-level callback we have a straightline code
  until the next top-level callback is executed (no non-determinism).

  This is similar to the large block encoding in software model
  checking.

  Also here the issue is to consider the parallel execution of the
  automata, which instead has branching.


Improvements for b)
- We can perform the union of different regexp automata to reduce the state space.
  For example, we can perform the union of all the automata that have
  the same effect on the transition system.
  Here we will have a tradeoff between the composed representation of
  the automata and the monolithic one (WARNING: the states of the monolithic
  automaton can explode since we need a complete and deterministic automaton).

Improvements for c)
- Now we compute the label operations using SAT.
  We can switch to BDD to increase the sharing and exploit the
  canonical representation.


The module defines the following classes:
  - TransitionSystem
  - TSEncoder
  - TSMapback
  - RegExpToAuto

"""

import logging
from cStringIO import StringIO

from pysmt.logics import QF_BOOL
from pysmt.environment import get_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol
from pysmt.shortcuts import Solver
from pysmt.shortcuts import TRUE as TRUE_PYSMT
from pysmt.shortcuts import FALSE as FALSE_PYSMT
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

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

        self.gs = GroundSpecs(self.trace)
        self.ground_specs = self._compute_ground_spec()
        self.pysmt_env = get_env()
        self.helper = Helper(self.pysmt_env)
        self.auto_env = AutoEnv(self.pysmt_env)
        self.cenc = CounterEnc(self.pysmt_env)
        self.mapback = TSMapback(self.pysmt_env, None, None)

        self.error_label = "_error_"
        letters = set([self.error_label])
        letters.update(self.msgs)
        self.r2a = RegExpToAuto(self.cenc, letters,
                                self.mapback, self.auto_env)


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
        for spec in self.specs:
            tmp = self.gs.ground_spec(spec)
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
        (spec_ts, disabled_ci, accepting) = self._encode_ground_specs()
        self.ts.product(spec_ts)

        # 3. Encode the execution of the top-level callbacks
        (cb_ts, errors) = self._encode_cbs(disabled_ci)
        self.ts.product(cb_ts)
        self.error_prop = FALSE_PYSMT()
        for e in errors:
            self.error_prop = Or(self.error_prop, e)
        self.mapback.set_error_condition(self.error_prop)

        # initial condition: all the messages are enabled
        for msg in self.msgs:
            self.ts.init = And(self.ts.init,
                               TSEncoder._get_state_var(msg))


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

            # If we do not end in the final states of the automata
            # the variable should not change
            #
            # Note: the changes is encoded on the next state (the
            # accepting one)
            changes = FALSE_PYSMT()
            for u in accepting_for_var:
                changes = Or(changes, u)
            not_change = Not(changes)
            not_change_next = self.helper.get_next_formula(ts.state_vars, not_change)
            fc = Implies(not_change_next, fc_msg)
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
        spec_accepting = []
        msg = get_spec_rhs(ground_spec.ast)
        key = TSEncoder.get_key_from_call(msg)
        for a_s in auto.final_states:
            ts_s = auto2ts_map[a_s]

            eq_current = self.cenc.eq_val(auto_pc, ts_s)

            # add the current state to the accepting states
            spec_accepting.append(eq_current)

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
        accepting.extend(spec_accepting)

        # Set the mapback information
        accepting_formula = FALSE_PYSMT()
        for f in spec_accepting:
            accepting_formula = Or(accepting_formula, f)
        spec = self.gs.get_source_spec(ground_spec)
        self.mapback.add_var2spec(TSEncoder._get_state_var(key),
                                  ground_spec.is_enable(),
                                  ground_spec,
                                  accepting_formula,
                                  spec)

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
        error = None

        # Create the pc variable
        tl_callback_count = len(self.trace.children)
        # Creates an additional error state
        #
        # The trace has self.trace_length messages, and
        # there are tl_callback_count top-level callbacks.
        #
        # The initial state is shared by all the top level callbacks,
        # since from here we have the non-deterministic transitions
        # Hence we remove tl_callback_count states and we add one
        # single initial state.
        # Then, we add an additional error state.
        pc_size = self.trace_length - tl_callback_count + 1 + 1
        max_pc_value = pc_size - 1
        pc_name = TSEncoder._get_pc_name()
        self.cenc.add_var(pc_name, max_pc_value) # starts from 0
        self.mapback.set_pc_var(pc_name)
        self.mapback.add_encoder(pc_name, self.cenc)

        # The last state is the error one
        error_state_id = max_pc_value

        # add all the bit variables
        for v in self.cenc.get_counter_var(pc_name):
            ts.add_var(v)

        # start from the initial state
        ts.init = self.cenc.eq_val(pc_name, 0)
        #logging.debug("Init state: %d" % (0))

        ts.trans = FALSE_PYSMT() # disjunction of transitions
        # encode each cb
        for tl_cb in self.trace.children:
            # dfs on the tree of messages
            state_count = 0
            current_state = 0

            stack = [tl_cb]
            while (len(stack) != 0):
                msg = stack.pop()
                msg_key = TSEncoder.get_key_from_msg(msg)
                msg_enabled = TSEncoder._get_state_var(msg_key)

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

                # Encode the enabled transition
                label = And(self.r2a.get_msg_eq(msg_key), msg_enabled)
                s0 = self.cenc.eq_val(pc_name, current_state)
                self.mapback.add_pc2trace(current_state, msg)
                snext = self.cenc.eq_val(pc_name, next_state)
                snext = self.helper.get_next_formula(ts.state_vars, snext)
                single_trans = And([s0, label, snext])
                ts.trans = Or([ts.trans, single_trans])

#                logging.debug("Trans: %d -> %d on %s" % (current_state, next_state, msg_key))

                # encode the transition to the error state
                if (msg_key in disabled_ci and isinstance(msg, CCallin)):
                    error_label = And(Not(msg_enabled),
                                      self.r2a.get_msg_eq(self.error_label))
                    error_state = self.cenc.eq_val(pc_name, error_state_id)
                    snext_error = self.helper.get_next_formula(ts.state_vars,
                                                               error_state)
                    single_trans = And([s0, error_label, snext_error])
                    ts.trans = Or([ts.trans, single_trans])

                    if error is None:
                        error = self.cenc.eq_val(pc_name, max_pc_value)
                        self.mapback.add_pc2trace(error_state_id,
                                                  self.error_label)

                current_state = next_state

        # Add self loop on error state to avoid deadlocks
        error_label = And(self.r2a.get_msg_eq(self.error_label))
        error_state = self.cenc.eq_val(pc_name, error_state_id)
        snext_error = self.helper.get_next_formula(ts.state_vars,
                                                   error_state)
        single_trans = And([error_state, error_label, snext_error])
        ts.trans = Or([ts.trans, single_trans])

        if error is None:
            errors = []
        else:
            errors = [error]
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
    def get_key(retval, call_type, method_name, params):
        assert method_name is not None
        assert params is not None
        assert method_name != ""

        assert call_type == "CI" or call_type == "CB"

        if (retval != None):
            key = "%s=[%s]_%s(%s)" % (retval,
                                      call_type,
                                      method_name,
                                      ",".join(params))
        else:
            key = "[%s]_%s(%s)" % (call_type,
                                   method_name,
                                   ",".join(params))
        return key

    @staticmethod
    def get_key_from_msg(msg):
        """ The input is a msg from a concrete trace.
        The output is the key to the message
        """

        if isinstance(msg, CCallin):
            msg_type = "CI"
        elif isinstance(msg, CCallback):
            msg_type = "CB"
        else:
            assert False

        if (msg.return_value is None):
            retval = None
        else:
            retval = TSEncoder.get_value_key(msg.return_value)

        params = []
        for p in msg.params:
            params.append(TSEncoder.get_value_key(p))

        full_msg_name = msg.get_full_msg_name()
        return TSEncoder.get_key(retval, msg_type, full_msg_name, params)

    @staticmethod
    def get_key_from_call(call_node):
        """ Works for grounded call node """
        assert get_node_type(call_node) == CALL

        node_retval = get_call_assignee(call_node)
        if (new_nil() != node_retval):
            assert ID == get_node_type(node_retval)
            retval = get_id_val(node_retval)
        else:
            retval = None

        node_call_type = get_call_type(call_node)
        if (get_node_type(node_call_type) == CI):
            call_type = "CI"
        elif (get_node_type(node_call_type) == CB):
            call_type = "CB"
        else:
            assert False

        # method_name_node = get_call_method(call_node)
        method_name_node = get_call_signature(call_node)
        assert (ID == get_node_type(method_name_node))
        method_name = get_id_val(method_name_node)
        receiver = get_call_receiver(call_node)

        if (new_nil() != receiver):
            assert ID == get_node_type(receiver)
            params = [get_id_val(receiver)]
        else:
            params = []

        node_params = get_call_params(call_node)

        while (PARAM_LIST == get_node_type(node_params)):
            p_node = get_param_name(node_params)
            assert ID == get_node_type(p_node)
            p = get_id_val(p_node)
            params.append(p)
            node_params = get_param_tail(node_params)

        return TSEncoder.get_key(retval, call_type,
                                 method_name, params)


    @staticmethod
    def get_value_key(value):
        """ Given a value returns its representation
        that will be used in the message key """

        assert (isinstance(value, CValue))

        value_repr = value.get_value()

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
            key = TSEncoder.get_key_from_msg(msg)

            msgs.add(key)
            if (isinstance(msg, CCallback)):
                cb_set.add(key)
            if (isinstance(msg, CCallin)):
                ci_set.add(key)

            for msg2 in msg.children:
                stack.append(msg2)

        return (trace_length, msgs, cb_set, ci_set)


class TSMapback():
    """ Keeps the needed information to mapback the results from the
    encoding to the trace/specification level.

    Data to store:
    a. Message state variable -> ground specification -> (accepting, specification)
    b. (msg_ivar, value) -> msg
    c. (pc_var, value) -> ci/cb in the trace
    """

    def __init__(self, pysmt_env, msg_ivar, pc_var):
        """ Info to keep: """
        self.vars2spec = {}
        self.vars2msg = {}
        self.pc2trace = {}
        self.pc2ci = {}

        self.msg_ivar = msg_ivar
        self.pc_var = pc_var
        self.error_condition = None

        # Several counter variables are encoded with a set of Boolean
        # variables.
        #
        # In the model we have the Boolean variables, but we want to
        # compare their truth assignment with the value of the
        # counter.
        #
        # We reuse the counter encoders already used in the encoding
        # for this
        self.vars_encoders = {}

        # used for lazyness to evaluate a formula given a model
        self.pysmt_env = pysmt_env

    def set_msg_ivar(self, msg_ivar):
        self.msg_ivar = msg_ivar

    def set_pc_var(self, pc_var):
        self.pc_var = pc_var

    def add_encoder(self, var, encoder):
        self.vars_encoders[var] = encoder

    def add_var2spec(self, var, value, ground_spec, accepting, spec):
        key = (var, value)
        if key not in self.vars2spec:
            gs_map = {}
            self.vars2spec[key] = gs_map
        else:
            gs_map = self.vars2spec[key]

        assert ground_spec not in gs_map
        gs_map[ground_spec] = (accepting, spec)

    def add_vars2msg(self, value, msg):
        assert self.msg_ivar is not None
        self.vars2msg[(self.msg_ivar,value)] = msg

    def add_pc2trace(self, value, trace_msg):
        assert self.pc_var is not None
        self.pc2trace[(self.pc_var, value)] = trace_msg

    def set_error_condition(self, error_condition):
        self.error_condition = error_condition

    def _get_msg_for_model(self, var_map, var, current_state):
        assert var in self.vars_encoders

        counter_enc = self.vars_encoders[var]
        value = counter_enc.get_counter_value(var, current_state)

        key = (var, value)
        if key in var_map:
            return var_map[key]
        else:
            return None

    def get_trans_label(self, current_state):
        """ Given the model of the current state, returns
        the label of the message executed in the transition
        """
        return self._get_msg_for_model(self.vars2msg,
                                       self.msg_ivar, current_state)


    def get_fired_trace_msg(self, current_state):
        """ Given the models for the current states, returns
        the correspondent message in the trace that was executed.
        """
        return self._get_msg_for_model(self.pc2trace,
                                       self.pc_var, current_state)

    def get_fired_spec(self, current_state, next_state, only_changed=True):
        """ Given the models for the current and next states, return
        a set of pairs containing a ground specification and the
        corresponding general specification.

        A ground specification is in the specification if its effect
        was applied in the transition relation.

        The flag only_changed only reports the specifications that
        changed the state of the system.
        """

        def same_model(var, mod1, mod2):
            return mod1[var] == mod2[var]

        solver = self.pysmt_env.factory.Solver(quantified=False,
                                               name="z3",
                                               logic=QF_BOOL)

        for (var, value) in next_state.iteritems():
            if (value):
                solver.add_assertion(var)
            else:
                solver.add_assertion(Not(var))

        fired_specs = []
        for (key, gs_map) in self.vars2spec.iteritems():
            (var, value) = key

            if ((next_state[var] != value) or
                (only_changed and
                 same_model(var,
                            current_state,
                            next_state))):
                continue

            for (gs, values) in gs_map.iteritems():
                (accepting, spec) = values
                solver.push()
                solver.add_assertion(accepting)
                if (solver.solve()):
                    fired_specs.append((gs, spec))
                solver.pop()

        return fired_specs

    def is_error(self, state):
        """ Return true if the state is an error state. """
        solver = self.pysmt_env.factory.Solver(quantified=False,
                                               name="z3",
                                               logic=QF_BOOL)

        for (var, value) in state.iteritems():
            if (value):
                solver.add_assertion(var)
            else:
                solver.add_assertion(Not(var))

        return solver.is_sat(self.error_condition)


class RegExpToAuto():
    """ Utility class to convert a regular expression in an automaton.

    TODO: We can implement memoization of the intermediate results

    TODO: all the recursive functions should become iterative

    """
    def __init__(self, cenc, alphabet, mapback, auto_env=None):
        if auto_env is None:
            auto_env = AutoEnv.get_global_auto_env()
        self.auto_env = auto_env

        self.cenc = cenc
        self.alphabet = alphabet

        # TODO: get a fresh variable
        self.counter_var = "__msg_var___"
        self.cenc.add_var(self.counter_var, len(self.alphabet))
        mapback.set_msg_ivar(self.counter_var)
        mapback.add_encoder(self.counter_var, self.cenc)

        self.alphabet_list = list(self.alphabet)
        self.letter_to_val = {}
        for i in range(len(self.alphabet_list)):
            self.letter_to_val[self.alphabet_list[i]] = i
            mapback.add_vars2msg(i, self.alphabet_list[i])

    def get_letter_vars(self):
        return self.cenc.get_counter_var(self.counter_var)

    def get_counter_var(self):
        return self.counter_var

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

