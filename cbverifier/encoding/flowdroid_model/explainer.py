""" Explain why a simulation run got stuck.

When we cannot simulate a recorded trace we want do localize what
part of the lifecycle model was responsible for that.

"""

import logging

from cbverifier.encoding.encoder import TSMapback
from cbverifier.encoding.encoder_utils import EncoderUtils
from cbverifier.encoding.flowdroid_model.encoder import FlowDroidEncoder
from cbverifier.encoding.flowdroid_model.lifecycle_constants import Component, Activity, Fragment

from pysmt.shortcuts import Iff

class Explainer:
    def __init__(self, encoder, mapback, last_cex, trace, tl_cb_ids = None):
        """
        last_cex is the last counter-example extracted from the
        trace.
        """
        self.encoder = encoder
        self.mapback = mapback
        self.last_cex = last_cex
        self.trace = trace
        self.tl_cb_ids = tl_cb_ids

    def find_failure(self):
        """
        Finds the cause of simulation failure.

        Returns a FailureType object.
        """

        if self.last_cex is None:
            # Special case - initial state of the simulation
            # is unsat.
            # It should not happen in the FlowDroid model
            return FailureInit(None)

        # get the message that got stuck in the trace
        stuck_msg = self._get_stuck_msg()

        # get how the message is constrained in the FlowDroid model
        res = self.encoder.fd_builder.get_msg_properties(stuck_msg)
        (is_constrained, is_lifecycle, owner_activities, owner_fragments) = res

        # Get the information from the cex
        res = self.get_cex_info()
        (running_activities, active_activities,
         infrag_activities, running_fragments) = res

        return Explainer._triage_failure(stuck_msg,
                                         is_constrained,
                                         is_lifecycle,
                                         owner_activities,
                                         owner_fragments,
                                         running_activities, active_activities,
                                         infrag_activities, running_fragments)

    @staticmethod
    def _triage_failure(stuck_msg,
                        is_constrained,
                        is_lifecycle,
                        owner_activities,
                        owner_fragments,
                        running_activities, active_activities,
                        infrag_activities, running_fragments):

        # Decide the failure reason
        if not (is_lifecycle or is_constrained):
            return FailureUnknown(stuck_msg,
                                  "Stuck on neither a lifecylce or " \
                                  "constrained msg")
        elif (is_lifecycle):
            return Explainer.analyze_failure_lifecycle(stuck_msg,
                                                       owner_activities,
                                                       owner_fragments,
                                                       running_activities,
                                                       active_activities,
                                                       infrag_activities,
                                                       running_fragments)
        else:
            assert is_constrained
            return Explainer.analyze_failure_constrained(stuck_msg,
                                                         owner_activities,
                                                         owner_fragments,
                                                         running_activities,
                                                         active_activities,
                                                         infrag_activities,
                                                         running_fragments)

    @staticmethod
    def analyze_failure_constrained(stuck_msg,
                                    owner_activities, owner_fragments,
                                    running_activities, active_activities,
                                    infrag_activities, running_fragments):

        if (not owner_activities.isdisjoint(running_activities)):
            # The msg activities are running
            if (owner_activities.isdisjoint(active_activities)):
                # The msg activities are running but not active now
                if (not owner_fragments.isdisjoint(running_fragments)):
                    # Fragment execution cannot be preemted in FD
                    return FailureFragInterleaving(stuck_msg,
                                                   owner_activities,
                                                   owner_fragments)
                else:
                    # CB should have been possible outside the active
                    # lifecycle
                    return FailureCbNonActive(stuck_msg, owner_activities)
            else:
                # msg are running and active: this should not happen
                return FailureUnknown(stuck_msg, "Stuck even if activity is " \
                                      "active!")
        else:
            # The msg activities are not running
            return FailureActInterleaving(stuck_msg, owner_activities)


    @staticmethod
    def analyze_failure_lifecycle(stuck_msg,
                                  owner_activities,
                                  owner_fragments,
                                  running_activities,
                                  active_activities,
                                  infrag_activities,
                                  running_fragments):

        msg_from_activity = len(owner_fragments) == 0

        if (msg_from_activity):
            # msg from activity lc
            if(not owner_activities.isdisjoint(running_activities) or
               len(running_activities) == 0):
                # activity is running: cannot execute the LC message!
                return FailureActLc(stuck_msg, owner_activities)
            else:
                # activity cannot run
                return FailureActInterleaving(stuck_msg, owner_activities)
        else:
            # msg from fragment lc
            if(not owner_activities.isdisjoint(running_activities)):
                # activity is running
                if (not owner_activities.isdisjoint(infrag_activities)):
                    # Activity is in the fragment state
                    # The lifecycle message from the fragment is stuck
                    return FailureFragLc(stuck_msg, owner_activities,
                                         owner_fragments)
                else:
                    # Activity is not in the fragment state
                    return FailureFragNonActive(stuck_msg, owner_activities,
                                                owner_fragments)
            else:
                # activity containing the fragment cannot run
                return FailureActInterleaving(stuck_msg, owner_activities)

    def _get_stuck_msg(self):
        """ Find the message that got stuck

        Return the message (string)
        """
        linear_trace = self.encoder._get_linear_trace(self.tl_cb_ids)

        assert not self.last_cex is None

        # trace from bmc counts states, not transitions
        simulated_length = len(self.last_cex) - 1
        i = 0
        for (entry_type, msg) in linear_trace:
            msg_key = EncoderUtils.get_key_from_msg(msg, entry_type)
            if not self.encoder._is_msg_visible(msg_key):
                continue

            i = i + 1
            if (i == (simulated_length + 1)):
                # Returns the first message that was not
                # simualted
                return msg_key

        return None


    def get_cex_info(self):
        """
        Extracts the information from the CEX.

        Returns a tuple containing:
          - running_activities: the current running activities.
          - active_activites: set of activities in the active state
          - infrag_activities: set of activities in the before on_start state
          - running_fragments: the current running fragments.

        Sets and maps contains the activity and fragment python
        objects
        """

        def are_eq(solver, f1, f2):
            """ True iff [f1 <-> f2] is valid """
            return solver.is_valid(Iff(f1, f2))

        running_activities = set()
        active_activities = set()
        infrag_activities = set()
        running_fragments = set()

        assert not self.last_cex is None

        solver = EncoderUtils.get_new_solver(self.encoder.pysmt_env)
        last_step = self.last_cex[-1:][0]

        component_pcs = self.mapback.get_component_pcs(last_step)
        for (pc_var, component, pc_value) in component_pcs:
            pc_value_eq = self.encoder.fd_enc._eq_val(pc_var, pc_value)

            if component in self.encoder.fd_enc.lifecycles:
                component_lc = self.encoder.fd_enc.lifecycles[component]

                if isinstance(component, Activity):
                    pc_in_init = component_lc.get_label(
                        FlowDroidEncoder.ActivityLcInfo.INIT)
                    pc_in_active = component_lc.get_label(
                        FlowDroidEncoder.ActivityLcInfo.IS_ACTIVE)
                    pc_in_frag = component_lc.get_label(
                        FlowDroidEncoder.ActivityLcInfo.BEFORE_ONSTART)

                    if (not are_eq(solver, pc_value_eq, pc_in_init)):
                        running_activities.add(component)

                    if (are_eq(solver, pc_value_eq, pc_in_active)):
                        active_activities.add(component)

                    if (are_eq(solver, pc_value_eq, pc_in_frag)):
                        infrag_activities.add(component)

                elif isinstance(component, Fragment):
                    pc_in_init = component_lc.get_label(
                        FlowDroidEncoder.FragmentLcInfo.INIT)

                    if (not are_eq(solver, pc_value_eq, pc_in_init)):
                        running_fragments.add(component)

        return (running_activities, active_activities,
                infrag_activities, running_fragments)


class FailureType(object):
    def __init__(self, stuck_msg):
        """
        stuck_msg is the first message that cannot be simualted
        from the trace
        """
        self.stuck_msg = stuck_msg

    def get_stuck_msg(self):
        return self.stuck_msg

    @staticmethod
    def get_clist_str(component_list):
        c_repr_list = []
        for c in component_list:
            if isinstance(c, Component):
                c_repr_list.append(str(c.get_inst_value()))
            else:
                c_repr_list.append(str(c))
        c_repr = ",".join(c_repr_list)
        return c_repr


class FailureUnknown(FailureType):
    def __init__(self, stuck_msg, explanation = None):
        FailureType.__init__(self, stuck_msg)
        self.explanation = explanation

    def __repr__(self):
        msg = """Failure: FailureUnknown
        Blocked message: %s
        Explanation: %s
        """ % (self.stuck_msg,
               self.explanation)
        return msg

class FailureInit(FailureType):
    def __init__(self, stuck_msg):
        FailureType.__init__(self, stuck_msg)

    def __repr__(self):
        msg = """Failure: FailuerInit
        """
        return msg

class FailureActivity(FailureType):
    def __init__(self, act_failure_name, stuck_msg, owner_activities):
        FailureType.__init__(self, stuck_msg)
        self.act_failure_name = act_failure_name
        self.owner_activities = owner_activities

    def __repr__(self):
        msg = """Failure: %s
        Blocked message: %s
        Owner activities: %s
        """ % (self.act_failure_name, self.stuck_msg,
               FailureType.get_clist_str(self.owner_activities))
        return msg

class FailureFragment(FailureType):
    def __init__(self, act_failure_name, stuck_msg,
                 owner_activities,
                 owner_fragments):
        FailureType.__init__(self, stuck_msg)
        self.act_failure_name = act_failure_name
        self.owner_activities = owner_activities
        self.owner_fragments = owner_fragments

    def __repr__(self):
        msg = """Failure: %s
        Blocked message: %s
        Owner activities: %s
        Owner fragments: %s
        """ % (self.act_failure_name, self.stuck_msg,
               FailureType.get_clist_str(self.owner_activities),
               FailureType.get_clist_str(self.owner_fragments))
        return msg

class FailureCbNonActive(FailureActivity):
    DESC = "FailureCbNonActive"
    def __init__(self, stuck_msg, owner_activities):
        FailureActivity.__init__(self,
                                 self.DESC,
                                 stuck_msg,
                                 owner_activities)

class FailureActLc(FailureActivity):
    DESC = "FailureActLc"
    def __init__(self, stuck_msg, owner_activities):
        FailureActivity.__init__(self,
                                 self.DESC,
                                 stuck_msg,
                                 owner_activities)

class FailureActInterleaving(FailureActivity):
    DESC = "FailureActInterleaving"
    def __init__(self, stuck_msg, owner_activities):
        FailureActivity.__init__(self,
                                 self.DESC,
                                 stuck_msg,
                                 owner_activities)


class FailureFragLc(FailureFragment):
    DESC = "FailureFragLc"
    def __init__(self, stuck_msg,
                 owner_activities,
                 owner_fragments):
        FailureFragment.__init__(self,
                                 self.DESC,
                                 stuck_msg,
                                 owner_activities,
                                 owner_fragments)

class FailureFragNonActive(FailureFragment):
    DESC = "FailureFragNonActive"
    def __init__(self, stuck_msg,
                 owner_activities,
                 owner_fragments):
        FailureFragment.__init__(self,
                                 self.DESC,
                                 stuck_msg,
                                 owner_activities,
                                 owner_fragments)


class FailureFragInterleaving(FailureFragment):
    DESC = "FailureFragInterleaving"
    def __init__(self, stuck_msg,
                 owner_activities,
                 owner_fragments):
        FailureFragment.__init__(self,
                                 self.DESC,
                                 stuck_msg,
                                 owner_activities,
                                 owner_fragments)
