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

from spec import SpecType, Spec, Binding

from ctrace import ConcreteTrace, CEvent, CCallin, CCallback
from helpers import Helper
from tosmv import SmvTranslator

Instance = collections.namedtuple("Instance", ["symbol", "args", "msg"],
                                  verbose=False,
                                  rename=False)

class Verifier:
    ENABLED_VAR_PREF  = "enabled_state"
    ALLOWED_VAR_PREF  = "allowed_state"
    ERROR_STATE = "error"

    def __init__(self, ctrace, specs, bindings,
                 debug_encoding=False,
                 coi=False):
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

        # options
        self.debug_encoding = debug_encoding
        self.coi = coi

        # Internal data structures
        self.msgs = MatchInfo(self)
        self.conc_to_msg = {} # From concrete events/callin to msgs
        self.msgs_to_instances = {} # Messages to list of instances
        self.symbol_to_instances = {} # symbols to list of instances
        # Map from ci to its containing event (message)
        self.ci_to_evt = {}

        # internal representation of the transition system
        self.ts_state_vars = None
        self.ts_input_vars = None
        self.ts_init = None
        self.ts_trans = None
        # reachability property
        self.ts_error = None

        self.msgs_to_var = {} # Messages to Boolean variables
        self.var_to_msgs = {} # inverse map
        # Map from a concrete event in the trace to their
        # invoke variable.
        # In practice, here we have a particular instance of an event
        # It is used for debug
        self.events_to_input_var = {}

        # Process trace
        self._process_trace()

        if self.coi:
            # Simplify the encoding
            self._simplify()

        # Initialize the transition system
        self._initialize_ts()

    def _next(self, var):
        assert var.is_symbol()
        return Helper.get_next_var(var, self.mgr)

    def _get_ts_var(self):
        all_vars = set(self.ts_state_vars)
        all_vars.update(self.ts_input_vars)
        return all_vars

    def _process_trace(self):
        """Process the trace."""
        logging.debug("Process trace...")

        # instantiate the events, matching the bindings
        self._find_instances()

        # Process every event, computing the preconditions and effects
        # due to the specifications
        i = 0
        for cevt in self.ctrace.events:
            i = i+1
            logging.debug("evt %d\n" % i)
            self._process_event(cevt)


    def _initialize_ts(self):
        """Initialize ts_vars and ts_trans."""
        logging.debug("Encode the ts...")

        self._init_ts_var()
        self._init_ts_init()
        self._init_ts_trans()

    def _get_msg_var(self, msg_name, is_evt):
        if (is_evt):
            prefix = Verifier.ENABLED_VAR_PREF
        else:
            prefix = Verifier.ALLOWED_VAR_PREF
        var_name = "%s_%s" % (prefix, msg_name)
        return var_name

    def _get_conc_var(self, conc_msg, is_evt):
        msg_name = self.conc_to_msg[conc_msg]
        return self.msgs_to_var[msg_name]

    def _get_ci_msg(self, cci):
        return "ci_" + cci.symbol + "_" + ",".join(cci.args)

    @staticmethod
    def _build_env(env, formals, actuals):
        """ Add to env the matching between formal and
        actual parameters.
        """
        assert len(formals) == len(actuals)
        for var, val in zip(formals, actuals):
            # no double assignment
            assert var not in env
            env[var] = val
        return env

    @staticmethod
    def _enum_evt_inst(values):
        """ Values contain a list of list of arguments.
        Each list of arguments may not be complete (some arguments may
        be None).

        The function tries to build a set of complete matches by
        combining multiple array of arguments.

        For example, if the values list is:
        [1, None, None], [2, None, None], [None, 3, 4]

        The function builds the complete argument lists:
        [1, 3, 4], [2, 3, 4].
        """
        assert None != values
        if len(values) == 0: return []
        init_val = [None for v in values[0]]
        acc = Verifier._enum_evt_inst_rec(values, init_val, [])
        return acc

    @staticmethod
    def _enum_evt_inst_rec(values, current_res, acc):
        """ Recursive auxiliary function of _enum_evt_inst."""
        def merge_vals(v1,v2):
            assert (len(v1) == len(v2))

            all_vals = True
            merged = []
            for (a1,a2) in zip(v1,v2):
                if (None != a1 and None != a2):
                    if (a1 != a2):
                        # cannot merge
                        return (None, None)
                    else:
                        merged.append(a1)
                elif (None == a2 and None != a1):
                    merged.append(a1)
                elif (None == a1 and None != a2):
                    merged.append(a2)
                elif (None == a1 and None == a2):
                    merged.append(None)
                    all_vals = False
                else:
                    assert False # should never happen

            assert len(merged) == len(v1)
            return (merged, all_vals)

        if (len(values) == 0): return acc

        current_val = values[0]

        # consider the current value
        assert len(current_val) == len(current_res)
        (merged, all_vals) = merge_vals(current_val, current_res)

        # Found one matching
        if (all_vals):
            assert len(merged) == len(current_val)
            acc.append(merged)
        if (None != merged and not all_vals):
            # can be merged but no result
            # try to complete merged with other values
            assert len(merged) == len(current_val)
            acc = Verifier._enum_evt_inst_rec(values[1:len(values)],
                                              list(merged),
                                              acc)
        # recursive search not considering the current value
        acc = Verifier._enum_evt_inst_rec(values[1:len(values)],
                                          list(current_res),
                                          acc)
        return acc

    @staticmethod
    def _evt_signature_from_cb(bindings, ccb, event_cb_map):
        """ Iterate through all the bindings, finding all the bindings
        that contain the callback ccb.

        Then, it populates a map from the event symbol of the binding
        to the concrete arguments of the callback.

        For example:
        - concrete callin := cb(@1, @2)
        - binding := event1(x1, x2) >> cb(x2, x1)

        The function add the list [@2, @1] to the list of bindings for
        the event "event1".

        The list of concrete arguments for the event can be partial at
        this stage (the elment in the list is None).
        """
        for bind in bindings:
            if (ccb.symbol == bind.cb and
                len(ccb.args) == len(bind.cb_args)):
                env = Verifier._build_env({}, bind.cb_args,
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
                event_cb_map[bind.event].append(cevt_args)

        return event_cb_map

    def _find_instances_callin(self, evt_msg, ccb):
        """ Creates the data structure to keep all the instances of the callin.
        """
        for cci in ccb.ci:
            ci_name = self._get_ci_msg(cci)
            self.conc_to_msg[cci] = ci_name

            # Different ci instances can have the same message
            if ci_name not in self.msgs.evt_info:
                self.msgs[ci_name] = CiInfo(ci_name)
            self.msgs[ci_name].conc_msgs.add(cci)

            if ci_name not in self.msgs_to_instances:
                self.msgs_to_instances[ci_name] = []
            instance = Instance(cci.symbol, tuple(cci.args), ci_name)

            self.msgs_to_instances[ci_name].append(instance)
            if cci.symbol not in self.symbol_to_instances:
                self.symbol_to_instances[cci.symbol] = []
            self.symbol_to_instances[cci.symbol].append(instance)

            if ci_name not in self.ci_to_evt:
                self.ci_to_evt[ci_name] = set()
            self.ci_to_evt[ci_name].add(evt_msg)

    def _init_ts_var_callin(self, ccb):
        """ Creates the encoding variables for all the  callins in ccb.
        """
        for cci in ccb.ci:
            ci_name = self._get_ci_msg(cci)
            ci_var_name = self._get_msg_var(ci_name, False)
            ci_var = Symbol(ci_var_name, BOOL)

            # Different ci s instance can have the same variable
            if ci_var not in self.ts_state_vars:
                self.ts_state_vars.add(ci_var)
                self.msgs_to_var[ci_name] = ci_var
                self.var_to_msgs[ci_var] = ci_name
                logging.debug("Callin %s: create variable %s" % (ci_name, str(ci_var)))

    def _find_instances(self):
        """ Instantiate the events from the trace.

        The instantiation is found by looking at the bindings defined
        in the specifications.

        The function changes the maps conc_to_msg, msgs_to_instances
        and symbol_to_instances.
        """

        self.conc_to_msg = {}
        self.msgs_to_instances = {}
        self.symbol_to_instances = {}
        self.ci_to_evt = {}

        i = 0

        # The loop computes several information from the trace and the
        # bindings.
        #
        # 1. A "name" for the event message that is determined by the
        #    callbacks involved in the message and their concrete
        #    parameters.
        #
        # 2. The set of "instances" of the event.
        #    An instance is defined by the name of an event
        #    (e.g. Click), the list of concrete parameters of the event
        #    (obj1, ...) and the message names that can generate the
        #    instance.
        #
        # 3. A "name" for the callin messages
        #
        # 4. A set of instances for each callin.
        #
        for cevent in self.ctrace.events:
            i = i + 1
            # List of names obtained from each callback
            # Used to name the event variable
            cb_names = []

            # The key is an event symbol while the values are a list
            # of list of arguments.
            #
            # The event_symbol and the arguments are found by matching
            # the concrete callback and its actual arguments with the
            # event symbol and its arguments specified in a binding.
            #
            # In practice:
            #   - each concrete callback has a list of concrete arguments
            #   - the binding specification tells that the
            #     callback cb(x1, x2, ..., xn) is called by the event
            #     event(x1, x2, ..., z1...)
            #
            # The loops build the "event signature" of the concrete
            # event using the concrete callbacks name and parameters
            # and the bindings (a map from callbacks and parameters to
            # event names and parameters).
            #
            event_cb_map = {}

            for ccb in cevent.cb:
                cb_names.append(ccb.symbol + "_#_" + "_".join(ccb.args))
            msg_name = "evt_".join(cb_names)
            if msg_name == "":
                msg_name = "no_callbacks"

            for ccb in cevent.cb:
                cb_names.append(ccb.symbol + "_#_" + "_".join(ccb.args))
                event_cb_map = Verifier._evt_signature_from_cb(self.bindings,
                                                               ccb,
                                                               event_cb_map)
                # process the callins (3 and 4)
                self._find_instances_callin(msg_name, ccb)

            self.conc_to_msg[cevent] = msg_name

            if (msg_name  not in self.msgs.evt_info):
                self.msgs[msg_name] = EventInfo(msg_name)
            self.msgs[msg_name].conc_msgs.add(cevent)

            # 4. Find all the possible instantiation of the event
            # parameter.
            #
            # These information are used both to match a rule and to
            # apply its effects.
            instances = []
            for (evt, values) in event_cb_map.iteritems():
                # keep a map from the event name
                if evt not in self.symbol_to_instances:
                    self.symbol_to_instances[evt] = []

                all_complete_args = Verifier._enum_evt_inst(values)
                if len(all_complete_args) != 0:
                    for args_list in all_complete_args:
                        instance = Instance(evt, tuple(args_list), msg_name)
                        instances.append(instance)
                        self.symbol_to_instances[evt].append(instance)
            self.msgs_to_instances[msg_name] = instances

    def _init_ts_var(self):
        """ Creates the variables in the transition system for a set
        of messages.

        What are the state variables of the system?

        For each callin "ci" with the concrete objects "o1, ..., on"
        we have a Boolean variable "allowed_state_ci_o1", where "o1"
        is the receiver.

        For each event "evt" we have a Boolean variable.

        Change ts_state_vars, ts_input_vars, msgs_to_var, var_to_msgs.
        """
        logging.debug("Create variable...")
        self.ts_state_vars = set()
        self.ts_input_vars = set()
        self.var_to_msgs = {}

        i = 0

        #
        for cevent in self.ctrace.events:
            i = i + 1

            assert cevent in self.conc_to_msg
            msg_name = self.conc_to_msg[cevent]

            if (msg_name not in self.msgs_to_var):
                evt_var_name = self._get_msg_var(msg_name, True)
                evt_var = Symbol(evt_var_name, BOOL)
                logging.debug("Event %s: create variable %s" % (msg_name,
                                                                evt_var_name))
                self.ts_state_vars.add(evt_var)
                self.msgs_to_var[msg_name] = evt_var
                self.var_to_msgs[evt_var] = msg_name

            if (self.debug_encoding):
                ivar_name = "INPUT_event_%d_%s" % (i, msg_name)
                ivar = Symbol(ivar_name, BOOL)
                self.events_to_input_var[cevent] = ivar
                self.ts_input_vars.add(ivar)

            # process the callback to add the ci called by the event
            for ccb in cevent.cb:
                self._init_ts_var_callin(ccb)

        # creates the error variable
        self.ts_error = Symbol(Verifier.ERROR_STATE, BOOL)
        self.ts_state_vars.add(self.ts_error)

    def _init_ts_init(self):
        """Initialize the ts init.

        In the initial state all the events and callins are enabled.
        """
        # The initial state is safe
        self.ts_init = Not(self.ts_error)
        # all the messages are enabled
        for v in self.ts_state_vars:
            if v != self.ts_error:
                self.ts_init = And(self.ts_init, v)
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
            if (not evt_msg in msg_enabled):
                msg_enabled[evt_msg] = 0

            # Initially the event value is unknown
            for ccb in cevt.cb:
                for cci in ccb.ci:
                    assert cci in self.conc_to_msg
                    ci_msg = self.conc_to_msg[cci]

                    if (ci_msg not in msg_enabled):
                        msg_enabled[ci_msg] = 0 # unknown

        return msg_enabled

    def _process_event(self, cevent):
        """ Process cevent.

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

        # Get the message associated to the event
        assert cevent in self.conc_to_msg
        msg_evt = self.conc_to_msg[cevent]
        evt_info = self.msgs[msg_evt]

        evt_info.guards = [msg_evt] # The event must be enabled
        evt_info.must_be_allowed = set()
        evt_info.msg_enabled = self._get_enabled_store()
        evt_info.msg_enabled[msg_evt] = 1
        # Deterministic bug
        evt_info.bug_ci = None

        # Apply right away the effect of the event
        # This is consistent with the semantic that applies the effect
        # of the event at the beginning if it, and not in the middle
        # of other callbacks or at the end of the event execution.
        self._apply_rules(msg_evt, msg_evt)

        # Process the sequence of callins of the event
        for ccb in cevent.cb:
            for cci in ccb.ci:
                msg_ci = self.conc_to_msg[cci]
                assert msg_ci in evt_info.msg_enabled
                val = evt_info.msg_enabled[msg_ci]

                if (val == 0):
                    # the ci must have been enabled in the state of the
                    # system if neiter the event itself nor a previous
                    # callin enabled it.
                    #
                    # If it is not the case, then we have a bug!
                    evt_info.must_be_allowed.add(msg_ci)

                elif (val == -1):
                    # The ci is disabled, and we are trying to invoke it
                    # This results in an error
                    logging.debug("Bug condition: calling " \
                                  "disabled %s" % str(msg_ci))
                    evt_info.bug_ci = msg_ci

                    # We stop at the first bug, all the subsequent
                    # inferences would be bogus
                    break
                else:
                    # enabled by some previous message
                    assert val == 1
                # apply the rule for the callin
                self._apply_rules(msg_ci, msg_evt)

        return

    def _inst_param_rule(self, rule_formal_args, env):
        """ Instantiate the formal parameters of a rule given an
        environment.
        """
        conc_dst_args = []
        for c in rule_formal_args:
            if c not in env:
                logging.debug("%s is an unbounded parameter in " \
                              "the rule." % (c))
                conc_dst_args.append(None)
            else:
                assert c in env
                conc_dst_args.append(env[c])
        assert (len(conc_dst_args) == len(rule_formal_args))
        return conc_dst_args

    def _match_args(self, inst_args, conc_args):
        """ Matches all the concrete argument of conc_args
        with the arguments of instance
        """
        matches = True
        for (conc_arg, inst_arg) in zip(conc_args, inst_args):
            if None != conc_arg and conc_arg != inst_arg:
                matches = False
                break
        return matches

    def _apply_rules(self, msg_evt, cevt_msg):
        """ Find all the rules that match an instantiation in inst_list.

        An instantiation is of the form: evt(@1, ..., @n)
        (a symbol and a list of actual parameters.

        A rule src(x1, ..., xn) => dst(y1, ..., ym) is matched if src
        is equal to evt and the arity of the args of src and evt are
        the same.

        The function applies the changes of the matched rules to
        self.msgs[msg_evt].msg_enabled.
        """
        logging.debug("START: matching rules for %s..." % msg_evt)

        msg_enabled = self.msgs[cevt_msg].msg_enabled

        # Get the possible instantiation of cevent from the
        # possible bindings
        # The instantiation correspond to a list of environments, one
        # for each callback in the event.
        assert msg_evt in self.msgs_to_instances
        inst_list = self.msgs_to_instances[msg_evt]

        # process all the rules
        for rule in self.specs:
            # Find a matching instance for the rule
            for inst in inst_list:
                if (not (rule.src == inst.symbol and
                         len(rule.src_args) == len(inst.args))):
                    # skip rule if it does not match the event
                    continue

                # Skip rule if there are no instantiation for the dst
                # symbol of the rule
                if rule.dst not in self.symbol_to_instances:
                    continue

                # Build the list of actual parameters for rule.src.
                #
                # rule.src has a set of formal parameter [x1,x2,...,xn]
                # Inst has a set of actual parameter [a1, ..., an]
                # rule.dst has a set of formal parameter [y1,x2,...,yk]
                # Some of the ai-s can be None (the instance is a
                # partial instantiation of the event).
                #
                # conc_dst_args is a list [l1, ..., lk]
                # where li = aj if l1 = xj, and li = None otherwise
                #
                src_env = self._build_env({}, rule.src_args, inst.args)
                conc_dst_args = self._inst_param_rule(rule.dst_args, src_env)

                # At this point: the rule matches an instance.

                # Find the instances that are affected by the rule
                for inst_dst in self.symbol_to_instances[rule.dst]:
                    matches = self._match_args(inst_dst.args, conc_dst_args)

                    if matches:
                        # we found an effect for the rule
                        logging.debug("Matched rule:\n" \
                                      "%s\n" \
                                      "Src match: %s\n" \
                                      "Dst match: %s." % (rule.get_print_desc(),
                                                          inst, inst_dst))
                        self.msgs[cevt_msg].add_match(rule, inst, inst_dst)
                        if (rule.specType == SpecType.Enable or
                            rule.specType == SpecType.Allow):
                            # if (self.msgs[cevt_msg].msg_enabled[inst_dst.msg] == -1):
                            #     # Two rules are conflicting (here we
                            #     # try to enalbe inst_dst.msg while
                            #     # another rule that applies to the
                            #     # event disables it)
                            #     raise Exception("Found two conflicting rules")

                            self.msgs[cevt_msg].msg_enabled[inst_dst.msg] = 1
                        else:
                            assert (rule.specType == SpecType.Disable or
                                    rule.specType == SpecType.Disallow)

                            if (rule.specType == SpecType.Disable):
                                # msg is a callin that can be disabled
                                self.msgs[inst_dst.msg].disabled = True

                            # if (self.msgs[cevt_msg].msg_enabled[inst_dst.msg] == 1):
                            #     # Two rules are conflicting (here we
                            #     # try to disalbe inst_dst.msg while
                            #     # another rule that applies to the
                            #     # event enables it)
                            #     raise Exception("Found two conflicting rules")
                            self.msgs[cevt_msg].msg_enabled[inst_dst.msg] = -1

        logging.debug("START: matching rules for %s..." % msg_evt)

    def _encode_evt(self, cevent):
        """Encode the transition relation of a single event."""
        logging.debug("Encoding event %s" % cevent)

        evt_msg = self.conc_to_msg[cevent]
        (msg_enabled, guards, bug_ci, must_be_allowed) = (self.msgs[evt_msg].msg_enabled,
                                                          self.msgs[evt_msg].guards,
                                                          self.msgs[evt_msg].bug_ci,
                                                          self.msgs[evt_msg].must_be_allowed)
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
                must_ci_formula = And([self.msgs_to_var[v] for v in must_be_allowed])
                # All the CIs in must_be_allowed are allowed
                # iff there is no bug.
                evt_trans = Iff(must_ci_formula,
                                Not(self._next(self.ts_error)))

            if (len(guards) > 0):
                # logging.debug("Add guards " + str(guards))
                evt_trans = And(evt_trans, And([self.msgs_to_var[v] for v in guards]))
            if (len(next_effects) > 0):
                # logging.debug("Add effects " + str(next_effects))
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

        # logging.debug("Event %s: trans is %s" % (cevent.symbol, str(evt_trans)))

        return evt_trans

    def _init_ts_trans(self):
        """Initialize the ts trans."""
        logging.debug("Encoding the trans...")

        # Perform the encoding
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


    def _build_trace(self, model, steps):
        """Extract the trace from the satisfying assignment."""

        vars_to_use = [self.ts_state_vars, self.ts_input_vars]
        cex = []
        for i in range(steps + 1):
            cex_i = {}

            # skip the input variables in the last step
            if (i >= steps):
                vars_to_use = [self.ts_state_vars]

            for vs in vars_to_use:
                for var in vs:
                    var_i = self.helper.get_var_at_time(var, i)
                    cex_i[var] = model.get_value(var_i, True)
            cex.append(cex_i)
        return cex

    def print_cex(self, cex, changed=False, readable=True):
        def _print_var_set(varset, step, prev_state,
                           only_true = False,
                           skipinit = True,
                           only_changed = True):
            def _print_val(key,val,msg):
                if None != msg:
                    print("(%s): %s: %s" % (msg, key, value))
                else:
                    print("%s: %s" % (key, value))
            if skipinit:
                print "All events/callins are enabled"

            for key in varset:
                assert key in step

                if key in self.var_to_msgs:
                    message = self.var_to_msgs[key]
                else:
                    message = None

                value = step[key]
                if only_changed:
                    if (key not in prev_state or
                        (key in prev_state and
                        prev_state[key] != value)):
                        if only_true and value == FALSE():
                            continue
                        if not skipinit:
                            _print_val(key,value,message)
                    prev_state[key] = value
                else:
                    if only_true and value == FALSE():
                        continue
                    if not skipinit:
                        _print_val(key,value,message)

        sep = "----------------------------------------"
        i = 0

        prev_state = {}

        print("")
        print("--- Counterexample ---")
        print(sep)
        for step in cex:
            print("State - %d" % i)
            print(sep)

            _print_var_set(self.ts_state_vars, step, prev_state, False,
                           (readable and i == 0), changed)

            # skip the last input vars
            if (i >= (len(cex)-1)): continue
            print(sep)
            print("Input - %d" % i)
            print(sep)
            _print_var_set(self.ts_input_vars, step, prev_state, True,
                           False, False)
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

        all_vars = self._get_ts_var()
        # Set the variables of the ts
        for i in range(steps + 1):
            logging.debug("Encoding %d..." % i)

            if (i == 0):
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts_init, i)
            else:
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts_trans, i-1)
            solver.add_assertion(f_at_i)

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
            trace = self._build_trace(model, steps)

            return trace
        else:
            # No bugs found
            logging.debug("No bugs found up to %d steps" % steps)
            return None

    def find_bug_inc(self, steps):
        """ Incremental version of bmc check
        """

        solver = Solver(name='z3', logic=QF_BOOL)

        error_condition = []

        all_vars = self._get_ts_var()
        # Set the variables of the ts
        for i in range(steps + 1):
            logging.debug("Encoding %d..." % i)

            if (i == 0):
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts_init, i)
            else:
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts_trans, i-1)
            solver.add_assertion(f_at_i)

            solver.push()
            bug_at_i = self.helper.get_formula_at_i(all_vars,
                                                    self.ts_error,
                                                    i)
            solver.add_assertion(bug_at_i)

            logging.debug("Finding bug at %d steps..." % steps)
            res = solver.solve()
            if (solver.solve()):
                logging.debug("Found bug...")

                model = solver.get_model()
                trace = self._build_trace(model, i)

                return trace
            else:
                # No bugs found
                logging.debug("No bugs found up to %d steps" % steps)
                solver.pop()
        return None

    def to_smv(self, stream):
        translator = SmvTranslator(self.env,
                                   self.ts_state_vars,
                                   self.ts_input_vars,
                                   self.ts_init,
                                   self.ts_trans,
                                   Not(self.ts_error))
        translator.to_smv(stream)

################################################################################
# SIMPLIFICATION - TO MOVE
################################################################################

    def _get_containing_evt(self, frontier):
        """ Get the event instances that call a callin contained in
        frontier.
        """
        events_in_frontier = set()
        for inst in frontier:
            if inst.msg in self.ci_to_evt:
                events_of_ci = self.ci_to_evt[inst.msg]
                for evt_of_ci in events_of_ci:
                    # add all the instances of evt_of_ci
                    for i in self.msgs_to_instances[evt_of_ci]:
                        events_in_frontier.add(i)
        frontier.update(events_in_frontier)

        return frontier


    def _get_buggy_instances(self):
        """ Get the set of instances that can be disabled and thus
        cause a vioalation.
        """
        buggy_instances = set()
        for rule in self.specs:
            if (rule.specType == SpecType.Disallow):
                if rule.dst not in self.symbol_to_instances: continue
                for inst in self.symbol_to_instances[rule.dst]:
                    buggy_instances.add(inst)
        buggy_instances = self._get_containing_evt(buggy_instances)
        return buggy_instances

    def _compute_pre(self, frontier):
        """ Given a set of instances, it returns all the instances
        that can enable/disable one instance in the set.
        """

        new_frontier = set()
        for inst in frontier:
            # find the instances that can enable/disable inst
            # We find the rules that can have effects in inst, and
            # then find the instances that can match them.
            for rule in self.specs:
                if rule.dst == inst.symbol:
                    if not rule.src in self.symbol_to_instances:
                        # No instances that match rule.src
                        continue

                    # Instantiate the paramter on the lhs of the rule
                    dst_env = self._build_env({}, rule.dst_args, inst.args)
                    conc_src_args = self._inst_param_rule(rule.src_args, dst_env)

                    for prev_inst in self.symbol_to_instances[rule.src]:
                        # we only add the instances that can match the
                        # parameters
                        if self._match_args(prev_inst.args, conc_src_args):
                            new_frontier.add(prev_inst)

        # Add the instances of the events that call a ci in the
        # frontier
        new_frontier = self._get_containing_evt(new_frontier)

        return new_frontier

    def _computes_relevant_instances(self):
        """ Computes the set of relevant instances.

        Definition - relevant instance.

        - An event instance is relevant if:
          - it calls a relevant callin instance
          - it can enable/disable (allow/disallow) a relevant event
            (callin) instance

        - A callin instance is relevant if:
          - it can be disabled
          - it can enable/disable (allow/disallow) a relevant event
            (callin) instance

        The set is computed with a fixed point algorithm.
        """

        # Initialize the relevant instances with the callins that can be disabled
        relevant_instances = self._get_buggy_instances()
        frontier = set(relevant_instances)

        # Fix-point computation of the relevant set
        prev_size = 0
        while prev_size != len(relevant_instances):
            prev_size = len(relevant_instances)
            # compute the frontier
            frontier = self._compute_pre(frontier)
            # get the new set of "reachable" instances
            relevant_instances.update(frontier)

        return relevant_instances


    def _simplify(self):
        """ Simplify the concrete trace according to the current
        specification.
        """
        # get the relevant instances
        relevant_instances = self._computes_relevant_instances()

        # get the relevant messages
        relevant_msgs = set()
        for msg in self.msgs.evt_info.keys():
            is_relevant = False
            if msg in self.msgs_to_instances:
                for inst in self.msgs_to_instances[msg]:
                    if inst in relevant_instances:
                        is_relevant = True
            if is_relevant:
                relevant_msgs.add(msg)

        # Create a new trace
        new_ctrace = ConcreteTrace()
        new_ctrace.events.append(CEvent("initial"))
        for cevt in self.ctrace.events:
            evt_msg = self.conc_to_msg[cevt]
            if evt_msg not in relevant_msgs: continue

            new_cevt = CEvent(cevt.symbol)
            new_cevt.args = list(cevt.args)
            new_ctrace.events.append(new_cevt)

            for ccb in cevt.cb:
                new_ccb = CCallback(ccb.symbol)
                new_ccb.args = list(ccb.args)
                new_cevt.cb.append(new_ccb)

                for cci in ccb.ci:
                    ci_name = self._get_ci_msg(cci)
                    if ci_name not in relevant_msgs: continue
                    new_cci = CCallin(cci.symbol)
                    new_cci.args = list(cci.args)
                    new_ccb.ci.append(new_cci)

        # change the traces
        self.ctrace = new_ctrace

        # Create a new matchinfo structure
        self.msgs = MatchInfo(self)
        # process the trace again
        self._process_trace()

class MsgInfo(object):
    def __init__(self, msg):
        self.msg = msg
        # set of concrete messages in the trace that have
        # been mapped to the same message
        self.conc_msgs = set()
        # List of matches
        # A match is a tuple (rule, match_inst, eff_inst) where:
        # - rule: is a rule from specs
        # - match_inst: instantiation that matched the premise of the rule
        # - eff_inst: instantiation that matched the consequence of the rule
        self.matches = []

    def add_match(self, rule, match_inst, eff_inst):
        # Helper function to add a match
        self.matches.append((rule, match_inst, eff_inst))

class CiInfo(MsgInfo):
    def __init__(self, msg):
        super(CiInfo, self).__init__(msg)
        # is_disabled tracks if the Ci can be disabled by some rule
        self.is_disabled = False

class EventInfo(MsgInfo):
    def __init__(self, evt_msg):
        super(EventInfo, self).__init__(evt_msg)
        # Map from messages (events and callins) to their state that
        # could be:
        # 0  if (unkonwn), 1 (enabled/allowed), -1 (disabled/disallowed)
        # The map must be initialized by the caller.
        # The map represent the deterministic effects due to the
        # execution of the event.
        self.msg_enabled = None
        # Set of message symbols that must be enabled/allowed to
        # enable the transition of the event.
        self.guards = set()
        # set of CIs that must be allowed to execute the event without
        # ending in a bug
        self.must_be_allowed = set()
        # set of 
        self.effects = set()
        # First ci that cannot be called (if any)
        # Corner case where just observing the sequence of CI in an
        # event we can determine that we reach a bug.
        self.bug_ci = None

class MatchInfo:
    """ Stores and print the information to explain how we obtained
        the transition system.
    """

    def __init__(self, verifier):
        # need access to the verifier
        self.verifier = verifier

        # maps from msgs to message information
        self.evt_info = {}

        # map from concrete message in the trace to index
        self.cmsgs_to_index = {}
        evt_index = 0
        for cevt in self.verifier.ctrace.events:
            evt_index = evt_index + 1
            self.cmsgs_to_index[cevt] = [str(evt_index)]

            cb_index = 0
            for ccb in cevt.cb:
                cb_index = cb_index + 1
                self.cmsgs_to_index[ccb] = [str(evt_index), str(cb_index)]

                ci_index = 0
                for cci in ccb.ci:
                    ci_index = ci_index + 1
                    self.cmsgs_to_index[cci] = [str(evt_index),
                                                str(cb_index),
                                                str(ci_index)]

    def __setitem__(self, msg_name, evt_info):
        self.evt_info[msg_name] =  evt_info

    def __getitem__(self, msg_name):
        return self.evt_info[msg_name]

    def print_info(self):
        print("\n--- Encoding information ---")
        (count_e, count_ci) = (0,0)
        for msg_name, dbg_info in self.evt_info.iteritems():
            if isinstance(dbg_info, EventInfo):
                count_e = count_e + 1
            else:
                count_ci = count_ci + 1
        total = count_e + count_ci
        print("Processed %d messages (%d events, %d callins)\n" \
              % (total, count_e, count_ci))

        i = 0
        for msg_name, dbg_info in self.evt_info.iteritems():
            i = i + 1

            is_evt = isinstance(dbg_info, EventInfo)
            if not is_evt: prefix = "Callin"
            else: prefix = "Event"
            print("(%d/%d) %s: %s" % (i, total, prefix, dbg_info.msg))

            readable_msgs = []
            for l in  dbg_info.conc_msgs:
                ",".join(self.cmsgs_to_index[l])
                readable_msgs.append(",".join(self.cmsgs_to_index[l]) +
                                     " " +
                                     str(l.symbol))
            str_msgs = "  \n".join(readable_msgs)
            print("Concrete messages:\n  %s" % (str_msgs))

            print("List of matches:")
            for (rule, inst, dst_inst) in dbg_info.matches:
                print("--- Match ---")
                print("Matched instance: %s(%s)" % (inst.symbol, ",".join(inst.args)))
                if (dst_inst == None):
                    print("No effects.")
                else:
                    print("Matched effects: %s(%s)" % (dst_inst.symbol, ",".join(dst_inst.args)))
                print rule.get_print_desc()
            if is_evt:
                print("Guards: %s" % ",".join(list(dbg_info.guards)))
                print("Required callins:\n  %s" % "\n  ".join(list(dbg_info.must_be_allowed)))
                print("Effects: %s" % ",".join(list(dbg_info.effects)))
                if dbg_info.bug_ci != None:
                    print("Event ends in bug %s" % (dbg_info.bug_ci))
            print("-------------")



