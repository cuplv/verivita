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

5. Performs the product of the specifications' automata and the
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
import copy

from pysmt.logics import QF_BOOL
from pysmt.environment import get_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol
from pysmt.shortcuts import Solver
from pysmt.shortcuts import TRUE as TRUE_PYSMT
from pysmt.shortcuts import FALSE as FALSE_PYSMT
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne
from pysmt.shortcuts import simplify

from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback
from cbverifier.encoding.automata import Automaton, AutoEnv
from cbverifier.encoding.counter_enc import CounterEnc
from cbverifier.encoding.grounding import GroundSpecs
from cbverifier.encoding.conversion import TraceSpecConverter

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

    ENTRY = "ENTRY"
    EXIT = "EXIT"


    def __init__(self, trace, specs, ignore_msgs = False):
        # copy the trace removing the top-level exception
        self.trace = trace.copy(True)

        self.specs = specs
        self.ts = None
        self.error_prop = None

        self.gs = GroundSpecs(self.trace)
        self.ground_specs = TSEncoder._compute_ground_spec(self.gs, self.specs)

        # Remove all the messages in the trace that do not
        # appear in the specification.
        # WARNING: the simplification is UNSOUND - added to make
        # progresses in the verification.
        if (ignore_msgs):
            self.trace = TSEncoder._simplify_trace(self.trace,
                                                   self.ground_specs)
            print("\n---Simplified Trace---")
            self.trace.print_trace(sys.stdout)
            print("\n")

        (trace_length, msgs, fmwk_contr, app_contr) = self.get_trace_stats()
        self.trace_length = trace_length
        self.msgs = msgs
        # set of messages controlled by the framework
        self.fmwk_contr = fmwk_contr
        # set of messages controlled by the app
        self.app_contr = app_contr

        self.pysmt_env = get_env()
        self.helper = Helper(self.pysmt_env)
        # With True we use BDDs
        self.auto_env = AutoEnv(self.pysmt_env, False)
        self.cenc = CounterEnc(self.pysmt_env)
        self.mapback = TSMapback(self.pysmt_env, None, None)

        self.error_label = "_error_"
        letters = set([self.error_label])
        letters.update(self.msgs)
        self.r2a = RegExpToAuto(self.cenc, letters,
                                self.mapback, self.auto_env)


        # Map from regular expression to the correspondent automata, pc and final states
        self.regexp2ts = {}

    def get_ts_encoding(self):
        """ Returns the transition system encoding of the dynamic
        verification problem.
        """
        if (self.ts is None): self._encode()
        return self.ts

    def get_trace_encoding(self, tl_cb_ids = None):
        """ Returns the encoding of the trace formed by the callbacks
        """
        # the ts encoding should be built
        self.get_ts_encoding()

        tl_cbs = []
        if tl_cb_ids is not None:
            for message_id in tl_cb_ids:
                cb = self.trace.get_tl_cb_from_id(message_id)
                if cb is None:
                    raise Exception("Message id %s not found in the trace" % message_id)
                tl_cbs.append(cb)
        else:
            tl_cbs = self.trace.children

        # encode each callback
        # No trace constraints in the initial state
        trace_encoding = []
        pc_name = TSEncoder._get_pc_name()
        for tl_cb in tl_cbs:
            stack = [(TSEncoder.EXIT, tl_cb),(TSEncoder.ENTRY, tl_cb)]

            while (len(stack) != 0):
                (entry_type, msg) = stack.pop()

                # Fill the stack in reverse order
                if (TSEncoder.ENTRY == entry_type):
                    for i in reversed(range(len(msg.children))):
                        stack.append((TSEncoder.EXIT, msg.children[i]))
                        stack.append((TSEncoder.ENTRY, msg.children[i]))

                msg_enc = self.mapback.get_trans2pc((entry_type, msg))
                assert(msg_enc is not None)

                (current_state, next_state) = msg_enc
                s0 = self.cenc.eq_val(pc_name, current_state)
                s1 = self.cenc.eq_val(pc_name, next_state)
                logging.debug("Simulation - transition from %s -> %s" % (current_state,next_state))

                try:
                    msg_error_enc = self.mapback.get_trans2pc((entry_type, msg, self.error_label))
                    logging.debug("Simulation - transition from %s -> %s could not happen if msg is not enabled" % (current_state,next_state))
                    if msg_error_enc is not None:
                        # this is a possible error state
                        msg_key = TSEncoder.get_key_from_msg(msg, entry_type)
                        msg_enabled = TSEncoder._get_state_var(msg_key)
                        # progress only if the message is enabled
                        s0 = And(s0, msg_enabled)
                except KeyError:
                    pass
                trace_encoding.append((s0,s1))

        return trace_encoding


    def get_ground_spec(self):
        return self.ground_specs

    @staticmethod
    def _compute_ground_spec(gs, specs):
        """ Computes all the ground specifications from the
        specifications with free variables in self.spec and the
        concrete trace self.trace

        Return a list of ground specifications.
        """

        ground_specs = set()
        for spec in specs:
            tmp = gs.ground_spec(spec)
            ground_specs.update(set(tmp))
        return ground_specs


    @staticmethod
    def _simplify_trace(trace, ground_specs):
        """ Collect all the symbols appearing in the ground
        specifications

        Remove all the messages in the trace that do not
        correspond to a symbol from the above set.

        Caveat: we still keep the top-level callbacks even if
        they are not in the set but they contain a messsage that
        is included.

        WARNING: the simplification is UNSOUND

        The result is a new trace.
        """
        def simplify_msg(parent, trace_msg, spec_msg):
            for child in trace_msg.children:
                if (TSEncoder.get_key_from_msg(child, TSEncoder.ENTRY) in spec_msg or
                    TSEncoder.get_key_from_msg(child, TSEncoder.EXIT) in spec_msg):
                    # Keep both entry and exit for now
                    new_parent = copy.copy(child)
                    new_parent.children = []
                    parent.add_msg(new_parent)
                else:
                    # skip child if it is not in the set
                    new_parent = parent
                simplify_msg(new_parent, child, spec_msg)

        logging.warning("The simplification of the trace is UNSOUND")

        # collect the calls appearing in the ground specs
        spec_msgs = set()
        for spec in ground_specs:
            for call in spec.get_spec_calls():
                spec_msgs.add(TSEncoder.get_key_from_call(call))

        # reconstruct the trace ignoring symbols not in spec_calls
        new_trace = CTrace()
        for cb in trace.children:
            parent = copy.copy(cb)
            parent.children = []
            simplify_msg(parent, cb, spec_msgs)

            if ((TSEncoder.get_key_from_msg(cb, TSEncoder.ENTRY) in spec_msgs or
                 TSEncoder.get_key_from_msg(cb, TSEncoder.EXIT) in spec_msgs) or
                len(parent.children) > 0):
                new_trace.add_msg(parent)

        return new_trace


    def _encode(self):
        """ Function that performs the actual encoding of the TS.

        The function performs the following steps:

        1. Encode all the variables of the system
        2. Encode the effects of the specifications
        3. Encode the execution of the top-level callbacks and the
        error conditions
        """
        logging.info("Generating the encoding...")

        self.ts = TransitionSystem()

        # 1. Encode all the variables of the system
        logging.info("Encoding the variables...")
        vars_ts = self._encode_vars()
        self.ts.product(vars_ts)
        logging.info("Done encoding the variables.")

        # 2. Specs ts
        logging.info("Encoding the specification...")
        (spec_ts, disabled_msg, accepting) = self._encode_ground_specs()
        self.ts.product(spec_ts)
        logging.info("Done encoding the specification.")

        # 3. Encode the execution of the top-level callbacks
        logging.info("Encoding the trace...")
        (cb_ts, errors) = self._encode_cbs(disabled_msg)
        self.ts.product(cb_ts)
        self.error_prop = FALSE_PYSMT()
        for e in errors:
            self.error_prop = Or(self.error_prop, e)
        self.mapback.set_error_condition(self.error_prop)
        logging.info("Done encoding the trace.")

        self._encode_initial_conditions()
        logging.info("Done generating the encoding.")

        logging.info("Miscellaneous stats:")
        logging.info("Trace length: %d" % (self.trace_length))
        logging.info("Total messages: %d" % (len(self.msgs)))
        logging.info("Top-level callbacks: %d" % (len(self.trace.children)))
        logging.info("Ground specs: %d" % (len(self.ground_specs)))
        logging.info("State variables: %d" % (len(self.ts.state_vars)))
        logging.info("Input variables: %d" % (len(self.ts.input_vars)))

        self.ts.init = simplify(self.ts.init)
        self.ts.trans = simplify(self.ts.trans)


    def _encode_ground_specs(self):
        """ Encode the set of ground specifications.

        Returns the transition system that encodes the effects of the
        specification and the set of messages disabled_msg.
        disabled_msg is the set
        of callin messages that can be disabled by some specification.
        """

        ts = TransitionSystem()

        # Accepting is a map from messages to set of states where the
        # message enabled status is changed (because the system matched
        # a regular expression in the specification).
        # In practice, these are the accepting states of the automaton.
        accepting = {}
        disabled_msg = set()
        spec_id = 0
        for ground_spec in self.ground_specs:
            msg = get_spec_rhs(ground_spec.ast)
            key = TSEncoder.get_key_from_call(msg)

            if ground_spec.is_disable():
                if key in self.app_contr:
                    disabled_msg.add(key)

            if key not in accepting: accepting[key] = []
            gs_ts = self._get_ground_spec_ts(ground_spec,
                                             spec_id,
                                             accepting[key])
            ts.product(gs_ts)
            spec_id = spec_id + 1

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

        # If a message is not in the msg_key, then its value do not change.
        # This applies to all the messages that are not changed by a
        # specification
        for msg in self.msgs:
            if msg not in accepting:
                msg_enabled = TSEncoder._get_state_var(msg)
                fc_msg = Iff(msg_enabled,
                             Helper.get_next_var(msg_enabled,
                                                 self.pysmt_env.formula_manager))
                ts.trans = And(ts.trans, fc_msg)

        return (ts, disabled_msg, accepting)





    def _get_regexp_ts(self, regexp, spec_id):
        """ Builds the ts for the automaton.
        It returns the ts that encode the acceptance of the language.

        Resulting transition system (initial are the init state of the auto,
        trans(s) is the list of transition (s', label) from s)

        VAR pc : {0, ... num_states -1 };
        INIT:= \bigvee{s in initial} pc = s;
        TRANS
          \bigwedge{s in states}
            pc = s -> ( \bigvee{(dst,label) \in trans(s)} label and (pc' = dst) )
        This allow to re-use the same automaton across the same regexp.
        """
        def _get_pc_value(auto2ts_map, current_pc_val, auto_state):
            if not auto_state in auto2ts_map:
                current_pc_val += 1
                state_id = current_pc_val
                auto2ts_map[auto_state] = state_id
            else:
                state_id = auto2ts_map[auto_state]
            return (current_pc_val, state_id)

        ts = TransitionSystem()

        # map from ids of automaton states to the value used in the
        # counter for the transition system
        auto2ts_map = {}

        auto = self.r2a.get_from_regexp(regexp)

        # if (not regexp in self.regexp2ts):
        #     self.regexp2ts[regexp] = 1
        # else:
        #     print "DUPLICATE"
        #     #pretty_print(regexp)

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

        final_states_ts = []
        for a_s in auto.final_states:
            ts_s = auto2ts_map[a_s]
            final_states_ts.append(ts_s)

        return (auto_pc, final_states_ts, ts)


    def _get_ground_spec_ts(self, ground_spec, spec_id, accepting):
        """ Given a ground specification, returns the transition
        system that encodes the updates implied by the specification.

        It has side effects on accepting.

        Resulting transition system is the transition system of the regexp and
        the effects  on the disable/enable.

        Note that we reuse the same automaton across the same regexp.

        This is the ts that encodes the effects.

        INIT:= (pc' = s ->  enable_msg/not enable_msg)
        TRANS
          \bigwedge{s in final}
            (pc' = s ->  enable_msg/not enable_msg)

        enable_msg is the message in the rhs of the spec. It is negated if
        the spec disables it.
        """

        assert isinstance(ground_spec, Spec)

        ts = TransitionSystem()
        regexp = get_regexp_node(ground_spec.ast)
        if (regexp in self.regexp2ts):
            (auto_pc, final_states, ts_auto) = self.regexp2ts[regexp]

            # Do not compute the product twice!
            ts.state_vars = ts_auto.state_vars
            ts.input_vars = ts_auto.input_vars
        else:
            (auto_pc, final_states, ts_auto) = self._get_regexp_ts(regexp, spec_id)
            self.regexp2ts[regexp] = (auto_pc, final_states, ts_auto)
            ts.product(ts_auto)

        # Record the final states - on these states the value of the
        # rhs of the specifications change
        spec_accepting = []
        msg = get_spec_rhs(ground_spec.ast)
        key = TSEncoder.get_key_from_call(msg)
        msg_enabled = TSEncoder._get_state_var(key)
        all_vars = set(ts.state_vars)
        all_vars.add(msg_enabled)
        for ts_s in final_states:
            eq_current = self.cenc.eq_val(auto_pc, ts_s)

            # add the current state to the accepting states
            spec_accepting.append(eq_current)

            # encode the fact that the message must be
            # enabled/disabled in *this* state
            if (ground_spec.is_disable()):
                effect = Not(msg_enabled)
            else:
                assert ground_spec.is_enable()
                effect = msg_enabled
            effect = Implies(eq_current, effect)

            ts.init = And(ts.init, effect)

            effect_in_trans = self.helper.get_next_formula(all_vars, effect)

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

        self.mapback.add_state_vars(var_ts.state_vars)

        return var_ts


    def _encode_cbs(self, disabled_msg):
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

        # TODO: Fix the length of the trace, adding the exit messages!

        pc_size = (self.trace_length * 2) - tl_callback_count + 1 + 1

        max_pc_value = pc_size - 1

        # print self.trace_length
        # print tl_callback_count
        # print "MAX"
        # print max_pc_value

        pc_name = TSEncoder._get_pc_name()
        self.cenc.add_var(pc_name, max_pc_value) # starts from 0
        self.mapback.set_pc_var(pc_name)
        self.mapback.add_encoder(pc_name, self.cenc)

        # The last state is the error one
        error_state_id = max_pc_value
        logging.debug("%d is the error state: " % error_state_id)

        # add all the bit variables
        for v in self.cenc.get_counter_var(pc_name):
            ts.add_var(v)

        # start from the initial state
        ts.init = self.cenc.eq_val(pc_name, 0)
        logging.debug("Init state: %d" % (0))

        offset = 0
        ts.trans = FALSE_PYSMT() # disjunction of transitions
        # encode each cb
        for tl_cb in self.trace.children:
            # dfs on the tree of messages
            state_count = 0
            current_state = 0

            # (True, tl_cb)  -> True if it is the entry message
            # (False, tl_cb) -> False if it is the exit message
            stack = [(TSEncoder.EXIT, tl_cb), (TSEncoder.ENTRY, tl_cb)]
            while (len(stack) != 0):
                (entry_type, msg) = stack.pop()

                msg_key = TSEncoder.get_key_from_msg(msg, entry_type)
                msg_enabled = TSEncoder._get_state_var(msg_key)

                # print "%s/%s"% (entry_type, msg_key)

                # Fill the stack in reverse order
                # Add the child only if pre-visit
                if (entry_type == TSEncoder.ENTRY):
                    for i in reversed(range(len(msg.children))):
                        stack.append((TSEncoder.EXIT, msg.children[i]))
                        stack.append((TSEncoder.ENTRY, msg.children[i]))

                # encode the transition
                if (len(stack) == 0):
                    # visited all the cb/ci of the top-level cb
                    if offset < current_state:
                        # handle 0 -> 0 transition used for callbacks with no ci
                        offset = current_state
                    next_state = 0
                else:
                    state_count += 1
                    # add the offset when we move to an inner message
                    next_state = state_count + offset

                # Encode the enabled transition
                label = And(self.r2a.get_msg_eq(msg_key), msg_enabled)
                s0 = self.cenc.eq_val(pc_name, current_state)
                self.mapback.add_pc2trace(current_state,
                                          next_state,
                                          (entry_type,msg), msg_key)
                self.mapback.add_trans2pc((entry_type,msg), current_state, next_state)

                snext = self.cenc.eq_val(pc_name, next_state)
                snext = self.helper.get_next_formula(ts.state_vars, snext)
                single_trans = And([s0, label, snext])
                ts.trans = Or([ts.trans, single_trans])

                logging.debug("Trans: %d -> %d on %s" % (current_state, next_state, msg_key))

                # encode the transition to the error state
                if (msg_key in disabled_msg and ((isinstance(msg, CCallin) and entry_type == TSEncoder.ENTRY) or
                                                 (isinstance(msg, CCallback) and entry_type == TSEncoder.EXIT))):
                    logging.debug("Error condition: %s not enabled" % str(msg_enabled))
                    error_label = And(Not(msg_enabled),
                                      self.r2a.get_msg_eq(self.error_label))
                    error_state = self.cenc.eq_val(pc_name, error_state_id)
                    snext_error = self.helper.get_next_formula(ts.state_vars,
                                                               error_state)
                    single_trans = And([s0, error_label, snext_error])
                    logging.debug("Error transition: %d -> %d on %s" % (current_state, error_state_id, error_label))
                    ts.trans = Or([ts.trans, single_trans])

                    if error is None:
                        error = self.cenc.eq_val(pc_name, max_pc_value)

                    self.mapback.add_pc2trace(current_state,
                                              error_state_id,
                                              (entry_type,msg),
                                              self.error_label)
                    # self.mapback.add_trans2pc((entry_type,msg), current_state, error_state_id)
                    # DEBUG
                    self.mapback.add_trans2pc((entry_type,msg,self.error_label), current_state, error_state_id)

                current_state = next_state

        # Add self loop on error state to avoid deadlocks
        # WARNING: we can still have deadlocks due to internal callbacks that
        # are disabled.
        error_label = And(self.r2a.get_msg_eq(self.error_label))
        error_state = self.cenc.eq_val(pc_name, error_state_id)
        snext_error = self.helper.get_next_formula(ts.state_vars,
                                                   error_state)
        single_trans = And([error_state, error_label, snext_error])
        self.mapback.add_pc2trace(error_state_id,
                                  error_state_id,
                                  self.error_label,
                                  self.error_label)

        ts.trans = Or([ts.trans, single_trans])

        if error is None:
            errors = []
        else:
            errors = [error]
        return (ts, errors)


    def _encode_initial_conditions(self):
        """ Initial condition:
        All the messages that are not specifically disabled/disallowed are
        enalbed/allowed
        """
        solver = self.pysmt_env.factory.Solver(quantified=False,
                                               name="z3",
                                               logic=QF_BOOL)
        solver.add_assertion(self.ts.init)

        for msg in self.msgs:
            msg_var = TSEncoder._get_state_var(msg)
            solver.push()
            solver.add_assertion(msg_var)
            can_be_enabled = solver.solve()
            solver.pop()

            if (can_be_enabled):
                self.ts.init = And(self.ts.init, msg_var)


    @staticmethod
    def _get_pc_name():
        atom_name = "pc"
        return atom_name

    @staticmethod
    def _get_state_var(key):
        atom_name = "enabled_" + key
        return Symbol(atom_name, BOOL)

    @staticmethod
    def get_key(retval, call_type, entry_type, method_name, params):
        assert method_name is not None
        assert params is not None
        assert method_name != ""

        assert call_type == "CI" or call_type == "CB"
        assert entry_type == TSEncoder.ENTRY or entry_type == TSEncoder.EXIT

        string_params = [str(f) for f in params]

        if (retval != None and entry_type == TSEncoder.EXIT):
            # ADD return value only for EXIT
            key = "%s=[%s]_[%s]_%s(%s)" % (retval,
                                           call_type,
                                           entry_type,
                                           method_name,
                                           ",".join(string_params))
        else:
            key = "[%s]_[%s]_%s(%s)" % (call_type ,
                                        entry_type,
                                        method_name,
                                        ",".join(string_params))
        return key

    @staticmethod
    def get_key_from_msg(msg, entry_type):
        """ The input is a msg from a concrete trace.
        The output is the key to the message

        The message must also be paired with the entry/exit information.
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
            p_value = TSEncoder.get_value_key(p)
            params.append(p_value)

        full_msg_name = msg.get_full_msg_name()
        return TSEncoder.get_key(retval, msg_type, entry_type, full_msg_name, params)

    @staticmethod
    def get_key_from_call(call_node):
        """ Works for grounded call node """
        assert (get_node_type(call_node) == CALL_ENTRY or
                get_node_type(call_node) == CALL_EXIT)

        if (get_node_type(call_node) == CALL_EXIT):
            node_retval = get_call_assignee(call_node)
            if (new_nil() != node_retval):
                retval_val = TraceSpecConverter.specnode2traceval(node_retval)
                retval = TSEncoder.get_value_key(retval_val)
            else:
                retval = None
        else:
            retval = None

        node_call_type = get_call_type(call_node)
        if (get_node_type(node_call_type) == CI):
            call_type = "CI"
        elif (get_node_type(node_call_type) == CB):
            call_type = "CB"
        else:
            assert False

        entry_type = TSEncoder.ENTRY if get_node_type(call_node) == CALL_ENTRY else TSEncoder.EXIT

        method_name_node = get_call_signature(call_node)

        assert (ID == get_node_type(method_name_node))
        method_name = get_id_val(method_name_node)
        receiver = get_call_receiver(call_node)

        if (new_nil() != receiver):
            param_val = TraceSpecConverter.specnode2traceval(receiver)
            params = [TSEncoder.get_value_key(param_val)]
        else:
            params = []

        node_params = get_call_params(call_node)

        while (PARAM_LIST == get_node_type(node_params)):
            p_node = get_param_name(node_params)
            p = TraceSpecConverter.specnode2traceval(p_node)
            p_value = TSEncoder.get_value_key(p)
            params.append(p_value)
            node_params = get_param_tail(node_params)

        return TSEncoder.get_key(retval, call_type, entry_type,
                                 method_name, params)


    @staticmethod
    def get_value_key(value):
        """ Given a value returns its representation
        that will be used in the message key """

        assert (isinstance(value, CValue))

        value_repr = value.get_value()

        return value_repr

    def get_trace_stats(self):
        # count the total number of messages and returns the set of
        # messages of the trace
        trace_length = 0
        msgs = set()

        fmwk_contr = set()
        app_contr = set()

        stack = []
        for msg in self.trace.children:
            stack.append(msg)

        while (len(stack) != 0):
            msg = stack.pop()
            trace_length = trace_length + 1

            # Add ENTRY
            key = TSEncoder.get_key_from_msg(msg, TSEncoder.ENTRY)
            msgs.add(key)
            if (isinstance(msg, CCallback)): fmwk_contr.add(key)
            else: app_contr.add(key)

            # Add EXIT
            key = TSEncoder.get_key_from_msg(msg, TSEncoder.EXIT)
            msgs.add(key)
            if (isinstance(msg, CCallback)): app_contr.add(key)
            else: fmwk_contr.add(key)

            for msg2 in msg.children:
                stack.append(msg2)

        return (trace_length, msgs, fmwk_contr, app_contr)


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

        self.msg2trans = {}

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

        # set of state variables
        self.state_vars = set()

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

    def add_pc2trace(self, value, next_value, trace_msg, msg_key):
        assert self.pc_var is not None
        self.pc2trace[(self.pc_var, value, next_value, msg_key)] = trace_msg

    def add_trans2pc(self, msg, current_state, next_state):
        self.msg2trans[msg] = (current_state, next_state)

    def set_error_condition(self, error_condition):
        self.error_condition = error_condition

    def _get_pc_value(self, var, current_state):
        assert var in self.vars_encoders
        counter_enc = self.vars_encoders[var]

        value = counter_enc.get_counter_value(var, current_state)

        return value

    def _get_msg_for_model(self, var_map, var, current_state):
        assert var in self.vars_encoders

        counter_enc = self.vars_encoders[var]
        value = self._get_pc_value(var, current_state)

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


    def get_fired_trace_msg(self, current_state, next_state):
        """ Given the models for the current states, returns
        the correspondent message in the trace that was executed.
        """

        trans_label = self.get_trans_label(current_state)

        assert self.pc_var in self.vars_encoders
        counter_enc = self.vars_encoders[self.pc_var]
        value = self._get_pc_value(self.pc_var, current_state)
        next_value = self._get_pc_value(self.pc_var, next_state)

        key = (self.pc_var, value, next_value, trans_label)
        if key in self.pc2trace:
            return self.pc2trace[key]
        else:
            return None

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

    def get_trans2pc(self, msg):
        return self.msg2trans[msg]

    def add_state_vars(self, set_vars):
        self.state_vars.update(set_vars)

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
        #deterministic = res.determinize()
        deterministic = res.minimize()
        return deterministic

    def get_from_regexp_aux(self, regexp):
        node_type = get_node_type(regexp)

        if (node_type in [TRUE,FALSE,CALL_ENTRY,CALL_EXIT,AND_OP,OR_OP,NOT_OP]):
            # base case
            # accept the atoms in the bexp
            formula = self.get_be(regexp)
            label = self.auto_env.new_label(formula)
            automaton = Automaton.get_singleton(label, self.auto_env)
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
        elif (node_type == CALL_ENTRY or node_type == CALL_EXIT):
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

