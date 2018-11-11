"""
--------------------------------------------------------------------------------
Helper class that builds the FlowDroid model.

The helper builds the relations among different objects and determines
when a callback can be executed inside a particular component's
lifecycle.

We follow the description in Section 3 "Precise Modeling of Lifecycle" of:
'FlowDroid: Precise Context, Flow, Field, Object-sensitive
and Lifecycle-aware Taint Analysis for Android Apps',
Artz et al, PLDI 14

We follow the source code of flowdroid in the repo
secure-software-engineering/FlowDroid,
commit a1438c2b38a6ba453b91e38b2f7927b6670a2702.


The code in FlowDroid that implements the model is mainly in the files:
soot-infoflow-android/src/soot/jimple/infoflow/android/SetupApplication.java
and
soot-infoflow-android/src/soot/jimple/infoflow/android/callbacks/AbstractCallbackAnalyzer.java

The lifecycle constraints (which are encoded in the encoder) are in the file:
soot-infoflow/src/soot/jimple/infoflow/entryPointCreators/AndroidEntryPointCreator.java


The construction of the FlowDroid model follows the following steps.

1. Builds the attachment relation.
   A pair (a,b) of objects from the trace is in the relation if
   a attach b (b is attached to a).

   The attachment relation is defined in the module
   cbverifier.encoding.model_properties.

   The attachment relation is build by FlowDroid looking at the XML
   file of the app and the call of some methods like findViewById.

   We ignore the XML related attachment relation.
   In the built model, we will let all the non-attached objects to execute
   their callbacks freely.

   We capture the "code" attachment instead, since we have the entire
   trace of the app. We use the methods such as findViewById and
   onAttachedFragment to reconstruct the attachment relation.

   Creates the self.attach_rel


2. Collects the set of messages that belongs to a listener object.
   The set of listener object classes and interfaces is defined
   in cbverifier.encoding.flowdroid_model.lifecycle_constants
   module.

   Creates self.listener2cb

3. Builds the registration relation for listeners.

   A pair (a,b) of objects from the trace is in the relation if
   a registers b as a listener (b is registered to a).

   FlowDroid over-approximate the registration relation looking at
   the XML file and the dynamic listener registration done
   calling the Android APIs.

   For the dynamic registration, the implementation of FlowDroid is mainly in
   the files:
   soot-infoflow-android/src/soot/jimple/infoflow/android/SetupApplication.java
   (line 476 (calculateCallbacks method))
   and
   soot-infoflow-android/src/soot/jimple/infoflow/android/callbacks/AbstractCallbackAnalyzer.java

   At line 182 of AbstractCallbackAnalyzer.java (method analyzeMethodForCallbackRegistrations)
   FlowDroid:
     - builds the the points-to relation and the call graph and from
       the lifecycle callbacks of each component
     - it visits each method called from the lifecycle callback to collect a
       set of concrete types that can be used as listener inside the
       component.
       A concrete type is considered if one of the object implementing
       it is used (overapprox. with the points-to set) as actual
       parameter of a formal parameter of listener type (one of the
       types such as OnClickListener defined by FlowDroid)
     - Finds and add the callbacks found in the implementation of the types
       found before (see line 261 and 547)
       The callbacks are all the methods that are concrete, non system
       class, not constructor or static (line 614).
     - The iteration of the model construction is handled in the
       calculateCallbacks method of SetupApplication

   We are agnostic of the listener registration through the XML
   (thus, the callbacks of a listener that is registered in the XML
   can happen at any point in time for us).

   We discover the dynamic registration as follows.
   If a method involving a listener object l is used in a *callback*
   of another object o (the receiver is o), then we add (o,l) to the
   registered relation.

   We discover the callbacks methods of the receiver as in step 2.

   We build the final relation "this activity can call a method from
   a listener" when computing the transitive closure in step 5.

   Creates self.reg_rel


4. Identifies the components (Activity and Fragment) existing in the
   trace and fills the activity/fragment parent/child relation.

   Creates: self.components, self.components_set


5. Builds the list of active callbacks for each activity as follows:

   For each activity visit transitively all the attached and registered
   objects.
   For all the objects, get the registered listener callbacks and add them
   to the set of active callbacks.

   Creates: self.act2active_callback

6. Build the set of constrained messages that are constrained by the lifecycle.
   The set of constrained message is the set of all messages minus:
     - the set of lifecycle messages by each activity
     - the set of lifecycle messages by fragments that are attached to
       the at least one activity.
     - the set of callbacks in the active part of each activity

   Creates: self.constrained_msgs

The encoding will use the set of callbacks that must be executed in the
active state of an activity, the activity/fragment parent child relation and
the set of all the free messages.

"""

import sys
import logging

from cbverifier.traces.ctrace import (
    CTrace, CCallback, CCallin, CValue, CTraceException
)
from cbverifier.encoding.flowdroid_model.lifecycle_constants import (
    Activity, Fragment, KnownAndroidListener
)
from cbverifier.specs.spec_ast import get_node_type, CALL_ENTRY, CALL_EXIT, ID
from cbverifier.encoding.grounding import bottom_value
from cbverifier.encoding.encoder_utils import EncoderUtils
from cbverifier.encoding.model_properties import (
    AttachRelation, RegistrationRelation, EmptyRelation
)
from cbverifier.utils.utils import is_debug


class FlowDroidModelBuilder:

    def __init__(self, trace, trace_map):
        """ Initialize the model builder taking as input an instance
        of the trace, trace map and a list of the existing messages
        """
        self.trace = trace
        self.trace_map = trace_map

        self.attach_rel = None
        self.listener2cb = None
        self.reg_rel = None

        self.components = None
        self.components_set = None

        self.act2active_callback = None
        self.constrained_msgs = None

        # Get all listeners and all the values
        all_values = self.trace.get_all_trace_values()

        # 1. Computes the attachment relation
        self.attach_rel = AttachRelation(self.trace_map,
                                         self.trace,
                                         all_values)

        # 2. Collects the set of callbacks for the listener objects
        self.listener2cb = FlowDroidModelBuilder._get_all_listeners(self.trace)

        # 3. Builds the registration relation for listeners
        self.reg_rel = EmptyRelation(self.trace_map, self.trace, all_values)
        FlowDroidModelBuilder._build_reg_rel(self.reg_rel,
                                             self.trace,
                                             self.listener2cb)

        # 4. Populate the map of all components from the trace
        res = FlowDroidModelBuilder._get_all_components(self.trace,
                                                        self.trace_map,
                                                        self.attach_rel)
        (self.components_set, self.components_map) = res

        # 5. Builds the list of active callbacks for each activity
        self.act2active_callback = self._compute_active_cb()

        # Compute the set of messages constrained by
        # the flowdroid model.
        # All the other messages will be free to move
        self.constrained_msgs = self._compute_const_msg()

        # print the model
        if (logging.getLogger().isEnabledFor(logging.INFO)):
            self.print_model(sys.stdout)

    def get_components(self):
        return list(self.components_set)

    def get_const_msgs(self):
        return self.constrained_msgs

    def get_comp_callbacks(self, component_object):
        if (component_object in self.act2active_callback):
            return self.act2active_callback[component_object]
        else:
            return set()

    def get_msg_properties(self, msg):
        """
        Returns the information about msg in the FlowDroid model

        It returns a tuple:
        (is_constrained, is_lifecycle, owner_activity, owner_fragment)

        where:
        - is_constrained is True iff msg is a controlled messages
        - is_lifecycle is True iff msg is a lifecycle message
        - owner_activities is the set of Activities owning the message
        - owner_fragments is the set of Fragments owning the message

        Warning: we assume fragments and activity lifecycle objects and
        methods to be dijoints
        """

        is_constrained = msg in self.get_const_msgs()
        is_lifecycle = False
        owner_activities = set()
        owner_fragments = set()

        for c in self.get_components():
            is_activity = isinstance(c, Activity)
            is_fragment = isinstance(c, Fragment)

            lc_msg = c.get_lifecycle_msgs()
            msg_in_c_lc = msg in lc_msg
            is_lifecycle = is_lifecycle or msg_in_c_lc

            if msg_in_c_lc:
                if is_activity:
                    owner_activities.add(c)
                elif is_fragment:
                    owner_fragments.add(c)
                    for parent in c.get_parent_activities():
                        owner_activities.add(parent)

            c_object = c.get_inst_value()
            if msg in self.get_comp_callbacks(c_object):
                assert is_activity
                owner_activities.add(c)

        return (is_constrained, is_lifecycle,
                owner_activities, owner_fragments)

    @staticmethod
    def _get_all_components(trace, trace_map, attach_rel):
        """ Populate the list of all components from the trace.

        Returns a pair (components, components_map),

        components is the set of all object components (i.e., the
        Activity and Fragment object declarede in the lifecycle_constants
        module)

        components_map is a map from the component object value to
        the component object
        """

        components = set()
        components_map = {}

        trace_stack = []
        for msg in trace.children:
            trace_stack.append(msg)

        # Finds all the components in the trace
        while (0 != len(trace_stack)):
            msg = trace_stack.pop()
            # Collect the list of compnents
            for value in msg.params:
                if value in components_map:
                    continue

                is_act = trace._is_in_class_names(Activity.class_names, value)
                is_frag = trace._is_in_class_names(Fragment.class_names, value)
                if ( is_act and is_frag):
                    logging.warning("Object %s is both an activity and " \
                                    "a fragment" % (value.get_value()))
                    assert False

                if is_act:
                    act_types = trace._get_class_names(Activity.class_names,
                                                       value)
                    assert len(act_types) != 0
                    component = Activity(act_types, value, trace_map)
                    components.add(component)
                    components_map[value] = component

                if is_frag:
                    frag_types = trace._get_class_names(Fragment.class_names,
                                                        value)
                    assert len(frag_types) != 0
                    component = Fragment(frag_types, value, trace_map)
                    components.add(component)
                    components_map[value] = component

            for child in msg.children:
                trace_stack.append(child)
        # end of while loop

        FlowDroidModelBuilder._link_act_to_frag(components,
                                                components_map,
                                                attach_rel)

        return (components, components_map)

    @staticmethod
    def _link_act_to_frag(components_set,
                          components_map,
                          attach_rel):
        """ Fill the parent activities for fragments
        """
        for activity in components_set:
            if (not isinstance(activity, Activity)):
                continue

            visited = set()
            stack = [activity.get_inst_value()]
            while (len(stack) > 0):
                c_id = stack.pop()
                if (c_id in visited):
                    continue
                visited.add(c_id)

                for attached_obj in attach_rel.get_related(c_id):
                    if attached_obj in components_map:
                        fragment = components_map[attached_obj]
                        if isinstance(fragment, Fragment):
                            activity.add_child_fragment(fragment)
                            fragment.add_parent_activity(activity)
                    stack.append(attached_obj)

    @staticmethod
    def _get_all_listeners(trace):
        """
        Scan the trace and get all the callback entry messages
        that are defined in a listener class.

        These messages are the possible listener objects we seen in the
        trace.

        Return a map from listener object to its set of callbacks.
        """
        listener2cb = {}

        msg_stack = [cb_trace for cb_trace in trace.children]
        while (0 < len(msg_stack)):
            current = msg_stack.pop()

            rec = current.get_receiver()
            if ((not rec is None) and
                isinstance(current, CCallback) and
                trace._is_in_class_msg(KnownAndroidListener.listener_classes,
                                       current)):

                # The messages is a method declared in one
                # of the listener classes defined by flowdroid
                msg_key = EncoderUtils.get_key_from_msg(current,
                                                        EncoderUtils.ENTRY)
                if (not rec in listener2cb):
                    listener2cb[rec] = set()
                listener2cb[rec].add(msg_key)

            for c in current.children:
                msg_stack.append(c)

        return listener2cb

    @staticmethod
    def _build_reg_rel(reg_rel, trace, listener2cb):
        """
        A pair (a,b) of objects from the trace is in the relation if
        a registers b as a listener (b is registered to a).

        If a method involving a listener object l is used in a *callback*
        of another object o (the receiver is o), then we add (o,l) to the
        registered relation.
        """

        def _add_relations(reg_rel, cb_receivers, listener):
            for rec in cb_receivers:
                reg_rel.add_relation(rec, listener)

        def _br_rec(trace_msg, cb_receivers, reg_rel):
            if (isinstance(trace_msg, CCallback) and
                not trace_msg.get_receiver() is None):
                cb_receivers = list(cb_receivers)
                cb_receivers.append(trace_msg.get_receiver())

            for child in trace_msg.children:
                # Add the object to the relation, if that's the case
                for par in child.get_other_params():
                    if (par in listener2cb):
                        _add_relations(reg_rel, cb_receivers, par)

                # Process children -- not tail recursive, not efficient
                _br_rec(child, cb_receivers, reg_rel)

        for trace_msg in trace.children:
            _br_rec(trace_msg, [], reg_rel)


    def _compute_active_cb(self):
        """
        For each activity visits transitively all the attached and registered
        objects.

        For all the objects, get the registered listener callbacks and add them
        to the set of active callbacks.
        """
        act2active_callback = {}

        for act in self.get_components():
            if not isinstance(act, Activity):
                continue

            act_object = act.get_inst_value()

            assert act_object not in act2active_callback
            active_callback = set()
            act2active_callback[act_object] = active_callback

            stack = [act_object]
            visited = set()
            while (len(stack) > 0):
                current_obj = stack.pop()
                if (current_obj in visited):
                    continue
                else:
                    visited.add(current_obj)

                # Add the callbacks of the listener
                if (current_obj in self.listener2cb):
                    active_callback.update(self.listener2cb[current_obj])

                # Reachability on the attachment relation
                for attached_obj in self.attach_rel.get_related(current_obj):
                    stack.append(attached_obj)

                # Reachability on the registration relation
                for reg_obj in self.reg_rel.get_related(current_obj):
                    stack.append(reg_obj)

        return act2active_callback

    def _compute_const_msg(self):
        """
        Compute the set of constrained messages:

        The set of constrained message is the set of all messages minus:
        - the set of lifecycle messages by each activity
        - the set of lifecycle messages by fragments that are attached to
        the at least one activity.
        - the set of callbacks in the active part of each activity
        """

        const_msg = set()

        for c in self.get_components():
            # add the activity lifecycle messages
            if isinstance(c, Activity):
                const_msg.update(c.get_lifecycle_msgs())
            # add the fragment lifecycle messages,
            # if the fragment is attached to some activity
            if (isinstance(c, Fragment) and
                0 < len(c.get_parent_activities())):
                const_msg.update(c.get_lifecycle_msgs())

        # Add the set of callbacks in the active part of each activity
        for (act, msg_list) in self.act2active_callback.iteritems():
            const_msg.update(msg_list)

        return const_msg

    def print_model(self, stream):
        """ Prints a summary of the flowdroid model """

        def _print_comp(comp, stream):
            comp_type = "Activity" if isinstance(c, Activity) else "Fragment"
            comp_obj = c.get_inst_value()
            comp_value = comp_obj.get_value()
            stream.write("%s: %s\n" % (comp_type, str(comp_value)))

        def _print_sep(stream):
            for i in range(80): stream.write("-")
            stream.write("\n")

        stream.write("\n--- Flowdroid model summary ---\n")

        count_activities = 0
        count_fragments = 0

        for c in self.components_set:
            if isinstance(c, Activity):
                count_activities += 1
            if isinstance(c, Fragment):
                count_fragments += 1

        stream.write("--- Activities: %d\n" \
                     "--- Fragments: %d\n" \
                     "--- Constrained msgs: %d\n" % (count_activities,
                                                     count_fragments,
                                                     len(self.constrained_msgs)))

        for c in self.components_set:
            # type, object id
            _print_sep(stream)
            _print_comp(c, stream)

            # For all activities
            if isinstance(c, Activity):
                # attached fragments
                stream.write("Attached fragments:")
                for frag in c.get_child_fragments():
                    stream.write(" %s" % frag.get_inst_value().get_value())
                stream.write("\n")

            # list of lifecycle methods
            lc_msgs = c.get_lifecycle_msgs()
            stream.write("Lifecycle msg (%d):\n" % len(lc_msgs))
            for msg_key in lc_msgs:
                stream.write(" %s\n" % msg_key)

            if isinstance(c, Activity):
                # list of controlled callbacks
                # --- TODO: fix code duplication with encoder.py,
                #           _encode_non_lc_callback
                #           Not refactored to not introduce regression now
                stream.write("Messages in component:\n")
                # collect controlled cb
                c_id = c.get_inst_value()
                if c_id in self.act2active_callback:
                    cb_star = self.act2active_callback[c_id]
                    for msg_key in cb_star:
                        if "<init>" in msg_key:
                            continue
                        stream.write(" %s\n" % msg_key)
            _print_sep(stream)

        stream.write("--- Constrained messages ---\n")
        for msg_key in self.constrained_msgs:
            stream.write(" %s\n" % msg_key)
        _print_sep(stream)
        stream.flush()
