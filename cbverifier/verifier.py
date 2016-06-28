""" Encode and solve the verification problem

The input are:
  - a concrete trace
  - a specification (a set of rules)
  - a set of bindings
  - a bound

The verifier finds a possible (spurious) permutation of the events in
the concrete trace that may cause a bug (a bug arises a disabled
callin is called).

The possible permutation of the events depend on the enabled/disabled
status of events/callins.
"""

import logging
import collections

from pysmt.environment import reset_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from pysmt.shortcuts import Solver
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL

from spec import SpecType, Spec

from ctrace import ConcreteTrace
from helpers import Helper


Instance = collections.namedtuple("Instance", ["evt", "args"],
                                  verbose=False,
                                  rename=False)

class Verifier:
    ENABLED_VAR_PREF  = "enabled_state"
    ALLOWED_VAR_PREF  = "allowed_state"
    ERROR_STATE = "error"

    def __init__(self, ctrace, specs, bindings, debug_encoding=False):
        # debug_encoding: encode additional input variables to track
        # what concrete event has been fired in each execution step.
        # By default it is false.
        #
        logging.debug("Creating verifier...")
        assert None != ctrace
        assert None != specs
        assert None != bindings

        # pysmt stuff
        self.env = reset_env()
        self.mgr = self.env.formula_manager
        self.helper = Helper(self.env)

        # concrete trace
        self.ctrace = ctrace
        # specification (list of rules)
        self.specs = specs
        # list of bindings from events to callbacks parameters
        self.bindings = bindings
        self.debug_encoding = debug_encoding
        if self.debug_encoding:
            self.debug_info = DebugInfo(self)
        else:
            self.debug_info = None

        # internal representation of the transition system
        self.ts_vars = None
        self.ts_init = None
        self.ts_trans = None
        # reachability property
        self.ts_error = None

        # Internal data structures
        self.conc_to_msg = {} # From concrete events/callin to msgs
        self.msgs_to_var = {} # Messages to Boolean variables
        self.var_to_msgs = {} # inverse map
        self.msgs_to_instances = {} # Messages to list of instances

        # Map from a concrete event in the trace to their
        # invoke variable.
        # In practice, here we have a particular instance of an event
        # It is used for debug
        self.events_to_input_var = {}

        # Initialize the transition system
        self._initialize_ts()

    def _next(self, var):
        assert var.is_symbol()
        return Helper.get_next_var(var, self.mgr)

    def _initialize_ts(self):
        """Initialize ts_vars and ts_trans."""
        logging.debug("Encode the ts...")

        self._init_ts_var()
        self._init_ts_init()
        self._init_ts_trans()

    def _get_msg_var(self, msg_name, True):
        if (True):
            prefix = Verifier.ENABLED_VAR_PREF
        else:
            prefix = Verifier.ALLOWED_STATE
        var_name = "%s_%s" % (prefix, msg_name)

    def _build_env(self, env, formals, actuals):
        """ Add to env the matching between formal and
        actual parameters.
        """
        assert len(formals) == len(actuals)
        for var, val in zip(formals, actuals):
            # no double assignment
            assert var not in env
            env[var] = val
        return env

    def _enum_evt_inst(self, values):
        acc = self._enum_evt_inst_rec(values, [], [])

    def _enum_evt_inst_rec(self, values, current_res, acc):
        def merge_vals(v1,v2):
            assert (len(v1) == len(v2))

            all_vals = True
            merged = []
            for (a1,a2) in zip(v1,v2)
            if (None != v1 and None != v2):
                if (v1 != v2):
                    # cannot merge
                    return (None, None)
                else merged.append(v1)
            elif (None == v2 and None != v1):
                merged.append(v1)
            elif (None == v1 and None != v2):
                merged.append(v2)
            elif (None == v1 and None == v2):
                all_vals = False
            else:
                assert False # should never happen
            return (merged, all_vals)

        if (len(values) == 0):
            return acc

        current_val = values[0]

        # consider the current value
        (merged, all_vals) = merge_vals(current_val, current_res)
        if (all_vals):
            # Found one matching
            acc.append(merged)
        if (None != merged and ! all_vals):
            # can be merged but no result
            # try to complete merged with other values
            acc = self._enum_evt_inst_rec(values[1:len(values),
                                                 list(merged),
                                                 acc])
        # recursive search not considering the current value
        acc = self._enum_evt_inst_rec(values[1:len(values),
                                             list(current_res),
                                             acc])
        return acc

    def _init_ts_var():
        """Initialize the ts variables.

        What are the state variables of the system?

        For each callin "ci" with the concrete objects "o1, ..., on"
        we have a Boolean variable "allowed_state_ci_o1", where "o1"
        is the receiver.

        For each INSTANTIATION of an event "evt" we have a Boolean
        variable.

        The instantiation is obtained from the bindings of the rules
        """
        logging.debug("Create variable...")
        self.ts_vars = set()

        self.conc_to_msg = {}
        self.msgs_to_var = {}
        self.var_to_msgs = {}

        i = 0
        for cevent in self.ctrace.events:
            i = i + 1
            # each element is (event_symbol, actual_args)
            cb_names = []
            event_cb_map = {}
            for ccb in cevent.cb:
                cb_names.append(cb.symbol + "#" + "_".join(cb.args))

                # build the event signature from the bindings
                for bind in self.bindings:
                    if (ccb.symbol == bind.cb and
                        len(ccb.args) == len(bind.cb_args)):
                        env = self._build_env({}, bind.cb_args,
                                              ccb.args)
                        cevt_args = []
                        for evt_arg in bind.event_args:
                            if (evt_arg in env):
                                cevt_args.append(env[evt_arg])
                            else:
                                # Args not matched
                                cevt_args.append(None)
                        if bind.event not in event_cb_map:
                            event_cb_map[bind.event] = []
                        event_cb_map.append(cevt_args)

                # process the callins
                for cci in cb.ci:
                    ci_name = "ci_" + cci.symbol + "_".join(cci.args)
                    self.conc_to_msg[cci] = ci_name

                    ci_var = Symbol(ci_name, BOOL)
                    # Different ci s instance can have the same variable
                    if ci_var not in self.ts_vars:
                        self.ts_vars.add(ci_var)
                        self.msgs_to_var[ci_name] = ci_var
                        self.var_to_msgs[ci_var] = ci_name
                        logging.debug("Callin %s: create variable %s" % (ci_name, str(ci_var)))
                    if ci_name not in self.msgs_to_instances:
                        self.msgs_to_instances[ci_name] = []
                    self.msgs_to_instances[ci_name].append(ci.args)

            msg_name = "evt_".join(cb_names)

            self.conc_to_msg[cevent] = msg_name
            # event variable
            evt_var_name = self._get_msg_var(msg_name, True)
            evt_var = Symbol(evt_var_name, BOOL)
            logging.debug("Event %s: create variable %s" % (msg_name,
                                                            evt_var_name))
            self.ts_vars.add(evt_var)
            self.msgs_to_var[msg_name] = evt_var
            self.var_to_msgs[evt_var] = msg_name

            if (self.debug_encoding):
                ivar_name = "INPUT_event_%d_%s" % (i, msg_name)
                ivar = Symbol(ivar_name, BOOL)
                self.events_to_input_var[event] = ivar

            # Find all the possible instantiation of the event parameter.
            # Pre-compute the matches
            instances = []
            for (evt, values) in  event_cb_map.iteritems():
                all_instance = self._enum_evt_inst(values)
                if len(all_instances) != 0:
                    instances.append(Instance(evt, all_instance))
            self.msgs_to_instances[msg_name] = instance

        self.ts_error = Symbol(Verifier.ERROR_STATE, BOOL)

    def _init_ts_init(self):
        """Initialize the ts init.

        In the initial state all the events and callins are enabled.
        """
        # The initial state is safe
        self.ts_init = Not(self.ts_error)
        # all the messages are enabled
        for v in self.ts_vars: self.ts_init = And(self.ts_init, v)
        logging.debug("Initial state is %s" % str(self.ts_init))


    def _get_enabled_store(self):
        """ Return a map from messages to an internal state.

        The state is 0 (unkonwn), 1 (enabled/allowed),
        -1 (disabled/disallowed)
        """
        msg_enabled = {}
        for cevt in self.ctrace.events:
            assert cevt in self.conc_to_msg
            evt_msg = self.conc_to_msg[cevt]

            # already visited event
            if (evt_msg in msg_enabled): continue

            # Initially the event value is unknown
            msg_enabled[evt_msg] = 0

            for cb in event.cb:
                for ci in cb.ci:
                    assert ci in self.conc_to_msg
                    ci_msg = self.conc_to_msg[ci]

                    if (ci_msg not in msg_enabled):
                        msg_enabled[ci_msg] = 0 # unknown

        return msg_enabled

    def _process_event(self, cevent):
        """ Process src_event.

        Change msg_enabled updating it with the effects on the system
        state obtained by execturing src_event (and all its callbacks
        and callins).

        Builds a guard condition that contains the pre-condition for
        src_event to be executed.

        Put in in bug_ci all the callin that must be executed in
        src_event that are trivially disabled by some previous
        callin.

        Put in must_be_allowed a set of callins that must be allowed
        in order to execute the event.
        If the event is executed from a state where these callins are
        not enabled, then we have an error.
        """

        bug_ci = None # First ci that cannot be called
        # set of ci that must be allowed to execute the event
        must_be_allowed = []
        # message to a value in {0,1,-1}
        # 3-valued represenation: (0 unknown, -1 false, 1 true)
        msg_enabled = self._get_enabled_store()

        assert msg_evt in self.conc_to_msg
        msg_evt = self.conc_to_msg[cevent]

        # Apply right away the effect of the event
        # This is consistent with the semantic that applies the effect
        # of the event at the beginning if it, and not in the middle
        # of other callbacks or at the end of the event execution.
        self._apply_rules(msg_evt, msg_enabled)

        # Process the sequence of callins of the event
        for ccb in cevent.cb:
            i = i + 1

            for cci in ccb.ci:
                msg_ci = self.conc_to_msg[cci]
                val = msg_enabled[msg_ci]

                if (val == 0):
                    # the ci must have been enabled in the state of the
                    # system if neiter the event itself nor a previous
                    # callin enabled it.
                    #
                    # If it is not the case, then we have a bug!
                    must_be_allowed.append(self.msgs_to_var[msg_ci])

                elif (val == -1):
                    # The ci is disabled, and we are trying to invoke it
                    # This results in an error
                    logging.debug("Bug condition: calling " \
                                  "disabled %s" % str(msg_ci))
                    bug_ci = msg_ci

                    # We stop at the first bug, all the subsequent
                    # inferences would be bogus
                    break
                else:
                    # enabled by some previous message
                    assert val == 1

                # TODO: check keys
                assert False
                self._apply_rules(self, msg_ci, msg_enabled)

        return (msg_enabled, guards, bug_ci, must_be_allowed)

    def _apply_rules(self, msg_evt, msg_enabled):
        """ Find all the rules that match an instantiation in inst_list.

        An instantiation is of the form: evt(@1, ..., @n)
        (a symbol and a list of actual parameters.

        A rule src(x1, ..., xn) => dst(y1, ..., ym) is matched if src
        is equal to evt and the arity of the args of src and evt are
        the same.

        The function applies the changes of the matched rules to
        msg_enabled.
        """
        Logging.debug("START: matching rules for %s..." % msg_evt.symbol)

        # Get the possible instantiation of cevent from the
        # possible bindings
        # The instantiation correspond to a list of environments, one
        # for each callback in the event.
        assert msg_evt in self.msgs_to_instances
        inst_list = self.msgs_to_instances[msg_evt]

        for rule in self.specs:
            for inst in inst_list:
                if (not (rule.src == inst.evt and
                         len(rule.src_args) == len(inst.args))):
                # skip rule if it does not match the event
                continue

            # Build the "to be" list of concrete parameters
            src_env = self._build_env({}, rule.src_args, inst.args)
            conc_dst_args = []
            for c in rule.dst_args:
                if c not in rule.src_args:
                    Logging.debug("%s is an unbounded parameter in " \
                                  "the rule." % (c))
                    break
                else:
                    assert c in src_env
                    conc_dst_args = src_env(c)
            if (len(conc_dst_args) != len(rule.dst_args)):
                continue

            # search for the instantiation (rule.dst, conc_dst_args)
            # TODO use the right map
            assert False

            assert rule.dst in self.self.msgs_to_instances
            # TODO Fix dst_msg
            dst_msg = None
            assert False

            for inst_dst in self.self.msgs_to_instances[rule.dst]:
                if conc_dst_args == inst_dst.args:
                    # we found an effect
                    Logging.debug("Matched rule:\n" \
                                  "%s" \
                                  "Src match: %s\n" \
                                  "Dst match: %s." % (rule.get_print_desc(),
                                                      inst, inst_dst))
                    if (rule.specType == SpecType.Enable or
                        rule.specType == SpecType.Allow):
                        msg_enabled[dst_msg] = 1
                    else:
                        assert (rule.specType == SpecType.Disable or
                                rule.specType == SpecType.Disallow)
                        msg_enabled[dst_msg] = -1

        Logging.debug("START: matching rules for %s..." % msg_evt.symbol)


    def _encode_evt(self, cevent):
        """Encode the transition relation of a single event."""
        logging.debug("Encoding event %s" % cevent)

        (msg_enabled, guards, bug_ci, must_be_allowed) = self._process_event(cevent)

        # TODO: Fix
        # if self.debug_encoding:
        #     self.debug_info._add_pre(cevent, must_be_allowed)
        #     self.debug_info._add_effects(cevent, must_be_allowed)
        #     if (bug_ci != None):
        #         self.debug_info._add_bug(cevent, bug_ci)

        logging.debug("Event %s" % cevent)
        logging.debug("Guards %s" % guards)
        logging.debug("Must be allowed: %s" % must_be_allowed)

        # Create the encoding
        if None == bug_ci:
            # Non buggy transition
            logging.debug("Transition for event %s may be safe" % cevent)

            # Build the encoding for the (final) effects
            # after the execution of the callbacks
            next_effects = []
            for (msg_key, value) in msg_enabled.iteritems():
                assert msg_key in self.msgs_to_var
                msg_var = self.msgs_to_var[msg_key]
                if (value == 1):
                    # msg is enabled after the trans
                    next_effects.append(self._next(msg_var))
                elif (value == -1):
                    # msg is disabled after the trans
                    next_effects.append(Not(self._next(msg_var)))
                else:
                    # Frame condition - msg does not change
                    fc = Iff(msg_var, self._next(msg_var))
                    next_effects.append(fc)

            if (len(must_be_allowed) == 0):
                # no callins must have been enabled in the event
                # There cannot be bugs
                evt_trans = Not(self._next(self.ts_error))
            else:
                evt_trans = TRUE()
                must_ci_formula = And(must_be_allowed)
                # All the CIs in must_be_allowed are allowed
                # iff there is no bug.
                evt_trans = Iff(must_ci_formula,
                                Not(self._next(self.ts_error)))

            if (len(guards) > 0):
                evt_trans = And(evt_trans, And(guards))
            if (len(next_effects) > 0):
                evt_trans = And(evt_trans, And(next_effects))
        else:
            # taking this transition ends in an error,
            # independently from the system's states
            logging.debug("Transition for event %s is a bug" % cevent)
            evt_trans = self._next(self.ts_error)

            # Encode fc of all the state space if we end in error
            # Not compulsory, but useful for debug
            next_effects = []
            for (msg_key, value) in msg_enabled.iteritems():
                assert msg_key in self.msgs_to_var

                msg_var = self.msgs_to_var[msg_key]
                if msg_key != bug_ci:
                    evt_trans = And(evt_trans,
                                    Iff(msg_var, self._next(msg_var)))
                else:
                    # ci is disabled
                    evt_trans = And(evt_trans,
                                    Not(self._next(msg_var)))

        logging.debug("Event %s: trans is %s" % (cevent.symbol, str(evt_trans)))

        return evt_trans


    def _init_ts_trans(self):
        """Initialize the ts trans."""
        logging.debug("Encoding the trans...")

        events_encoding = []
        for evt in self.ctrace.events:
            evt_encoding = self._encode_evt(evt)

            if (self.debug_encoding):
                assert evt in self.events_to_input_var
                ivar = self.events_to_input_var[evt]
                events_encoding.append(Implies(ivar, evt_encoding))
            else:
                events_encoding.append(evt_encoding)

        if (self.debug_encoding):
            # Execute exactly one event at time
            ivars = self.events_to_input_var.values()
            self.ts_trans = And(And(events_encoding),
                                ExactlyOne(ivars))
        else:
            # WARNING: here we use Or instead of
            # exactly one event.
            # This means that "compatible" events may happen
            # at the same time.
            # This is sound for reachability properties.
            self.ts_trans = Or(events_encoding)


