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

b. We build a single automaton for each ground specification.
This can lead to an explosion in the state space.

c. Other standard bottlenecks: e.g. recursive vs. iterative, no
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
- We already merge together the automata that are equivalent.

  We could further perform the union of different regexp automata to reduce the state space.
  For example, we can perform the union of all the automata that have
  the same effect on the transition system.
  Here we will have a tradeoff between the composed representation of
  the automata and the monolithic one (WARNING: the states of the monolithic
  automaton can explode since we need a complete and deterministic automaton).



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
from cbverifier.encoding.encoder_utils import EncoderUtils
from cbverifier.encoding.automata import Automaton, AutoEnv
from cbverifier.encoding.counter_enc import CounterEnc
from cbverifier.encoding.grounding import GroundSpecs
from cbverifier.encoding.conversion import TraceSpecConverter
from cbverifier.encoding.flowdroid_model.flowdroid_model_builder import FlowDroidModelBuilder
from cbverifier.utils.stats import Stats
from cbverifier.helpers import Helper

DEBUG_AUTO = False

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

    def __init__(self, trace, specs, ignore_msgs = False,
                 stats = None, use_flowdroid_model = False):
        # 1. copy the trace removing the top-level exception
        self.trace = trace.copy(True)
        self.specs = specs
        self.ts = None
        self.error_prop = None
        self.stats = stats
        self.use_flowdroid_model = use_flowdroid_model

        # 2. computes the ground specification
        logging.info("Total number of specs (before grounding): %d" % (len(specs)))
        self.gs = GroundSpecs(self.trace)
        self.ground_specs = TSEncoder._compute_ground_spec(self.gs, self.specs,
                                                           self.stats)
        logging.info("Total specs after grounding: %d" % (len(self.ground_specs)))

        # initializes the informations needed to compute the FlowDroid model
        if (self.use_flowdroid_model):
            # [TODO] Add check to verify that we do not have enable/disable
            # in the current set of specification
            msg_key_sets = set()
            for spec in self.ground_specs:
                for call in spec.get_spec_calls():
                    msgs_key_sets.add(EncoderUtils.get_key_from_call(call))

            self.flowdroid_model_builder = FlowDroidModelBuilder(self.trace,
                                                                 msg_key_sets)
        else:
            self.flowdroid_model_builder = None

        # 3. Remove all the messages in the trace that do not
        # appear in the specification.
        if (ignore_msgs):
            # collect the calls appearing in the ground specs
            if (self.use_flowdroid_model):
                self.spec_msgs = self.flowdroid_model_builder.get_msgs_keys()
            else:
                self.spec_msgs = set()
                for spec in self.ground_specs:
                    for call in spec.get_spec_calls():
                        self.spec_msgs.add(EncoderUtils.get_key_from_call(call))

            # Collect the statistics on the trace
            self._is_msg_visible = self._is_msg_visible_all
            (trace_length, msgs, fmwk_contr, app_contr) = self.get_trace_stats()

            self.trace = TSEncoder._simplify_trace(self.trace,
                                                   self.spec_msgs)
            self._is_msg_visible = self._is_msg_visible_simpl
            print("\n---Simplified Trace---")
            self.trace.print_trace(sys.stdout)
            print("\n")
        else:
            self._is_msg_visible = self._is_msg_visible_all

        # 4. Initialize the data structures needed to construct the encoding
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

                msg_enc = self.mapback.get_trans2pc((EncoderUtils.ENTRY, cb))
                key = EncoderUtils.get_key_from_msg(cb, EncoderUtils.ENTRY)
                if not self._is_msg_visible(key):
                    raise Exception("Message id %s not found in the (simplified) trace" % message_id)

                tl_cbs.append(cb)
        else:
            tl_cbs = self.trace.children

        # encode each callback
        # No trace constraints in the initial state
        trace_encoding = []
        pc_name = EncoderUtils._get_pc_name()
        for tl_cb in tl_cbs:
            stack = [(EncoderUtils.EXIT, tl_cb),(EncoderUtils.ENTRY, tl_cb)]

            while (len(stack) != 0):
                (entry_type, msg) = stack.pop()

                # Fill the stack in reverse order
                if (EncoderUtils.ENTRY == entry_type):
                    for i in reversed(range(len(msg.children))):
                        stack.append((EncoderUtils.EXIT, msg.children[i]))
                        stack.append((EncoderUtils.ENTRY, msg.children[i]))

                msg_key = EncoderUtils.get_key_from_msg(msg, entry_type)
                if not self._is_msg_visible(msg_key):
                    continue

                msg_enc = self.mapback.get_trans2pc((entry_type, msg))
                assert(msg_enc is not None)

                (current_state, next_state) = msg_enc
                s0 = self.cenc.eq_val(pc_name, current_state)
                # strengthen s0 - progress only if the message is enabled
                msg_enabled = EncoderUtils._get_state_var(msg_key)
                s0 = And(s0, msg_enabled)
                s1 = self.cenc.eq_val(pc_name, next_state)

                current_step = str(len(trace_encoding) + 1)
                logging.info("SIMULATION: step %s on %s" % (current_step, msg_key))
                logging.debug("Simulation debug - transition from %s -> %s" % (current_state,next_state))
                try:
                    msg_error_enc = self.mapback.get_trans2pc((entry_type, msg, self.error_label))
                    info_msg = """SIMULATION - transition at step %s could not happen if %s is not allowed (%s -> %s in the encoding).
Simulation only executes the nominal trace and disregards errors.
If simulation iterrupts here, it could be due to the bug""" % (current_step, msg_key, str(current_state), str(next_state))
                    logging.info(info_msg)
                    # if msg_error_enc is not None:
                    #     # this is a possible error state
                    #     msg_key = EncoderUtils.get_key_from_msg(msg, entry_type)
                    #     msg_enabled = EncoderUtils._get_state_var(msg_key)
                    #     # progress only if the message is enabled
                    #     s0 = And(s0, msg_enabled)
                except KeyError:
                    pass
                trace_encoding.append((s0,s1))

        return trace_encoding


    def get_ground_spec(self):
        """
        Returns the list of ground specifications
        """
        return self.ground_specs

    def get_orig_ground_spec(self):
        """
        Returns a map where the key is one of the original
        specifications, and the value is the list of specification
        obtained by grounding the original spec.
        """

        ground_spec_map = {}
        for spec in self.ground_specs:
            orig_spec = self.gs.get_source_spec(spec)
            assert orig_spec is not None

            if orig_spec in ground_spec_map:
                spec_list = ground_spec_map[orig_spec]
            else:
                spec_list = []
                ground_spec_map[orig_spec] = spec_list
            spec_list.append(spec)

        return ground_spec_map


    @staticmethod
    def _compute_ground_spec(gs, specs, stats = None):
        """ Computes all the ground specifications from the
        specifications with free variables in self.spec and the
        concrete trace self.trace

        Return a list of ground specifications.
        """

        if stats is not None:
            stats.start_timer(stats.SPEC_GROUNDING_TIME)

        ground_specs = set()
        for spec in specs:
            logging.debug("Grounding spec: %s" % str(spec))
            tmp = gs.ground_spec(spec)
            logging.debug("Found %d concrete specs" % len(tmp))
            ground_specs.update(set(tmp))

        if stats is not None:
            stats.stop_timer(stats.SPEC_GROUNDING_TIME)
            stats.write_times(sys.stdout, stats.SPEC_GROUNDING_TIME)

        return ground_specs


    def _is_msg_visible_all(self, msg_key):
        return True

    def _is_msg_visible_simpl(self, msg_key):
        return msg_key in self.spec_msgs

    @staticmethod
    def _simplify_trace(trace, spec_msgs):
        """ Collect all the symbols appearing in the ground
        specifications

        Remove all the messages in the trace that do not
        correspond to a symbol from the above set.

        Caveat: we still keep the top-level callbacks even if
        they are not in the set but they contain a messsage that
        is included.

        Side effect on spec_msgs

        WARNING: the simplification is UNSOUND

        The result is a new trace.
        """
        def simplify_msg(parent, trace_msg, spec_msg):
            for child in trace_msg.children:
                if (EncoderUtils.get_key_from_msg(child, EncoderUtils.ENTRY) in spec_msg or
                    EncoderUtils.get_key_from_msg(child, EncoderUtils.EXIT) in spec_msg):
                    # Keep both entry and exit for now
                    new_parent = copy.copy(child)
                    new_parent.children = []
                    parent.add_msg(new_parent)
                else:
                    # skip child if it is not in the set
                    new_parent = parent
                simplify_msg(new_parent, child, spec_msg)

        # reconstruct the trace ignoring symbols not in spec_calls
        new_trace = CTrace()
        for cb in trace.children:
            parent = copy.copy(cb)
            parent.children = []
            simplify_msg(parent, cb, spec_msgs)

            # always add the ENTRY of the tl callback
            if ((EncoderUtils.get_key_from_msg(cb, EncoderUtils.ENTRY) in spec_msgs or
                 EncoderUtils.get_key_from_msg(cb, EncoderUtils.EXIT) in spec_msgs) or
                len(parent.children) > 0):
                new_trace.add_msg(parent)

                # print spec_msgs
                # print EncoderUtils.get_key_from_msg(cb, EncoderUtils.ENTRY) in spec_msgs
                # print EncoderUtils.get_key_from_msg(cb, EncoderUtils.EXIT) in spec_msgs
                # print len(parent.children) > 0

                if ( ( not EncoderUtils.get_key_from_msg(cb, EncoderUtils.ENTRY) in spec_msgs) and
                     len(parent.children) > 0):
                    # CB included by its children
                    msg_key = EncoderUtils.get_key_from_msg(cb, EncoderUtils.ENTRY)
                    spec_msgs.add(msg_key)

        return new_trace


    def _encode(self):
        """ Function that performs the actual encoding of the TS.

        The function performs the following steps:

        1. Encode all the variables of the system
        2. Encode the effects of the specifications
        3. Encode the FlowDroid model of callbacks, if the option
           is enabled
        4. Encode the execution of the top-level callbacks and the
           error conditions
        5. Encode the initial condition
        """
        if self.stats is not None:
            self.stats.start_timer(self.stats.ENCODING_TIME)

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

        # 3. Encode the FlowDroid model (if the option is enabled)
        if (self.use_flowdroid_model):
            assert self.flowdroid_model_builder is not None
            self.flowdroid_model_builder.encode()

        # 4. Encode the execution of the top-level callbacks
        logging.info("Encoding the trace...")
        (cb_ts, errors) = self._encode_cbs(disabled_msg)
        self.ts.product(cb_ts)
        self.error_prop = FALSE_PYSMT()
        for e in errors:
            self.error_prop = Or(self.error_prop, e)
        self.mapback.set_error_condition(self.error_prop)
        logging.info("Done encoding the trace.")

        # 5. Encode the initial condition
        self._encode_initial_conditions()
        logging.info("Done generating the encoding.")

        logging.info("Miscellaneous stats:")
        logging.info("Ground specs: %d" % (len(self.ground_specs)))

        logging.info("State variables: %d" % (len(self.ts.state_vars)))
        logging.info("Input variables: %d" % (len(self.ts.input_vars)))

        self.ts.init = simplify(self.ts.init)
        self.ts.trans = simplify(self.ts.trans)

        if self.stats is not None:
            self.stats.stop_timer(self.stats.ENCODING_TIME)
            self.stats.write_times(sys.stdout, self.stats.ENCODING_TIME)


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
            key = EncoderUtils.get_key_from_call(msg)

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
            msg_enabled = EncoderUtils._get_state_var(msg_key)

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

        # [TODO] When using the FlowDroid model, be sure that we do not add
        # the frame condition for all the back messages!
        # This works under the assumption that the FlowDroid model is never used
        # when the specification has any enabled/disabled rule
        if (self.use_flowdroid_model):
            raise NotImplementedError("Fix generation of frame condition when "\
                                      "using the FlowDroid model")

        # If a message is not in the msg_key, then its value do not change.
        # This applies to all the messages that are not changed by a
        # specification
        for msg in self.msgs:
            if msg not in accepting:
                msg_enabled = EncoderUtils._get_state_var(msg)
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

        # program counter of the automaton
        auto_pc = "spec_pc_%d" % spec_id
        self.cenc.add_var(auto_pc, auto.count_state() - 1) # -1 since it starts from 0
        for v in self.cenc.get_counter_var(auto_pc): ts.add_var(v)

        # Rude debugging of the automaton encoding
        # Leave it here for now.
        if DEBUG_AUTO:
            pretty_print(regexp, sys.stdout)
            auto.to_dot(sys.stdout)
            print auto_pc

        # initial states
        # Initially we are in one of the initial states
        # There should be a single initial state though since the automaton
        # is deterministic
        assert len(auto.initial_states) > 0
        current_pc_val = -1
        ts.init = FALSE_PYSMT()
        for a_init in auto.initial_states:
            (current_pc_val, s_id) = _get_pc_value(auto2ts_map,
                                                   current_pc_val,
                                                   a_init)

            #logging.debug("One of init: %s = %d" % (auto_pc,s_id))

            eq_current = self.cenc.eq_val(auto_pc, s_id)
            ts.init = Or(ts.init, eq_current)

            if DEBUG_AUTO:
                print "INIT: %s = %d" % (auto_pc, s_id)



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

                if DEBUG_AUTO:
                    print "TRANS - %s: %d -> %d" % (auto_pc, ts_s, ts_dst)

            s_trans = Implies(eq_current, s_trans)
            ts.trans = And(ts.trans, s_trans)

        final_states_ts = []
        for a_s in auto.final_states:
            ts_s = auto2ts_map[a_s]
            final_states_ts.append(ts_s)

            if DEBUG_AUTO:
                print "FINAL - %s: %d\n" % (auto_pc, ts_s)

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
            # # DEBUG
            # stringio = StringIO()
            # pretty_print(regexp, stringio)
            # logging.info("Creating automata for spec: %s\n" % (stringio.getvalue()))

            (auto_pc, final_states, ts_auto) = self._get_regexp_ts(regexp, spec_id)
            self.regexp2ts[regexp] = (auto_pc, final_states, ts_auto)
            ts.product(ts_auto)

        # Record the final states - on these states the value of the
        # rhs of the specifications change
        spec_accepting = []
        msg = get_spec_rhs(ground_spec.ast)
        key = EncoderUtils.get_key_from_call(msg)
        msg_enabled = EncoderUtils._get_state_var(key)
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
        self.mapback.add_var2spec(EncoderUtils._get_state_var(key),
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
            var = EncoderUtils._get_state_var(msg)
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

        pc_size = (self.trace_length) - tl_callback_count + 1 + 1

        max_pc_value = pc_size - 1

        pc_name = EncoderUtils._get_pc_name()
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


        def add_msgs_to_stack(stack, msg):
            exit_key = EncoderUtils.get_key_from_msg(msg, EncoderUtils.EXIT)
            if self._is_msg_visible(exit_key):
                stack.append((EncoderUtils.EXIT, msg))

            entry_key = EncoderUtils.get_key_from_msg(msg, EncoderUtils.ENTRY)
            if self._is_msg_visible(entry_key):
                stack.append((EncoderUtils.ENTRY, msg))

        offset = 0
        ts.trans = FALSE_PYSMT() # disjunction of transitions
        # encode each cb
        for tl_cb in self.trace.children:
            # dfs on the tree of messages
            state_count = 0
            current_state = 0

            # (True, tl_cb)  -> True if it is the entry message
            # (False, tl_cb) -> False if it is the exit message
            stack = []
            add_msgs_to_stack(stack, tl_cb)
            while (len(stack) != 0):
                (entry_type, msg) = stack.pop()
                msg_key = EncoderUtils.get_key_from_msg(msg, entry_type)
                msg_enabled = EncoderUtils._get_state_var(msg_key)
                assert self._is_msg_visible(msg_key)

                # Fill the stack in reverse order
                # Add the child only if pre-visit
                if (entry_type == EncoderUtils.ENTRY):
                    for i in reversed(range(len(msg.children))):
                        msg_i = msg.children[i]
                        add_msgs_to_stack(stack, msg_i)

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
                if (msg_key in disabled_msg and ((isinstance(msg, CCallin) and entry_type == EncoderUtils.ENTRY) or
                                                 (isinstance(msg, CCallback) and entry_type == EncoderUtils.EXIT))):
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
            msg_var = EncoderUtils._get_state_var(msg)
            solver.push()
            solver.add_assertion(msg_var)
            can_be_enabled = solver.solve()
            solver.pop()

            if (can_be_enabled):
                self.ts.init = And(self.ts.init, msg_var)

    def get_trace_stats(self):
        # count the total number of messages and returns the set of
        # messages of the trace
        trace_length = 0
        msgs = set()

#        fmwk_contr = set()
#        app_contr = set()

        ci_entry = set()
        ci_exit = set()
        cb_entry = set()
        cb_exit = set()

        stack = []
        for msg in self.trace.children:
            stack.append(msg)

        while (len(stack) != 0):
            msg = stack.pop()

            # Add ENTRY
            key = EncoderUtils.get_key_from_msg(msg, EncoderUtils.ENTRY)
            if self._is_msg_visible(key):
                trace_length = trace_length + 1
                msgs.add(key)
                if (isinstance(msg, CCallback)):
#                    fmwk_contr.add(key)
                    cb_entry.add(key)
                else:
#                    app_contr.add(key)
                    ci_entry.add(key)

            # Add EXIT
            key = EncoderUtils.get_key_from_msg(msg, EncoderUtils.EXIT)
            if self._is_msg_visible(key):
                trace_length = trace_length + 1
                msgs.add(key)
                if (isinstance(msg, CCallback)):
#                    app_contr.add(key)
                    cb_exit.add(key)
                else:
#                    fmwk_contr.add(key)
                    ci_exit.add(key)

            for msg2 in msg.children:
                stack.append(msg2)

        sys.stdout.write("""
TRACE STATISTICS
Trace length: %d
Top-level callbacks: %d
CI-ENTRY: %d
CI-EXIT: %d
CB-ENTRY: %d
CB-EXIT: %d
        """ % (trace_length, len(self.trace.children),
               len(ci_entry), len(ci_exit),
               len(cb_entry), len(cb_exit)))

        cb_entry.update(ci_exit)
        fmwk_contr = cb_entry

        ci_entry.update(cb_exit)
        app_contr = ci_entry

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
        key = EncoderUtils.get_key_from_call(call_node)
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

        if (node_type in [TRUE,FALSE,CALL_ENTRY,CALL_EXIT]):
            # base case
            # accept the atoms in the bexp
            formula = self.get_be(regexp)
            label = self.auto_env.new_label(formula)
            automaton = Automaton.get_singleton(label, self.auto_env)
            return automaton
        elif (node_type == AND_OP):
            lhs = self.get_from_regexp_aux(regexp[1])
            rhs = self.get_from_regexp_aux(regexp[2])

            automaton = lhs.intersection(rhs)

            lhs = None
            rhs = None
            return automaton
        elif (node_type == OR_OP):
            lhs = self.get_from_regexp_aux(regexp[1])
            rhs = self.get_from_regexp_aux(regexp[2])

            automaton = lhs.union(rhs)

            lhs = None
            rhs = None
            return automaton
        elif (node_type == NOT_OP):
            lhs = self.get_from_regexp_aux(regexp[1])

            automaton = lhs.complement()

            lhs = None
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
        else:
            raise UnexpectedSymbol(be_node)


class FlowDroidModelBuilder:
    """ We follow the description in Section 3 "Precise Modeling of Lifecycle" of:
    'FlowDroid: Precise Context, Flow, Field, Object-sensitive
    and Lifecycle-aware Taint Analysis for Android Apps',
    Artz et al, PLDI 14

    and in particular the implementation in:
    soot-infoflow/src/soot/jimple/infoflow/entryPointCreators/
    AndroidEntryPointCreator.java
    in the repo secure-software-engineering/FlowDroid,
    commit a1438c2b38a6ba453b91e38b2f7927b6670a2702.

      Activity lifecycle: generateActivityLifecycle, line 774

    We encode the lifecylce of each component forcing that at most one component
    can be active at each time.
    For each component, there is a different definition of active. For example,
    an activity component is active after the onResume and before the onPause
    callbacks.

    We follow the modeling where callbacks cannot happen if the component
    that register them is not active.
    We compute an over-approximation of the registration of components
    from the trace.

    We model the lifecycle for activity and fragment components since we
    are interested in components that run in the UI thread.

    As done in flowdroid, we encode the lifecycle component of fragment
    inside their activity component."""

    def __init__(self, enc, fd_builder):
        self.enc = enc
        self.fd_builder = fd_builder

    def encode(self):
        """ Create an encoding of the FlowDroid model.

        Returns a transition system representing the FlowDroid model of
        the callback control-flow.

        The transition system can be composed to the disallow set of
        specification and to the callback re-ordering from the trace.
        """
        # Encode the lifecycle for each component
        lifecycles = {}
        for c in self.fd_builder.get_components():
            c_lifecycle[c] = self._encode_component_lifecycle(c)

        # The encoding of enabled callback is "global"
        # since more callback can be enabled in several
        # components
        ts_callbacks = self._encode_callbacks_in_lifecycle(lifecycles)

        # Encode the component scheduler
        # We must change the ts of the other components to add the
        # stuttering!
        ts_scheduler = self._encode_components_scheduler()

        # Compose all the components
        ts_scheduler.product(ts_callbacks)
        for c in self.fd_builder.get_components():
            ts_scheduler.product(c)

        return ts_scheduler

    def _encode_component_lifecycle(self, component):
        """ Encode the components' lifecycles

        For now we handle activities and fragments.

        The encoding is compositional and, without additional
        constraints, allow each component lifecycle to
        interleave with each other.
        """
        if (isinstance(component, Activity)):
            lifecycle_encoding = self._encode_activity_lifecycle(component)
        elif (isinstance(component, Fragment)):
            lifecycle_encoding = self._encode_fragment_lifecycle(component)
        else:
            raise Exception("Unknown component!")

        return lifecycle_encoding

    def _encode_activity_lifecycle(self, activity):
        """
        Encode the lifecycle for activity.

        Return an ActivityLcInfo object
        """

        ts = TransitionSystem()

        # Add the program counter variable to encode the lifecycle
        # is the maximum number of states in the automaton
        # encoded in the activity lifecycle
        # (see how many times pc is incremented there)
        pc_size = 18
        pc = "pc_%s" % activity.get_inst_value()
        self.cenc.add_var(pc, pc_size - 1) # -1 since it starts from 0
        for v in self.cenc.get_counter_var(pc): ts.add_var(v)

        # Start from the initial state
        pc_val = 0
        entry_label = pc_val
        ts.init = self.cenc.eq_val(pc, pc_val)

        ts.trans = FALSE_PYSMT() # disjunction of transitions

        # Encode the lifecycle

        # line 793
        pc_val = self._enc_component_step(activity,
                                          Activity.ONCREATE,
                                          ts, pc, pc_val, pc_val + 1)
        # line 795
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYCREATED,
                                          ts, pc, pc_val, pc_val + 1, True)

        # line 840
        before_onStartStmt_label = pc_val
        pc_val = self._enc_component_step(activity,
                                          Activity.ONSTART,
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)

        # line 842
        before_onActivityStarted_label = pc_val
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYSTARTED,
                                          ts, pc, pc_val, pc_val + 1,
                                          True, True)

        # line 860
        pc_val = self._enc_component_step(activity,
                                          Activity.ONRESTOREINSTANCESTATE,
                                          ts, pc, pc_val, pc_val + 1)

        before_onPostCreate_label = pc_val
        # line 859 - jump from before before_onActivityStarted_label
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYSTARTED,
                                 ts, pc,
                                 before_onActivityStarted_label, pc_val,
                                 True, True)
        # line 864
        pc_val = self._enc_component_step(activity,
                                          Activity.ONPOSTCREATE,
                                          ts, pc, pc_val, pc_val + 1)
        before_onResume_label = pc_val # 868

        # line 870
        pc_val = self._enc_component_step(activity,
                                          Activity.ONRESUME,
                                          ts, pc, pc_val, pc_val + 1)
        # line 872
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYRESUMED,
                                          ts, pc, pc_val, pc_val + 1,
                                          True)
        # line 876
        pc_val = self._enc_component_step(activity,
                                          Activity.ONPOSTRESUME,
                                          ts, pc, pc_val, pc_val + 1)

        # Now we can execute all the activity callbacks
        # We pass back this condition to encode the scheduling of the
        # activity callbacks
        activity_is_active = self._eq_val(pc, pc_val)

        # line 916
        pc_val = self._enc_component_step(activity,
                                          Activity.ONPAUSE,
                                          ts, pc, pc_val, pc_val + 1)

        # line 918
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYPAUSED,
                                          ts, pc, pc_val, pc_val + 1,
                                          True)

        # line 921
        pc_val = self._enc_component_step(activity,
                                          Activity.ONCREATEDESCRIPTION,
                                          ts, pc, pc_val, pc_val + 1)

        # line 922
        pc_val = self._enc_component_step(activity,
                                          Activity.ONSAVEINSTANCESTATE,
                                          ts, pc, pc_val, pc_val + 1)

        # line 924
        before_onActivitySaveInstanceState_label = pc_val
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYSAVEINSTANCESTATE,
                                          ts, pc, pc_val, pc_val + 1,
                                          True)
        # line 930
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYSAVEINSTANCESTATE,
                                 ts, pc, before_onActivitySaveInstanceState_label,
                                 before_onResume_label,
                                 True)

        # line 934
        before_onStop_label = pc_val
        pc_val = self._enc_component_step(activity,
                                          Activity.ONSTOP,
                                          ts, pc, pc_val, pc_val + 1)

        # line 937
        before_onActivityStopped_label = pc_val
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYSTOPPED,
                                          ts, pc, before_onActivityStopped_label,
                                          pc_val + 1,
                                          True)
        # line 943
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYSTOPPED,
                                 ts, pc,
                                 before_onActivityStopped_label,
                                 before_onStop_label,
                                 True)
        # line 952
        before_onRestart_label = pc_val
        pc_val = self._enc_component_step(activity,
                                          Activity.ONRESTART,
                                          ts, pc, before_onRestart_label, pc_val + 1)
        # line 953
        self._enc_component_step(activity,
                                 Activity.ONRESTART,
                                 ts, pc, before_onRestart_label, before_onResume_label)
        # line 958
        before_onDestroy_label = pc_val
        self._enc_component_step(activity,
                                 Activity.ONDESTROY,
                                 ts, pc, pc_val, before_onResume_label)
        # line 948
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYSTOPPED,
                                 ts, pc,
                                 pc_val,
                                 before_onDestroy_label,
                                 True)
        # line 960 - go back to the beginning
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYDESTROYED,
                                 ts, pc, 0, before_onResume_label,
                                 True)

        lc_info = ActivityLcInfo(ts, pc, pc_size)
        lc_info.add_label(ActivityLcInfo.INIT,
                          self._eq_val(pc, entry_label))
        lc_info.add_label(ActivityLcInfo.BEFORE_ONSTART,
                          self._eq_val(pc, before_onStartStmt_label))
        lc_info.add_label(ActivityLcInfo.END,
                          self._eq_val(pc, pc_val))
        lc_info.add_label(ActivityLcInfo.IS_ACTIVE,
                          activity_is_active)

        return lc_info

    def _encode_fragment_lifecycle(self, fragment):
        """
        Encode the lifecycle for activity.

        Return a FragmentLcInfo object
        """
        ts = TransitionSystem()

        pc_size = 13 # init state + 12 (+ 1) of pc counter
        pc = "pc_%s" % fragment.get_inst_value()
        self.cenc.add_var(pc, pc_size - 1) # -1 since it starts from 0
        for v in self.cenc.get_counter_var(pc): ts.add_var(v)

        pc_val = 0
        entry_label = pc_val
        ts.init = self.cenc.eq_val(pc, pc_val)

        ts.trans = FALSE_PYSMT() # disjunction of transitions

        # line 821, 820
        self._enc_component_step(fragment,
                                 Fragment.ONATTACHFRAGMENT,
                                 ts, pc, pc_val, pc_val)

        before_onAttach_label = pc_val

        # line 986
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONATTACH,
                                          ts, pc, pc_val, pc_val+1,
                                          False, True)
        # line 992
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONCREATE,
                                          ts, pc, pc_val, pc_val+1,
                                          False, True)
        before_onCreateview_label = pc_val
        # line 998
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONCREATEVIEW,
                                          ts, pc, pc_val, pc_val+1,
                                          False, True)
        # line 1003
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONVIEWCREATED,
                                          ts, pc, pc_val, pc_val+1,
                                          False, True)
        # line 1009
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONACTIVITYCREATED,
                                          ts, pc, pc_val, pc_val+1,
                                          False, True)
        before_onStart_label = pc_val
        # line 1015
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONSTART,
                                          ts, pc, pc_val, pc_val+1)
        # line 1021
        before_onResume_label = pc
        # line 1022
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONRESUME,
                                          ts, pc, pc_val, pc_val+1)
        # line 1025
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONPAUSE,
                                          ts, pc, pc_val, pc_val+1)
        # line 1026
        self._enc_component_step(fragment,
                                 Fragment.ONPAUSE,
                                 ts, pc, pc_val, before_onResume_label)

        # line 1029
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONSAVEINSTANCESTATE,
                                          ts, pc, pc_val, pc_val+1)
        # line 1032
        before_onStop_label = pc_val
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONSTOP,
                                          ts, pc, before_onStop_label,
                                          pc_val+1)
        # line 1033
        self._enc_component_step(fragment,
                                 Fragment.ONSTOP,
                                 ts, pc, before_onStop_label,
                                 before_onCreateview_label)
        # line 1034
        self._enc_component_step(fragment,
                                 Fragment.ONSTOP,
                                 ts, pc, before_onStop_label,
                                 before_onStart_label)

        # line 1037
        before_onDestroyView_label = pc_val
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONDESTROYVIEW,
                                          ts, pc, before_onDestroyView_label, pc_val+1)
        # line 1038
        self._enc_component_step(fragment,
                                 Fragment.ONDESTROYVIEW,
                                 ts, pc, before_onDestroyView_label,
                                 before_onCreateview_label)
        # line 1041
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONDESTROY,
                                          ts, pc, pc_val, pc_val+1)
        # line 1044, 1045
        before_onDetach_label = pc_val
        self._enc_component_step(fragment,
                                 Fragment.ONDETACH,
                                 ts, pc, before_onDetach_label, entry_label)

        lc_info = FragmentLcInfo(ts, pc, pc_size)
        lc_info.add_label(FragmentLcInfo.INIT,
                          self._eq_val(pc, entry_label))
        lc_info.add_label(Fragment.END,
                          self._eq_val(pc, pc_val))
        return lc_info


    def _encode_callbacks_in_lifecycle(self, lifecycles):
        """ Encode the enabledness of the callbacks attached to
        Activities and Fragment
        """
        ts = TransitionSystem()

        # Loop over all the components
        for c, lifecycle in lifecycles.iteritems():
            if (isinstance(c, Activity)):
                # computes all the messages that must be executed
                # the activity lifecycle.
                # It includes all the cb from the attached
                # components
                cb_star = set()
                stack = [c.get_inst_value()]
                while (len(stack) > 0):
                    c_id = stack.pop()

                    if c_id in self.fd_builder.compid2msg_keys:
                        cb_star.update(self.fd_builder.compid2msg_keys[c_id])

                        if (c_id in self.fd_builder.compid2msg_keys):
                            c = self.fd_builder.compid2msg_keys[c_id]
                            if isinstance(c, Fragment):
                                # Remove the instance of lifecycle callbacks
                                # of the fragment
                                cb_star.difference(c.get_lifecycle_msgs())
                    for attached_obj in self.fd_builder.attach_rel.get_related(c_id):
                        stack.append(attached_obj)

                # encodes that these messages are executed only
                # when the activity is active
                all_msg_lbl = FALSE_PYSMT()
                for msg_key in cb_star:
                    all_msg_lbl = Or(all_msg_lbl,
                                     self._get_msg_label(msg_key))
                cb_msg_enc = Implies(all_msg_lbl,
                                     lifecycle.get_label(Activity.IS_ACTIVE))
                ts.trans = And(ts.trans, cb_msg_enc)
            elif (isinstance(c, Fragment)):
                # Do nothing on fragments here
                # Callbacks are encoded inside the activity
                pass
            else:
                raise Exception("Unknown component")

        # Do nothing for the other callbacks -- they are free
        # to happen whenever

        return ts

    def _encode_components_scheduler(self):
        """ Encode the order of execution of each component
        """
        raise NotImplementedError("_encode_components_scheduler not implemented")


    def _enc_component_step(self, component,
                            component_callback,
                            ts, pc, pc_val, next_pc_val,
                            at_least_one = False,
                            optional = False):
        """ Encode one step of the lifecycle for a component

        component: The component to encode the lifecycle to
        component_callback: key to get the lifecycle callbacks to observe
        in the encoded step (e.g., Activity.ONCREATE)
        ts: the transition system that encodes the lifecycle
            *WARNING* side effect on TS
        pc: the program counter variable
        pc_val: the current program counter value

        at_least_one: at_least_one encodes the fact that the set of lifecycle
        callback may be executed more than once to go to the next state.
        It somehow encodes a {cb1, cb2, ..., cbn}+ label

        optional: if true do not stop the execution even if the
        component does not have the callback

        Return the new value of pc_val
        """

        has_callback = False
        if component.has_trace_msg(component_callback):
            cb_msgs = activity.get_trace_msgs(component_callback)

            if len(cb_msgs) > 0:
                has_callback = True
                current_pc_val_enc = self._eq_val(pc, pc_val)
                pc_val = next_pc_val
                next_pc_val_enc = self._eq_val(pc, pc_val)
                next_pc_val_enc = self._get_next_formula(ts.state_vars,
                                                         next_pc_val_enc)

                all_cb_msg_enc = FALSE_PYSMT()
                for cb_msg in cb_msgs:
                    cb_msg_enc = self._get_msg_label(cb_msg)
                    all_msg_enc = Or(all_cb_msg_enc, cb_msg_enc)

                # Move from pc to pc + 1 by observing at least one of the
                # callback
                single_trans = And(all_msg_enc, And(current_pc_val, next_pc_val_enc))

                if not at_least_one:
                    ts.trans = Or(ts.ts_trans, single_trans)
                else:
                    # Add a self loop on current_pc_val
                    # It allows to non-determinitically visit more than once
                    # the same set of callbacks
                    single_trans = And(all_msg_enc, And(current_pc_val, current_pc_val))
                    ts.trans = Or(ts.ts_trans, single_trans)

            # Block the execution in this state if the call is not
            # optional
            if not has_callback:
                if not optional:
                    # the ts cannot move in pc_val right now, so there
                    # is a deadlock

                    # advance the pc, so that we keep to encode the rest
                    # of the lifecycle as it is.
                    # while there is a deadlock in the current pc_val
                    pc_val += next_pc_val

        # note that pc_val may *not* be incremented in the optional case
        # where we do not create the intermediate state
        return pc_val


    def _eq_val(self, pc, val):
        return self.enc.cenc.eq_val(pc, val)

    def _get_msg_label(self, msg_key):
        label = self.enc.r2a.get_msg_eq(msg_key)
        return label

    def _get_next_formula(self, state_vars, formula):
        return self.enc.helper.get_next_formula(state_vars,
                                                formula)

    class LcInfo:
        def __init__(self, ts, pc, pc_size):
            self.ts = ts
            self.pc = pc
            self.pc_size =  pc_size
            self.labels = {}

        def add_label(self, label, val):
            self.labels[label] = val

        def get_label(self, label):
            # Assume the label is there
            return self.labels[label]

    class ActivityLcInfo(LcInfo):
        INIT = "init"
        BEFORE_ONSTART = "before_onstart"
        END = "end"
        IS_ACTIVE= "is_active"

        def __init__(self, ts, pc, pc_size):
            LcInfo.__init__(self, ts, pc, pc_size)

    class FragmentLcInfo(LcInfo):
        INIT = "init"
        END = "end"

        def __init__(self, ts, pc, pc_size):
            LcInfo.__init__(self, ts, pc, pc_size)
