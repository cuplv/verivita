""" Encodes a "FlowDroid-like" lifecycle model.


We follow the description in Section 3 "Precise Modeling of Lifecycle" of:

'FlowDroid: Precise Context, Flow, Field, Object-sensitive and Lifecycle-aware
Taint Analysis for Android Apps',
Artz et al, PLDI 14

and in particular the implementation in:
soot-infoflow/src/soot/jimple/infoflow/entryPointCreators/AndroidEntryPointCreator.java
in the repository http://github.com/secure-software-engineering/FlowDroid,
commit a1438c2b38a6ba453b91e38b2f7927b6670a2702.


We encode the lifecylce of each component forcing that at most one
component can be active at each time. For each component, there is a
different definition of active. For example, an activity component is
active after the onResume and before the onPause callbacks.

We relax the contraint that callbacks in the
android.app.Application.ActivityLifecycleCallbacks must exist and
executed at least one.

We follow the modeling where registered callbacks cannot happen
outside the activity lifecycle.

We assume that non-registered callbacks can happen at any time. This
over-approximate the resulting model.
The consequence is:
- our model is "more sound" than the flowdroid one: we do not block the
  execution of callbacks for which we did not find a registration
- our model may be "less precise" than the flowdroid one, since it may allow
  more spurious trace.

We model the lifecycle for activity and fragment components since we are
interested in components that run in the UI thread.

As done in FlowDroid, we encode the lifecycle component of fragment inside
their attaching activity component.
"""

import logging

from pysmt.logics import QF_BOOL
from pysmt.environment import get_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol
from pysmt.shortcuts import Solver
from pysmt.shortcuts import TRUE as TRUE_PYSMT
from pysmt.shortcuts import FALSE as FALSE_PYSMT
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne
from pysmt.shortcuts import simplify

from cbverifier.encoding.ts import TransitionSystem
from cbverifier.encoding.flowdroid_model.flowdroid_model_builder import FlowDroidModelBuilder
from cbverifier.encoding.flowdroid_model.lifecycle_constants import Activity, Fragment

from cbverifier.utils.utils import is_debug


class FlowDroidEncoder:
    def __init__(self, enc, fd_builder):
        self.enc = enc
        self.fd_builder = fd_builder
        self.ts = None

    def get_ts_encoding(self):
        if (self.ts is None):
            self._encode()
        return self.ts

    def _encode(self):
        """ Create an encoding of the FlowDroid model.

        Returns a transition system representing the FlowDroid model of
        the callback control-flow.

        The transition system can be composed to the disallow set of
        specification and to the callback re-ordering from the trace.
        """
        # Encode the lifecycle for each component
        lifecycles = {}
        for c in self.fd_builder.get_components():
            lifecycles[c] = self._encode_component_lifecycle(c)

        # Encode the component scheduler
        # We must change the ts of the other components to add the
        # stuttering!
        ts_scheduler = self._encode_components_scheduler(lifecycles)

        self.enc.mapback.add_state_vars(ts_scheduler.state_vars)

        self.ts = ts_scheduler

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


    def _check_for_deadlocks(self, trans, pc, pc_size):
        """
        Checks for deadlocks in each state of the generated automaton
        """
        solver = self.enc.pysmt_env.factory.Solver(quantified=False,
                                                   name="z3",
                                                   logic=QF_BOOL)
        solver.add_assertion(trans)
        for i in range(pc_size-1):
            solver.push()
            solver.add_assertion(self._eq_val(pc, i))
            is_sat = solver.solve()
            solver.pop()

            if (is_sat):
                result = "%s = %s can move" % (pc, str(i))
            else:
                result = "%s = %s is in deadlock" % (pc, str(i))

    def _encode_activity_lifecycle(self, activity):
        """
        Encode the lifecycle for activity.

        Return an FlowDroidEncoder.ActivityLcInfo object
        """

        ts = TransitionSystem()

        # Add the program counter variable to encode the lifecycle
        # is the maximum number of states in the automaton
        # encoded in the activity lifecycle
        # (see how many times pc is incremented there)
        pc_size = 19
        pc = "pc_act_" + (activity.get_inst_value().get_value())
        self.enc.cenc.add_var(pc, pc_size - 1) # -1 since it starts from 0
        for v in self.enc.cenc.get_counter_var(pc): ts.add_var(v)

        self.enc.mapback.add_pc2component(pc, activity)
        self.enc.mapback.add_encoder(pc, self.enc.cenc)

        # Start from the initial state
        pc_val = 0
        entry_label = pc_val
        ts.init = self.enc.cenc.eq_val(pc, pc_val)

        ts.trans = FALSE_PYSMT() # disjunction of automata transitions

        # Encode the lifecycle

        # line 793
        pc_val = self._enc_component_step(activity,
                                          Activity.ONCREATE,
                                          ts, pc, pc_val, pc_val + 1)


        # line 795
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYCREATED,
                                          ts, pc, pc_val, pc_val + 1, True,
                                          True)

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
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)

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
                                          True, True)
        # line 876
        pc_val = self._enc_component_step(activity,
                                          Activity.ONPOSTRESUME,
                                          ts, pc, pc_val, pc_val + 1)

        # Now we can execute all the activity callbacks
        # We pass back this condition to encode the scheduling of the
        # activity callbacks
        activity_is_active = self._eq_val(pc, pc_val)


        # encode activity-bounded callbacks
        all_cb_labels = self._encodes_non_lc_callback(activity)
        current_pc_val_enc = self._eq_val(pc, pc_val)
        self_loop = self._get_next_formula(ts.state_vars,
                                           current_pc_val_enc)
        single_trans = And(all_cb_labels,
                           And(current_pc_val_enc, self_loop))
        ts.trans = Or(ts.trans, single_trans)

        self._enc_component_step(activity,
                                 Activity.ONPAUSE,
                                 ts, pc, pc_val, pc_val)


        # line 916
        pc_val = self._enc_component_step(activity,
                                          Activity.ONPAUSE,
                                          ts, pc, pc_val, pc_val + 1)

        # line 918
        pc_val = self._enc_component_step(activity,
                                          Activity.ONACTIVITYPAUSED,
                                          ts, pc, pc_val, pc_val + 1,
                                          True, True)

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
                                          True, True)
        # line 930
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYSAVEINSTANCESTATE,
                                 ts, pc, before_onActivitySaveInstanceState_label,
                                 before_onResume_label,
                                 True, True)

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
                                          True, True)
        # line 943
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYSTOPPED,
                                 ts, pc,
                                 before_onActivityStopped_label,
                                 before_onStop_label,
                                 True, True)
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
        pc_val = self._enc_component_step(activity,
                                          Activity.ONDESTROY,
                                          ts, pc, pc_val, pc_val + 1)
        # line 948
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYSTOPPED,
                                 ts, pc,
                                 pc_val,
                                 before_onDestroy_label,
                                 True, True)
        # line 960 - go back to the beginning
        self._enc_component_step(activity,
                                 Activity.ONACTIVITYDESTROYED,
                                 ts, pc, pc_val, entry_label,
                                 True, True)

        lc_info = FlowDroidEncoder.ActivityLcInfo(ts, pc, pc_size)
        lc_info.add_label(FlowDroidEncoder.ActivityLcInfo.INIT,
                          self._eq_val(pc, entry_label))
        lc_info.add_label(FlowDroidEncoder.ActivityLcInfo.END,
                          self._eq_val(pc, pc_val))
        lc_info.add_label(FlowDroidEncoder.ActivityLcInfo.BEFORE_ONSTART,
                          self._eq_val(pc, before_onStartStmt_label))
        lc_info.add_label(FlowDroidEncoder.ActivityLcInfo.IS_ACTIVE,
                          activity_is_active)

        if is_debug():
            self._check_for_deadlocks(lc_info.ts.trans,
                                      lc_info.pc,
                                      lc_info.pc_size)
        return lc_info

    def _encode_fragment_lifecycle(self, fragment):
        """
        Encode the lifecycle for activity.

        Return a FlowDroidEncoder.FragmentLcInfo object
        """
        ts = TransitionSystem()

        pc_size = 13 # init state + 12 (+ 1) of pc counter
        pc = "pc_frag_" + (fragment.get_inst_value().get_value())
        self.enc.cenc.add_var(pc, pc_size - 1) # -1 since it starts from 0
        for v in self.enc.cenc.get_counter_var(pc): ts.add_var(v)
        self.enc.mapback.add_pc2component(pc, fragment)
        self.enc.mapback.add_encoder(pc, self.enc.cenc)

        pc_val = 0
        entry_label = pc_val
        ts.init = self.enc.cenc.eq_val(pc, pc_val)

        ts.trans = FALSE_PYSMT() # disjunction of transitions

        # line 821, 820
        self._enc_component_step(fragment,
                                 Fragment.ONATTACHFRAGMENT,
                                 ts, pc, pc_val, pc_val)

        # line 986
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONATTACH,
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)
        # line 992
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONCREATE,
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)
        before_onCreateview_label = pc_val
        # line 998
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONCREATEVIEW,
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)
        # line 1003
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONVIEWCREATED,
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)
        # line 1009
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONACTIVITYCREATED,
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)
        before_onStart_label = pc_val
        # line 1015
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONSTART,
                                          ts, pc, pc_val, pc_val + 1,
                                          False, True)
        # line 1021
        before_onResume_label = pc_val
        # line 1022
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONRESUME,
                                          ts, pc, pc_val, pc_val + 1)
        # line 1025
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONPAUSE,
                                          ts, pc, pc_val, pc_val + 1)
        # line 1026
        self._enc_component_step(fragment,
                                 Fragment.ONPAUSE,
                                 ts, pc, pc_val,  before_onResume_label)

        # line 1029
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONSAVEINSTANCESTATE,
                                          ts, pc, pc_val, pc_val + 1)
        # line 1032
        before_onStop_label = pc_val
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONSTOP,
                                          ts, pc, before_onStop_label,
                                          pc_val + 1)
        # line 1033
        self._enc_component_step(fragment,
                                 Fragment.ONSTOP,
                                 ts, pc, pc_val,
                                 before_onCreateview_label)
        # line 1034
        self._enc_component_step(fragment,
                                 Fragment.ONSTOP,
                                 ts, pc, pc_val,
                                 before_onStart_label)

        # line 1037
        before_onDestroyView_label = pc_val
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONDESTROYVIEW,
                                          ts, pc, pc_val, pc_val+1)
        # line 1038
        self._enc_component_step(fragment,
                                 Fragment.ONDESTROYVIEW,
                                 ts, pc, pc_val,
                                 before_onCreateview_label)
        # line 1041
        pc_val = self._enc_component_step(fragment,
                                          Fragment.ONDESTROY,
                                          ts, pc, pc_val, pc_val + 1)
        # line 1044, 1045
        self._enc_component_step(fragment,
                                 Fragment.ONDETACH,
                                 ts, pc, pc_val, entry_label)

        lc_info = FlowDroidEncoder.FragmentLcInfo(ts, pc, pc_size)
        lc_info.add_label(FlowDroidEncoder.FragmentLcInfo.INIT,
                          self._eq_val(pc, entry_label))
        lc_info.add_label(FlowDroidEncoder.FragmentLcInfo.END,
                          self._eq_val(pc, pc_val))

        return lc_info


    def _encodes_non_lc_callback(self, c):
        """ Get the list of callbacks bounded by the activity lifecycle
        """
        cb_msg_enc = FALSE_PYSMT()
        for msg_key in self.fd_builder.get_comp_callbacks(c.get_inst_value()):
            cb_msg_enc = Or(cb_msg_enc,
                            self._get_msg_label(msg_key))
        return cb_msg_enc

    def _encode_free_messages(self):
        """ Returns the encoding of the free messages """
        # Do nothing for the other callbacks -- they are free
        # to happen whenever
        #
        # We block all the messages that are part of the
        # lifecycle
        cb_msg_enc = TRUE_PYSMT()
        for msg in self.fd_builder.get_const_msgs():
            msg_enc = Not(self._get_msg_label(msg))
            cb_msg_enc = And(cb_msg_enc, msg_enc)

        return cb_msg_enc

    def _encode_components_scheduler(self, lifecycles):

        ts_sched = TransitionSystem()

        """ Encode a boolean activation variable for each component and
        for all the other callbacks
        """
        # 1. Encode a Boolean activation variable for each
        #    component
        comp2actflags = {}
        for c in self.fd_builder.get_components():
            c_act = "act_component_%s" % c.get_inst_value().get_value()
            self.enc.cenc.add_var(c_act, 1)
            counter_vars = self.enc.cenc.get_counter_var(c_act)
            assert (len(counter_vars) == 1)
            for act_flag in counter_vars:
                ts_sched.add_var(act_flag)
                comp2actflags[c] = act_flag
                self.enc.mapback.add_actvar2component(act_flag, c)

        run_free_msg_name = "_run_free_msg_"
        self.enc.cenc.add_var(run_free_msg_name, 1)
        counter_vars = self.enc.cenc.get_counter_var(run_free_msg_name)
        assert (len(counter_vars) == 1)
        run_free_msg_flag = None
        for flag in counter_vars:
            ts_sched.add_var(flag)
            run_free_msg_flag = flag
            # Add the mapback in the map for debug
            # self.enc.mapback.add_actvar2component(act_flag, c)
        assert not run_free_msg_flag is None

        # 3. Compose the components' lifecycle
        for c, c_lc in lifecycles.iteritems():
            lc_info = lifecycles[c]
            flag = comp2actflags[c]

            # Frame condition for the pc of the lifecycle automaton
            fc_ts = TRUE_PYSMT()
            for var in lc_info.ts.state_vars:
                # Defensive programming - avoid flag in the fc, since it
                # must change
                fc_ts = And(Iff(var,
                                self._get_next_formula(lc_info.ts.state_vars,var)),
                            fc_ts)

            # We encode that the component's callback can be executed only
            # when the component is active
            block_lifecycle_msg = TRUE_PYSMT()
            for msg_key in c.get_lifecycle_msgs():
                msg_label = self._get_msg_label(msg_key)
                block_msg = Not(msg_label)
                block_lifecycle_msg = And(block_lifecycle_msg, block_msg)
            fc_ts = And(fc_ts, block_lifecycle_msg)

            # The automaton moves only when the flag is true
            lc_info.ts.trans = And(Implies(flag, lc_info.ts.trans),
                                   Implies(Not(flag), fc_ts))
            # Product with the scheduler
            ts_sched.product(lc_info.ts)

        # 4. Encode when the activity lifecycle and a fragment
        #    can be interrupted and resumed
        for c in self.fd_builder.get_components():
            flag = comp2actflags[c]
            if (isinstance(c, Activity)):
                lc_info = lifecycles[c]

                pc_init = lc_info.get_label(FlowDroidEncoder.ActivityLcInfo.INIT)
                pc_init_next = self._get_next_formula(ts_sched.state_vars,
                                                      pc_init)
                pc_before_onstart = lc_info.get_label(FlowDroidEncoder.ActivityLcInfo.BEFORE_ONSTART)
                pc_before_onstart_next = self._get_next_formula(ts_sched.state_vars,
                                                                pc_before_onstart)
                activity_act = And(Not(flag),
                                   self._get_next_formula(ts_sched.state_vars,
                                                          flag))
                activity_deact = And(flag,
                                     Not(self._get_next_formula(ts_sched.state_vars,
                                                                flag)))

                atleastone_frag_act_next = self._at_least_one_frag_activates(c, comp2actflags,
                                                                             ts_sched.state_vars)

                # An activity can be de-activated (preemption) if either:
                #
                # - it is in the initial state
                # - the next flag is are the "free to run callbacks"
                # - Must be before onstart, and one of its fragment must be
                #   activated next
                activity_deact_enc = Implies(activity_deact,
                                             Or(Or(pc_init_next,
                                                   self._get_next_formula(ts_sched.state_vars,
                                                                          run_free_msg_flag)),
                                                And(pc_before_onstart_next,
                                                    atleastone_frag_act_next)))

                # An activity can be activated (pre-empt) another activity
                # if all other activities are in the initial state state
                # (this means their fragment are inactive) and if all its
                # fragment are in an initial state.
                #
                # In this way, an activity that has been pre-empted by
                # a random callback while in a non-initial state will always
                # get back control (the invariant that other activities are
                # in the initial state holds).
                #
                other_act_in_init = self._other_activities_in_init(c, lifecycles)
                other_act_in_init_next = self._get_next_formula(ts_sched.state_vars,
                                                                other_act_in_init)
                child_fragments_in_init = self._child_fragment_in_init(c, lifecycles)
                child_fragments_in_init_next = self._get_next_formula(ts_sched.state_vars,
                                                                      child_fragments_in_init)
                activity_act_enc = Implies(activity_act,
                                           And(other_act_in_init_next,
                                               child_fragments_in_init_next))
                activity_sched = And(activity_deact_enc, activity_act_enc)
                ts_sched.trans = And(ts_sched.trans, activity_sched)

                for fragment in c.get_child_fragments():
                    parent_act = c
                    frag_flag = comp2actflags[fragment]
                    frag_lc_info = lifecycles[fragment]
                    frag_pc_init = frag_lc_info.get_label(FlowDroidEncoder.FragmentLcInfo.INIT)
                    frag_pc_init_next = self._get_next_formula(ts_sched.state_vars,
                                                               frag_pc_init)
                    fragment_act = And(Not(frag_flag),
                                       self._get_next_formula(ts_sched.state_vars,
                                                              frag_flag))
                    fragment_deact = And(frag_flag,
                                         Not(self._get_next_formula(ts_sched.state_vars,
                                                                    frag_flag)))

                    frag_pc_init = frag_lc_info.get_label(FlowDroidEncoder.FragmentLcInfo.INIT)
                    frag_pc_init_next = self._get_next_formula(ts_sched.state_vars,
                                                               frag_pc_init)

                    # preempt fragment either if:
                    # - we will execute a non-controlled callback
                    # - the fragment gets in its initial state
                    fragment_deact_enc = Implies(fragment_deact,
                                                 Or(self._get_next_formula(ts_sched.state_vars,
                                                                           run_free_msg_flag),
                                                    frag_pc_init_next))

                    # Activate the fragment only if
                    # - its activity will be in the right state
                    # - all the other children fragments are in their initial state
                    # - all the other activities are in their initial state
                    act_pc_run_frag = lc_info.get_label(FlowDroidEncoder.ActivityLcInfo.BEFORE_ONSTART)
                    act_pc_run_frag_next = self._get_next_formula(ts_sched.state_vars,
                                                                  act_pc_run_frag)

                    other_fragment_in_init = self._other_fragments_in_init(c, fragment, lifecycles)
                    other_fragment_in_init_next = self._get_next_formula(ts_sched.state_vars,
                                                                         other_fragment_in_init)
                    fragment_act_enc = Implies(fragment_act,
                                               And(act_pc_run_frag_next,
                                                   other_act_in_init_next,
                                                   other_fragment_in_init_next))

                    fragment_sched = And(fragment_act_enc, fragment_deact_enc)
                    ts_sched.trans = And(ts_sched.trans, fragment_sched)
            elif (isinstance(c, Fragment)):
                # Already encoded with activity
                pass
            else:
                raise Exception("Unknown component")

        # Encode the execution of the non lifecycle cb
        cb_msg_enc = self._encode_free_messages()
        callback_enc = And(Implies(run_free_msg_flag, cb_msg_enc),
                           Implies(Not(run_free_msg_flag), Not(cb_msg_enc)))
        ts_sched.trans = And(ts_sched.trans, callback_enc)

        # Enforce that at most one component is active
        set_flags = set()
        for flag in comp2actflags.values():
            set_flags.add(flag)
        set_flags.add(run_free_msg_flag)
        at_most_one = ExactlyOne(set_flags)
        ts_sched.trans = And(ts_sched.trans,
                             And(at_most_one,
                                 self._get_next_formula(ts_sched.state_vars,
                                                        at_most_one)))
        return ts_sched

    def _other_activities_in_init(self, activity, lifecycles):
        """ True if all activities are in init state """
        others_in_init = TRUE_PYSMT()
        for c in self.fd_builder.get_components():
            if c == activity:
                continue
            if (not isinstance(c, Activity)):
                continue

            lc_info = lifecycles[c]
            pc_init = lc_info.get_label(FlowDroidEncoder.ActivityLcInfo.INIT)
            others_in_init = And(others_in_init, pc_init)
        return others_in_init

    def _other_fragments_in_init(self, activity, my_fragment, lifecycles):
        """ True if all child fragments are in init state """
        fragments_in_init = TRUE_PYSMT()
        for fragment in activity.get_child_fragments():
            if (not my_fragment is None) and my_fragment == fragment:
                continue

            lc_info = lifecycles[fragment]
            pc_init = lc_info.get_label(FlowDroidEncoder.FragmentLcInfo.INIT)
            fragments_in_init = And(fragments_in_init, pc_init)
        return fragments_in_init

    def _child_fragment_in_init(self, activity, lifecycles):
        """ True if all child fragments are in init state """
        return self._other_fragments_in_init(activity, None, lifecycles)

    def _at_least_one_frag_activates(self, activity, comp2actflags, state_vars):
        """ True if at least one of the child fragments activate 
        in the next state"""
        atleastone_frag_act = FALSE_PYSMT()
        for fragment in activity.get_child_fragments():
            flag_frag = comp2actflags[fragment]

            frag_act = And(Not(flag_frag),
                           self._get_next_formula(state_vars,
                                                  flag_frag))
            atleastone_frag_act = Or(atleastone_frag_act,
                                     frag_act)
        return atleastone_frag_act


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
            cb_msgs = component.get_trace_msgs(component_callback)

            if len(cb_msgs) > 0:
                has_callback = True
                current_pc_val_enc = self._eq_val(pc, pc_val)
                pc_val = next_pc_val
                next_pc_val_enc = self._eq_val(pc, next_pc_val)
                next_pc_val_enc = self._get_next_formula(ts.state_vars,
                                                         next_pc_val_enc)

                all_cb_msg_enc = FALSE_PYSMT()
                for cb_msg in cb_msgs:
                    cb_msg_enc = self._get_msg_label(cb_msg)
                    all_msg_enc = Or(all_cb_msg_enc, cb_msg_enc)

                # Move from pc to pc + 1 by observing at least one of the
                # callback
                single_trans = And(all_msg_enc, And(current_pc_val_enc, next_pc_val_enc))

                ts.trans = Or(ts.trans, single_trans)
                if at_least_one:
                    # Add a self loop on current_pc_val
                    # It allows to non-determinitically visit more than once
                    # the same set of callbacks
                    self_loop = self._get_next_formula(ts.state_vars,
                                                       current_pc_val_enc)
                    single_trans = And(all_msg_enc,
                                       And(current_pc_val_enc, self_loop))
                    ts.trans = Or(ts.trans, single_trans)

        # Block the execution in this state if the call is not
        # optional
        if not has_callback:
            if not optional:
                # the ts cannot move in pc_val right now, so there
                # is a deadlock
                current_pc_val_enc = self._eq_val(pc, pc_val)

                # Do nothing - the automaton does not move

                # advance the pc, so that we keep to encode the rest
                # of the lifecycle as it is.
                # while there is a deadlock in the current pc_val
                pc_val += 1

                logging.debug("Lifecycle callback not found for:\n" \
                              "\tComponent: %s\n" \
                              "\tCallback: %s\n" % (component_callback,
                                                    component.get_inst_value().get_value()))

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

    class LcInfo(object):
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
            FlowDroidEncoder.LcInfo.__init__(self, ts, pc, pc_size)

    class FragmentLcInfo(LcInfo):
        INIT = "init"
        END = "end"

        def __init__(self, ts, pc, pc_size):
            FlowDroidEncoder.LcInfo.__init__(self, ts, pc, pc_size)
