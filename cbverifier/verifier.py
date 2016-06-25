""" Encode and solve the verification problem

The input are:
  - a concrete trace
  - a specification (a set of rules)
  - a bound

The verifier finds a possible (spurious) permutation of the events in
the concrete trace that may cause a bug (a bug arises a disabled
callin is called).

The possible permutation of the events depend on the enabled/disabled
status of events/callins.
"""

import logging

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


class Verifier:
    ENABLED_VAR_PREF  = "enabled_state"
    ALLOWED_VAR_PREF  = "allowed_state"
    ERROR_STATE = "error"

    def __init__(self, ctrace, specs, debug_encoding=False):
        # debug_encoding: encode additional input variables to track
        # what concrete event has been fired in each execution step.
        # By default it is false.
        #
        assert None != ctrace
        assert None != specs

        logging.debug("Creating verifier...")

        # pysmt stuff
        self.env = reset_env()
        self.mgr = self.env.formula_manager
        self.helper = Helper(self.env)

        # concrete trace
        self.ctrace = ctrace
        # specification (list of rules)
        self.specs = specs

        self.debug_encoding = debug_encoding

        # internal representation of the transition system
        self.ts_vars = None
        self.ts_init = None
        self.ts_trans = None
        # reachability property
        self.ts_error = None

        # Map from concrete messages to variables in the encoding
        self.msgs_to_var = {}

        # Map from concrete events to their invoke input variable
        # It is used for debug
        self.events_to_input_var = {}
        
        # Initialize the transition system
        self._initialize_ts()

    def _next(self, var):
        assert var.is_symbol()
        return Helper.get_next_var(var, self.mgr)

    def _get_evt_var(self, event):
        if len(event.args) > 0:
            args_suffix = "_".join(event.args)
        else:
            args_suffix = ""

        var_name = "%s_%s_%s" % (Verifier.ENABLED_VAR_PREF,
                                 event.symbol,
                                 args_suffix)
        return var_name

    def _get_ci_var(self, ci):
        # just take the first argument (the receiver)
        if len(ci.args) > 0:
            # The concrete name of the CI considers the first arguments
            # (the receiver)
            args_suffix = ci.args[0]
        else:
            args_suffix = ""

        var_name = "%s_%s_%s" % (Verifier.ALLOWED_VAR_PREF,
                                 ci.symbol,
                                 args_suffix)
        return var_name

    def _get_ci_key(self, ci):
        return self._get_ci_var(ci)

    def _initialize_ts(self):
        """Initialize ts_vars and ts_trans."""
        logging.debug("Encode the ts...")

        self._init_ts_var()
        self._init_ts_init()
        self._init_ts_trans()

    def _init_ts_var(self):
        """Initialize the ts variables.

        What are the state variable of the system?

        For each callin "ci" with the concrete objects "o1, ..., on"
        we have a Boolean variable "allowed_state_ci_o1", where "o1"
        is the receiver.

        For each event "evt" with objects "o1, ..., on" appearing in
        the event's arguments, we have a Boolean variable
        "enabled_state_evt_o1_..._on".
        """

        logging.debug("Create variable...")
        self.ts_vars = set()
        self.msgs_to_var = {}

        # Process the trace
        for event in self.ctrace.events:
            # event variable
            evt_var_name = self._get_evt_var(event)
            evt_var = Symbol(evt_var_name, BOOL)
            logging.debug("Event %s: create variable %s" % (event, evt_var_name))            
            self.ts_vars.add(evt_var)
            self.msgs_to_var[event] = evt_var

            if (self.debug_encoding):
                ivar_name = "INPUT_%s" % evt_var_name
                ivar = Symbol(ivar_name, BOOL)
                self.events_to_input_var[event] = ivar

            for cb in event.cb:
                for ci in cb.ci:
                    ci_var = Symbol(self._get_ci_var(ci), BOOL)
                    if ci_var not in self.ts_vars: self.ts_vars.add(ci_var)
                    # Different ci s instance can have the same
                    # variable
                    key = self._get_ci_key(ci)
                    self.msgs_to_var[key] = ci_var
                    logging.debug("Callin %s for ci %s" % (ci, str(ci_var)))

        self.ts_error = Symbol(Verifier.ERROR_STATE, BOOL)


    def _init_ts_init(self):
        """Initialize the ts init.

        In the initial state all the events and callins are enabled.
        """

        # The initial state is safe
        self.ts_init = Not(self.ts_error)

        # all the messages are enabled
        for v in self.ts_vars:
            self.ts_init = And(self.ts_init, v)

        logging.debug("Initial state is %s" % str(self.ts_init))

    def _get_enabled_store(self):
        """ Return a map from messages to an internal state.

        The state is 0 (unkonwn), 1 (enabled/allowed),
        -1 (disabled/disallowed)
        """
        msg_enabled = {}
        for event in self.ctrace.events:
            msg_enabled[event] = 0 # unknown
            for cb in event.cb:
                for ci in cb.ci:
                    key = self._get_ci_key(ci)

                    if (key not in msg_enabled):
                        msg_enabled[key] = 0 # unknown

        return msg_enabled

    def _process_event(self, src_event):
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
        # First ci that cannot be called
        bug_ci = None
        must_be_allowed = []

        # 3-valued represenation (0 unknown, -1 false, 1 true)
        msg_enabled = self._get_enabled_store()

        # The event must be enabled
        msg_enabled[src_event] = 1
        guards = [self.msgs_to_var[src_event]]

        evt_matched_rules = self._find_matching_rules_evt(src_event)

        # Apply the effect of the event.
        #
        # This is consistent with the semantic
        # that applies the effect of the event at the beginning if it,
        # and not in the middle of other callbacks or at the end of
        # the event execution.
        for (env, rule) in evt_matched_rules:
            # Apply the effect of the event
            self._compute_effect(env, rule, msg_enabled)

        # Process the sequence of callins of the event
        for event in self.ctrace.events:
            for cb in event.cb:
                for ci in cb.ci:
                    key = self._get_ci_key(ci)
                    assert key in msg_enabled
                    val = msg_enabled[key]

                    if (key not in msg_enabled):
                        msg_enabled[key] = 0 # unknown
                    if (val == 0):
                        # the ci must have been enabled in the state of the
                        # system if neiter the event itself nor a previous
                        # callin enabled it.
                        #
                        # If it is not the case, then we have a bug!
                        must_be_allowed.append(self.msgs_to_var[key])
                    elif (val == -1):
                        # The ci is disabled, and we are trying to invoke it
                        # Thisf results in an error
                        logging.debug("Bug condition: calling " \
                                      "disabled %s" % str(key))
                        bug_ci = key

                        # We stop at the first bug, all the subsequent
                        # inferences would be bogus
                        break
                    else:
                        # enabled by some previous message
                        assert val == 1

                    # find the rules that are matched by ci
                    ci_matching = self._find_matching_rules_ci(ci)
                    # Apply the effect for the callins
                    for (env, rule) in ci_matching:
                        self._compute_effect(env, rule, msg_enabled)

        return (msg_enabled, guards, bug_ci, must_be_allowed)


    def _encode_evt(self, src_event):
        """Encode the transition relation of a single event."""
        logging.debug("Encoding event %s" % src_event)

        (msg_enabled, guards, bug_ci, must_be_allowed) = self._process_event(src_event)

        # Create the encoding
        if None == bug_ci:
            # Non buggy transition
            logging.debug("Transition for event %s is safe" % src_event)

            # Build the encoding for the (final) effects
            # after the execution of the callbacks
            next_effects = []
            for (msg, value) in msg_enabled.iteritems():
                assert msg in self.msgs_to_var
                msg_var = self.msgs_to_var[msg]

                if (value == 1):
                    # enabled after the trans
                    next_effects.append(self._next(msg_var))
                elif (value == -1):
                    # disable after the trans
                    next_effects.append(Not(self._next(msg_var)))
                else:
                    # Frame condition
                    fc = Iff(msg_var, self._next(msg_var))
                    next_effects.append(fc)

            if (len(must_be_allowed) == 0):
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
            # taking this transition ends in an error
            logging.debug("Transition for event %s is a bug" % src_event)
            evt_trans = self._next(self.ts_error)

            # Encode fc if we end in error - useful for debug
            next_effects = []
            for (msg, value) in msg_enabled.iteritems():
                assert msg in self.msgs_to_var
                msg_var = self.msgs_to_var[msg]
                evt_trans = And(evt_trans,
                                Iff(msg_var, self._next(msg_var)))

        logging.debug("Event %s: trans is %s" % (src_event, str(evt_trans)))

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

    def _merge_env(self, env1, env2):
        """ Merge env2 into env1.
        Return a new env obtained merging env2 into env1.

        If the actual value for a parameter in env1 and
        env2 differs than the function returns None.
        """
        copy_env = {}
        for (var, val) in env1.iteritems():
            copy_env[var] = val

        for (var, val) in env2.iteritems():
            if var in copy_env:
                if val != copy_env[var]:
                    # Disagreement in the values
                    # for var
                    return None
            else:
                copy_env[var] = val
        return copy_env

    def _find_matching_rules_evt(self, evt):
        """ Find all the rules that match an event.

        A rule:
        src(x1, ..., xn) >> cb(y1, ..., yl) => ...

        Matches the event evt:
          - evt_symbol, (o1, ..., on)
          - cb_symbol, (c1, ..., cl)

        if src = evt_symbol, cb = cb_symbol, the arity of the
        arguments is the same and if x_j = y_k then o_j = c_k

        For each matched rule, the function also builds an
        environment that stores how formal parameters in the rule
        are instantiated by the event.
        """

        matching_rules = []
        for rule in self.specs:
            # Environment: map from vars to concrete values
            env = {}

            if (not (rule.src == evt.symbol and
                     len(rule.src_args) == len(evt.args))):
                # skip rule if it does not match the event
                continue
            env = self._build_env(env, rule.src_args, evt.args)

            if rule.cb == None:
                # no callback in the rule, then we already have a
                # match
                matching_rules.append((env, rule))
            else:
                # Need to match a cb in the trace with a cb in
                # the rule
                for cb in evt.cb:
                    if (not (rule.cb == cb.symbol and
                         len(rule.cb_args) == len(cb.args))):
                        continue

                    # match the arguments
                    env_cb = {}
                    env_cb = self._build_env(env_cb, rule.cb_args, cb.args)
                    merged_env = self._merge_env(env, env_cb)

                    # the rule does not match
                    if None == merged_env: continue

                    matching_rules.append((merged_env, rule))

        return matching_rules

    def _find_matching_rules_ci(self, ci):
        """ Find all the rules that match a callin.

        A rule: src(x1, ..., xn) => ...

        Matches the callin ci:
          - ci_symbol, (o1, ..., on)

        if src = ci_symbol and the arity of the
        arguments is the same

        """
        matching_ci = []

        for rule in self.specs:
            env = {} # map from vars to concrete values
            if (not (rule.src == ci.symbol and
                     len(rule.src_args) == len(ci.args))):
                continue
            env = self._build_env(env, rule.src_args, ci.args)

            matching_ci.append((env, rule))

        return matching_ci

    def _dst_match(self, env, dst_symbol, dst_args, rule):
        assert None != dst_symbol

        logging.debug("\n--- Matching --- \n" \
                      "Dst symbol: %s [%s]\n"
                      "Rule (%s[%s], %s[%s], %s[%s])\n" \
                      "Environment %s" \
                      % (dst_symbol,
                         ",".join(dst_args),
                         rule.src, ",".join(rule.src_args),
                         rule.cb, ",".join(rule.cb_args),
                         rule.dst, ",".join(rule.dst_args),
                         str(env)))

        if dst_symbol != rule.dst:
            logging.debug("Does not match (name): %s != %s" \
                          % (dst_symbol, rule.dst))
            return False
        if len(dst_args) != len(rule.dst_args):
            logging.debug("Does not match (length) " \
                          "%d != %d" \
                          % (len(dst_args), len(rule.dst_args)))
        for (actual,formal) in zip(dst_args, rule.dst_args):
            if formal in env:
                if actual != env[formal]:
                    logging.debug("Does not match (args): %s != %s" \
                                  % (actual, env[formal]))
                    return False

        logging.debug("Matched!")
        return True

    def _find_events(self, env, rule):
        """ Find all the concrete events that match the dst of the rule.

        The match is not unique and may be partial (since some
        parameters may be free)
        """
        logging.debug("Matching EVENTs...")
        matching_events = []
        for evt in self.ctrace.events:
            match = self._dst_match(env, evt.symbol, evt.args, rule)
            if match: matching_events.append(evt)
        return matching_events

    def _find_callins(self, env, rule):
        """ Find all the concrete callins that match the dst of the
        rule.

        The match is not unique and may be partial (since some
        parameters may be free)
        """
        logging.debug("Matching CIs...")
        matching_ci = []
        for evt in self.ctrace.events:
            for cb in evt.cb:
                for ci in cb.ci:
                    assert None != ci.symbol
                    match = self._dst_match(env, ci.symbol, ci.args, rule)
                    if match:
                        matching_ci.append(ci)
        return matching_ci

    def _compute_effect(self, env, rule, msg_enabled):
        """ Given an environment and a rule,
        changes msg_enabled applying the rule.
        """
        logging.debug("_compute_effect")

        if (rule.specType == SpecType.Enable or
            rule.specType == SpecType.Disable):
            # Effect on the events
            # Find all the concrete events that are affected by the
            # rule.
            for conc_evt in self._find_events(env, rule):
                logging.debug("Change status of %s" % conc_evt)

                if (rule.specType == SpecType.Enable):
                    msg_enabled[conc_evt] = 1
                else:
                    msg_enabled[conc_evt] = -1
        else:
            # Effect on the callin
            assert rule.specType == SpecType.Allow or rule.specType == SpecType.Disallow

            for conc_callin in self._find_callins(env, rule):
                ci_key = self._get_ci_key(conc_callin)
                if (rule.specType == SpecType.Allow):
                    msg_enabled[ci_key] = 1
                else:
                    msg_enabled[ci_key] = -1

    def _build_trace(self, model, state_vars, input_vars, steps):
        """Extract the trace from the satisfying assignment."""
        all_vars = set(state_vars).union(input_vars)
        
        cex = []
        for i in range(steps + 1):
            cex_i = {}

            # skip the input variables in the last step
            if (i < steps): vars_to_use = all_vars
            else: vars_to_use = state_vars
                
            for var in vars_to_use:
                var_i = self.helper.get_var_at_time(var, i)
                cex_i[var] = model.get_value(var_i, True)
            cex.append(cex_i)

        return cex

    def print_cex(self, cex, changed=False):
        sep = "----------------------------------------"        
        i = 0

        prev_state = {}
        
        print(sep)
        for step in cex:
            print("State - %d" % i)
            print(sep)
            for key, value in step.iteritems():
                if changed:
                    if (key not in prev_state or
                        (key in prev_state and
                        prev_state[key] != value)):
                        print("%s: %s" % (key, value))
                    prev_state[key] = value
                    
                else:
                    print("%s: %s" % (key, value))                    
            print(sep)
            
    
    def find_bug(self, steps):
        """Explore the system up to k steps.
        Steps correspond to the number of events executed in the
        system.

        Returns None if no bugs where found up to k or a
        counterexample otherwise (a list of events).
        """

        solver = Solver(name='z3', logic=QF_BOOL)

        error_condition = []

        # Set the variables of the ts
        state_vars = set(self.ts_vars)
        state_vars.add(self.ts_error)
        input_vars = set(self.events_to_input_var.values())
        all_vars = set(state_vars)
        all_vars.update(input_vars)
        
        for i in range(steps + 1):
            logging.debug("Encoding %d..." % i)

            if (i == 0):
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts_init, i)
            else:
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts_trans, i-1)
            solver.add_assertion(f_at_i)
            logging.debug("Add assertion %s" % f_at_i)

            error_condition.append(self.helper.get_formula_at_i(all_vars,
                                                                self.ts_error,
                                                                i))

        # error condition in at least one of the (k-1)-th states
        logging.debug("Error condition %s" % error_condition)
        solver.add_assertion(Or(error_condition))

        logging.debug("Finding bug up to %d steps..." % steps)
        res = solver.solve()
        if (solver.solve()):
            logging.debug("Found bug...")

            model = solver.get_model()
            trace = self._build_trace(model, state_vars, input_vars, steps)

            return trace
        else:
            # No bugs found
            logging.debug("No bugs found up to %d steps" % steps)
            return None
