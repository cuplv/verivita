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

class DebugInfo:
    """ Store the encoding information that helps to debug counterexamples
    """

    def __init__(self, verifier):
        # need access to the verifier
        self.verifier = verifier

        # maps from concrete events to the set of
        # callins that must be allowed
        self.events_to_pre = {}

        # maps from events to effects
        self.events_to_effects = {}

        # Determinisic bugs when executing an event
        self.events_to_bugs = {}

    def _add_pre(self, evt, pre):
        assert evt not in self.events_to_pre
        self.events_to_pre[evt] = pre

    def _add_effects(self, evt, effects):
        assert evt not in self.events_to_effects
        self.events_to_effects[evt] = effects

    def _add_bug(self, evt, bug_ci):
        assert evt not in self.events_to_bugs
        self.events_to_bugs[evt] = bug_ci


class Verifier:
    ENABLED_VAR_PREF  = "enabled_state"
    ALLOWED_VAR_PREF  = "allowed_state"
    ERROR_STATE = "error"

    def __init__(self, ctrace, specs, bindings, debug_encoding=False):
        # debug_encoding: encode additional input variables to track
        # what concrete event has been fired in each execution step.
        # By default it is false.
        #
        assert None != ctrace
        assert None != specs
        assert None != bindings

        logging.debug("Creating verifier...")

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

        # Map from concrete messages to variables in the encoding
        # The key is the concrete message instance
        self.msgs_to_var = {}
        self.var_to_cis = {}

        # Map from particular events in the trace
        # events to their invoke input variable.
        # In practice, here we have a particular instance of an event
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

    def _get_msg_key(self, msg):
        if isinstance(msg, CCevent):
            return self._get_evt_var(ci)
        elif isinstance(msg, CCallin):
            return self._get_ci_var(ci)
        assert False

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
            self.msgs_to_var[self._get_msg_key(event)] = evt_var

            if (self.debug_encoding):
                ivar_name = "INPUT_%s" % evt_var_name
                ivar = Symbol(ivar_name, BOOL)
                self.events_to_input_var[event] = ivar

            for cb in event.cb:
                for ci in cb.ci:
                    ci_var = Symbol(self._get_ci_var(ci), BOOL)
                    if ci_var not in self.ts_vars: self.ts_vars.add(ci_var)
                    # Different ci s instance can have the same variable
                    self.msgs_to_var[self._get_msg_key(ci)] = ci_var
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
            msg_enabled[self._get_msg_key(event)] = 0 # unknown
            for cb in event.cb:
                for ci in cb.ci:
                    key = self._get_msg_key(ci)

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
        msg_enabled[self._get_msg_key(src_event)] = 1
        guards = [self.msgs_to_var[self._get_msg_key(src_event)]]

        # Get the possible instantiation of src_event from the
        # possible bindings
        # The instantiation correspond to a list of environments, one
        # for each callback in the event.
        inst_list = self._find_evt_inst(src_event)

        # Apply right away the effect of the event
        # Apply the effect of the event.
        #
        # This is consistent with the semantic
        # that applies the effect of the event at the beginning if it,
        # and not in the middle of other callbacks or at the end of
        # the event execution.
        for env in inst_list:
            matching_rule = self._find_matching_rules_evt(src_event, env)
            for rule in matching_rule:
                self._compute_effect(env, rule, msg_enabled)

        # Process the sequence of callins of the event
        i = 0
        for cb in src_event.cb:
            # the callin must be evaluated on the environment
            # found for the cb
            cb_env = inst_list[i]
            i = i + 1

            for ci in cb.ci:
                val = msg_enabled[self._get_msg_key(ci)]

                if (val == 0):
                    # the ci must have been enabled in the state of the
                    # system if neiter the event itself nor a previous
                    # callin enabled it.
                    #
                    # If it is not the case, then we have a bug!
                    must_be_allowed.append(self.msgs_to_var[key])

                elif (val == -1):
                    # The ci is disabled, and we are trying to invoke it
                    # This results in an error
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

        if self.debug_encoding:
            self.debug_info._add_pre(src_event, must_be_allowed)
            self.debug_info._add_effects(src_event, must_be_allowed)
            if (bug_ci != None):
                self.debug_info._add_bug(src_event, bug_ci)

        logging.debug("Event %s" % src_event)
        logging.debug("Guards %s" % guards)
        logging.debug("Must be allowed: %s" % must_be_allowed)

        # Create the encoding
        if None == bug_ci:
            # Non buggy transition
            logging.debug("Transition for event %s is safe" % src_event)

            # Build the encoding for the (final) effects
            # after the execution of the callbacks
            next_effects = []
            for (msg_key, value) in msg_enabled.iteritems():
                assert msg_key in self.msgs_to_var
                msg_var = self.msgs_to_var[msg_key]

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

        logging.debug("Event %s: trans is %s" % (src_event.symbol, str(evt_trans)))

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

    def _find_evt_inst(self, src_event):
        """ Gets the possible instantiations of src_event from the
        existing bindings in the callbacks.

        Each instantiation corresponds to a list of environments, one
        for each callback of the event.
        """
        cb_env_list = []

        for cb in src_events.cb:
            cb_env = self._find_cb_evt_inst(self, src_event, cb)

            if None == cb_env:
                # In this case we have a concrete event and callbacks that
                # we cannot instantiate.
                # In this case, it means that we miss the association
                # between the arguments of the callback and the arguments
                # of the event.
                #
                # Without the mapping, we are possible missing some
                # relations
                raise Exception("Cannot instantiate the concrete "\
                                "event %s for the callback %s" %
                                (src_event.symbol, cb.symbol))

            cb_env_list.append(cb_env)

        return cb_env_list

    def _find_cb_evt_inst(self, src_event, cb):
        """ Given a callback and an event, it finds the instantiation
        of parameters OF the event based on the concrete values of the
        callback.

        The instantiation (or binding, or grounding, ...) is obtained
        using the bindings specifications.
        """
        env = None
        for binding in self.bindings:
            if ! ((binding.event == src_event.symbol and
                   binding.cb == cb.symbol and
                   len(binding.cb_args) == len(cb.args))):
                continue
            # We have a possible instantiation.
            env_tmp = {}

            # TODO: pre compute these elements in the binding
            formal_cb_pos = 0
            for formal_cb in binding.cb_args:
                # if we have the same letter in the event args
                if formal_cb in binding.event_args:
                    env_tmp[formal_cb] = cb.args[formal_cb_pos]
                formal_cb_pos = formal_cb_pos + 1

            if env != None:
                # Sanity check (when we are sure, we can have an early
                # termination

                eq = True
                if (len(env.keys()) != len(env_tmp.keys())):
                    eq = False
                else:
                    for (k1,v1) in env:
                        if k1 not in env_tmp:
                            eq = False
                            break
                        if env[k1] != env_tmp[k2]:
                            eq = False
                            break
                if not eq:
                    msg = "Found inconsistent binding for "\
                          "event: %s, cb: %s\n" % (src_event.symbol,cb.symbol)
                    raise Exception(msg)
            else:
                env = env_tmp
        return env

    def _find_matching_rules_evt(self, evt, env):
        """ Find all the rules that match the symbol evt.symbol under the
        environment env.

        A rule:
        src(x1, ..., xn) => dst(y1, ..., ym)
        With environment e

        Matches the symbol evt.symbol: evt.symbol(x1, e[x2], ...)

        if src = evt.symbol and if all the dst.args argument can be
        instantiated, then the rule matches the symbol.

        The function returns a list of rules.
        """
        Logging.debug("START: matching rules for %s..." % evt.symbol)


        matching_rules = []
        for rule in self.specs:
            if (not (rule.src == evt.symbol and
                     len(rule.src_args) == len(evt.args))):
                # skip rule if it does not match the event
                continue

            rule_env = {}
            for (src_arg, evt_arg) in rule.src_args:
                if src_arg in env:
                    rule_env[src_arg] = env[evt_arg]
                else:
                    rule_env[src_arg] = None

            for dst_arg in rule.dst_args:
                if dst_arg not in rule_env:
                    # there is a free parameter in dst_arg
                    msg = "Skipping %s\n" \
                          "Free argument arg %s" % (rule.get_print_desc(), dst_arg)
                    Logging.debug(msg)
                    continue
                if rule_env[dst_arg] == None:
                    msg = "Skipping %s\n" \
                          "Arguments %s is not matched by " \
                          "%s" % (rule.get_print_desc(), dst_arg, evt.symbol)
                    Logging.debug(msg)
                    continue
            matching_rules.append(rule)

        Logging.debug("END: matching rule for %s..." % evt.symbol)
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
                    msg_enabled[self._get_msg_key(conc_evt)] = 1
                else:
                    msg_enabled[self._get_msg_key(conc_evt)] = -1
        else:
            # Effect on the callin
            assert rule.specType == SpecType.Allow or rule.specType == SpecType.Disallow

            for conc_callin in self._find_callins(env, rule):
                if (rule.specType == SpecType.Allow):
                    msg_enabled[self._get_msg_key(conc_callin)] = 1
                else:
                    msg_enabled[self._get_msg_key(conc_callin)] = -1

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
            i = i + 1


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

    def _get_bug_index(self, cex):
        i = 0
        for step in cex:
            assert self.ts_error in step

            if TRUE() == step[self.ts_error]:
                return i
            else:
                i = i + 1
        assert False

    def _get_evt_at(self, cex, i):
        """ Get the event at the specified step."""

        step = cex[i]
        for evt in self.ctrace.events:
            assert evt in self.events_to_input_var
            var = self.events_to_input_var[evt]

            assert var in step

            if TRUE() == step[var]:
                return evt

        return None

    def _get_bug_ci(self, pre, cex, i):
        """ Get the ci that is disabled in step but should not be"""

        step = cex[i]

        for var_in_pre in pre:
            assert var_in_pre in step

            if FALSE() == step[var_in_pre]:
                if not var_in_pre in self.var_to_cis:
                    self.var_to_cis[var_in_pre] = []
                    for evt in self.ctrace.events:
                        for cb in evt.cb:
                            for ci in cb.ci:
                                ci_key = self._get_msg_key(ci)
                                assert ci_key in self.msgs_to_var
                                if var_in_pre == self.msgs_to_var[ci_key]:
                                    self.var_to_cis[var_in_pre].append(ci)
                return self.var_to_cis[var_in_pre]
        return None

    def debug_cex(self, cex):
        """ Finds the following information from the cex:
        - What ci was called and was not enabled
        - What event disabled the ci in the trace
        - What events could have been enabled the ci "in the middle"
        """
        assert len(cex) > 0 # in the initial state everything is enabled
        assert self.debug_encoding # only available with debug info

        bug_index = self._get_bug_index(cex)
        assert bug_index > 0 # initial state is safe

        # What ci caused the error?
        last_evt = self._get_evt_at(cex, bug_index - 1)
        assert None != last_evt

        if (last_evt in self.debug_info.events_to_bugs):
            error_ci = self.debug_info.events_to_bugs[last_evt]
            print "Callin %s disabled deterministically " \
                "by %s" % (error_ci, last_evt)
        else:

            assert last_evt in self.debug_info.events_to_pre
            error_ci = self._get_bug_ci(self.debug_info.events_to_pre[last_evt],
                                        cex, bug_index - 1)
            print "Event %s tries to execute a disabled callin" % last_evt.symbol
            print "Disabled concrete callins: %s" % str([l.symbol for l in error_ci])

