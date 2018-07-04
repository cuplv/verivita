"""
--------------------------------------------------------------------------------
Helper class that builds the FlowDroid model.

We follow the description in Section 3 "Precise Modeling of Lifecycle" of:
'FlowDroid: Precise Context, Flow, Field, Object-sensitive
and Lifecycle-aware Taint Analysis for Android Apps',
Artz et al, PLDI 14

and in particular the implementation in:
soot-infoflow/src/soot/jimple/infoflow/entryPointCreators/
AndroidEntryPointCreator.java
in the repo secure-software-engineering/FlowDroid,
commit a1438c2b38a6ba453b91e38b2f7927b6670a2702.

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
inside their activity component.
"""

from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue, CTraceException
from cbverifier.encoding.flowdroid_model.lifecycle_constants import Activity, Fragment
from cbverifier.specs.spec_ast import get_node_type, CALL_ENTRY, CALL_EXIT, ID
from cbverifier.encoding.grounding import bottom_value
from cbverifier.encoding.encoder_utils import EncoderUtils
from cbverifier.encoding.model_properties import AttachRelation, RegistrationRelation

class FlowDroidModelBuilder:

    def __init__(self, trace, trace_map, spec_msgs_keys):
        """ Initialize the model builder taking as input an instance
        of the ts_encoder (to use traces, other encoders...).
        """
        self.trace = trace
        self.trace_map = trace_map

        # Populate the map of all components from the trace
        self.components_set = set([])
        FlowDroidModelBuilder._get_all_components(self.trace,
                                                  self.components_set,
                                                  self.trace_map)

        # map from component address to its representation
        self.components_map = {}
        for c in self.components_set:
            self.components_map[c.get_inst_value()] = c

        # root_components_ids = []
        # for c in self.components_set:
        #     if isinstance(c, Activity):
        #         root_components_ids.append(c.get_inst_value())

        all_values = FlowDroidModelBuilder._get_all_values(self.trace)
        self.attach_rel = AttachRelation(self.trace_map,
                                         all_values)
        self.register_rel = RegistrationRelation(self.trace_map,
                                                 all_values)

        print self.attach_rel.relation

        # Map from object id to messages where the id is used as a receiver
        self.obj2msg_keys = FlowDroidModelBuilder._get_obj2msg_keys(self.trace)

        # set up all messages -- all messages narrowed down from the specs
        # and all the messages from the lifecycle
        self.msgs_keys = set(spec_msgs_keys)
        for c in self.components_set:
            c_msgs = c.get_lifecycle_msgs()
            for msg_key in c_msgs:
                self.msgs_keys.add(msg_key)

        # Computes where each message can be executed
        (compid2msg_keys, free_msg) = self._compute_msgs_boundaries()

        self.compid2msg_keys = compid2msg_keys
        self.free_msg = free_msg

    def get_msgs_keys(self):
        return self.msgs_keys

    @staticmethod
    def _get_all_components(trace, components, trace_map):
        """ Populate the list of all components from the trace.
        """
        trace_stack = []
        for msg in trace.children:
            trace_stack.append(msg)

        component_ids = set()

        # Finds all the components in the trace
        while (0 != len(trace_stack)):
            msg = trace_stack.pop()
            # Collect the list of compnents
            for value in msg.params:
                if value in component_ids:
                    continue

                if Activity.is_class(value.type):
                    component = Activity(value.type, value, trace_map)
                    components.add(component)
                    component_ids.add(value)

                if Fragment.is_class(value.type):
                    component = Fragment(value.type, value, trace_map)
                    components.add(component)
                    component_ids.add(value)

            for child in msg.children:
                trace_stack.append(child)

    def _compute_msgs_boundaries(self):
        """
        Determines where each message can be executed in the
        activity/fragment lifecycle
        """
        # Messages that can be executed everywhere in the lifecycle
        free_msg = set(self.msgs_keys)

        # Map from object id of a component to a set of messages that
        # can only be called inside that component lifecycle
        compid2msg_keys = {}

        visited_registered = set()
        visited_attached = set()

        # Loop on all the activities
        for c in self.components_set:
            if not isinstance(c, Activity):
                continue
            activity = c
            activity_obj = activity.get_inst_value()

            self._process_msgs_component(free_msg,
                                         compid2msg_keys,
                                         activity)

            # Process all the registered callbacks to the activity
            self._add_registered_msgs(compid2msg_keys,
                                      visited_registered,
                                      activity,
                                      (activity, activity_obj))

            # Process all the attached components
            self._add_attached_msgs(free_msg, compid2msg_keys,
                                    visited_attached,
                                    visited_registered,
                                    activity,
                                    (activity, activity_obj))

        return (compid2msg_keys, free_msg)


    def _add_registered_msgs(self,
                             compid2msg_keys,
                             visited_registered,
                             lifecycle_comp, parent_pair):
        (parent_comp, parent_obj) = parent_pair
        assert lifecycle_comp is not None
        assert parent_obj is not None
        lifecycle_obj = lifecycle_comp.get_inst_value()

        key = (lifecycle_obj, parent_obj)
        if key in visited_registered:
            return
        visited_registered.add(key)

        assert(lifecycle_obj in compid2msg_keys)
        lifecycle_comp_msgs_keys = compid2msg_keys[lifecycle_obj]

        # get all the msg keys registered to parent
        for registered_obj in self.register_rel.get_related(parent_obj):
            registered_msg_keys = self.obj2msg_keys(registered_obj)

            for msg_key in registered_msg_keys:
                lifecycle_comp_msgs_keys.add(msg_key)

            # TODO - check
            # Transitive closure on the registered relation
            self._add_registered_msgs(compid2msg_keys,
                                      visited_registered,
                                      lifecycle_comp,
                                      (None, registered_obj))


    def _add_attached_msgs(self, free_msg, compid2msg_keys,
                           visited_attached,
                           visited_registered,
                           lifecycle_comp, parent_pair):
        (parent_comp, parent_obj) = parent_pair
        assert lifecycle_comp is not None
        assert parent_obj is not None
        lifecycle_obj = lifecycle_comp.get_inst_value()

        key = (lifecycle_obj, parent_obj)
        if key in visited_attached:
            return
        visited_attached.add(key)

        for attached_obj in self.attach_rel.get_related(parent_obj):
            is_fragment = False
            fragment = None
            for attach_obj in self.components_map:
                fragment = self.components_map[attach_obj]
                is_fragment = isinstance(fragment, Fragment)

            if is_fragment:
                self._process_msgs_component(free_msg,
                                             compid2msg_keys,
                                             fragment)

                # Process all the registered callbacks to the activity
                self._add_registered_msgs(compid2msg_keys,
                                          visited_registered, fragment,
                                          (fragment, fragment.get_inst_value()))

                # Process all the attached components
                self._add_attached_msgs(free_msg, compid2msg_keys,
                                        visited_attached,
                                        visited_registered,
                                        fragment,
                                        (fragment, fragment.get_inst_value()))
            else:
                # The obj should have been visited before
                assert(lifecycle_obj in compid2msg_keys)
                lifecycle_comp_msgs_keys = compid2msg_keys[lifecycle_obj]
                attached_msg_keys = self.obj2msg_keys(attached_obj)

                for msg_key in attached_msg_keys:
                    lifecycle_comp_msgs_keys.add(msg_key)

                self._add_registered_msgs(compid2msg_keys,
                                          visited_registered,
                                          lifecycle_comp,
                                          (None, attached_obj))

                self._add_attached_msgs(free_msg, compid2msg_keys,
                                        visited_attached,
                                        visited_registered,
                                        lifecycle_comp,
                                        (None, attached_obj))

    def _process_msgs_component(self,
                                free_msg,
                                compid2msg_keys,
                                component):
        component_obj = component.get_inst_value()

        if (component_obj in compid2msg_keys):
            component_msg_keys = compid2msg_keys[component_obj]
        else:
            component_msg_keys = set()
            compid2msg_keys[component_obj] = component_msg_keys

        lifecycle_msg = component.get_lifecycle_msgs()
        # Removes the lifecycle messages
        for m in lifecycle_msg:
            if m in free_msg:
                free_msg.remove(m)
        # add all the non-lifecycle component messages
        for m in self.obj2msg_keys[component_obj]:
            if m not in lifecycle_msg:
                component_msg_keys.add(m)

    def get_components(self):
        return list(self.components_set)

    def encode(self):
        """ Create an encoding of the FlowDroid model
        """
        self._encode_lifecycle()
        self._encode_callbacks_in_lifecycle()

    def _encode_lifecycle(self):
        """ Encode the components' lifecylces

        For now we handle activities.
        """
        raise NotImplementedError("_encode_lifecycle not implemented")

    def _encode_callbacks_in_lifecycle(self):
        """ Encode the enabledness of the callbacks attached to
        Activities and Fragment
        """
        raise NotImplementedError("_encode_callbacks_in_lifecycle not implemented")

    @staticmethod
    def _get_all_values(trace):
        """
        Get all the objects used in the trace.
        """
        all_values = set()

        msg_stack = [child for child in trace.children]
        while (0 < len(msg_stack)):
            current = msg_stack.pop()

            rec = current.get_receiver()
            if rec is not None:
                all_values.add(rec)

            for par in current.get_other_params():
                all_values.add(par)

            for c in current.children:
                msg_stack.append(c)

        return all_values

    @staticmethod
    def _get_obj2msg_keys(trace):
        obj2msg = {}

        trace_stack = [child for child in trace.children]
        while (0 < len(trace_stack)):
            current = trace_stack.pop()

            rec = current.get_receiver()
            if rec is not None:
                if not rec in obj2msg:
                    obj2msg[rec] = set()

                msg_entry = EncoderUtils.get_key_from_msg(current, EncoderUtils.ENTRY)
                msg_exit = EncoderUtils.get_key_from_msg(current, EncoderUtils.EXIT)
                obj2msg[rec].add(msg_entry)
                obj2msg[rec].add(msg_exit)

            for c in current.children:
                trace_stack.append(c)

        return obj2msg
