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
that contains them is active. We compute an over-approximation of the
containment of components from the trace.

We model the lifecycle for activity and fragment components since we
are interested in components that run in the UI thread.

As done in flowdroid, we encode the lifecycle component of fragment
inside their activity component.

"""

from cbverifier.traces.ctrace import CTrace, CCallback, CCallin, CValue, CTraceException
from cbverifier.encoding.flowdroid_model.lifecycle_constants import Activity, Fragment
from cbverifier.specs.spec_ast import get_node_type, CALL_ENTRY, CALL_EXIT, ID
from cbverifier.encoding.grounding import bottom_value

class FlowDroidModelBuilder:

    def __init__(self, ts_encoder):
        """ Initialize the model builder taking as input an instance
        of the ts_encoder (to use traces, other encoders...).
        """
        self.ts_encoder = ts_encoder

        # Populate the set of all components from the trace
        # and the map of existing top-level callbacks for every receiver
        self.components_set = set([])
        FlowDroidModelBuilder._get_all_components(self.ts_encoder.trace,
                                                  self.ts_encoder.gs.trace_map,
                                                  self.components_set)

        # map from activity to a list of contained objects
        self.activity2contained = {}

        # map from an object to one of its back messages
        self.obj2backmsg = {}

        # List of messages used in the the model builder
        self.msgs = []

        return

        # Get an over-approximation of the objects that may
        # be attached to the activities/fragments
        self._get_attachment_overapprox()

        raise NotImplementedError("Initialization of the fd model")

    def get_calls(self):
        """ Get all the calls that are observed in the FlowDroid
        model.

        """
        raise NotImplementedError("get_calls not implemented")


    def get_components(self):
        return self.components_set

    @staticmethod
    def _get_all_components(trace, trace_map, components):
        """ Populate the list of all components from the trace.

        The components we are interested in are Activities
        """
        trace_stack = []
        for msg in trace.children:
            trace_stack.append(msg)

        # Finds all the components in the trace
        while (0 != len(trace_stack)):
            msg = trace_stack.pop()
            # Collect the list of compnents
            for value in msg.params:
                if Activity.is_class(value.type):
                    component = Activity(value.type, value)
                    components.add(component)
                if Fragment.is_class(value.type):
                    component = Fragment(value.type, value)
                    components.add(component)
            for child in msg.children:
                trace_stack.append(child)

        # Finds the lifecycle methods for each component
        for component in components:
            for (key, _) in component.get_class_cb():
                for call_ast in component.get_methods_names(key):
                    # find the concrete methods in the trace for the correct
                    # method name

                    node_type = get_node_type(call_ast)
                    assert (node_type == CALL_ENTRY or node_type == CALL_EXIT)
                    asets = trace_map.lookup_assignments(call_ast)

                    # convert the values to concrete calls and then to messages
                    for aset in asets:
                        for (fvar, fval) in aset.assignments.iteritems():
                            if (fval == bottom_value or
                                get_node_type(fvar) == ID):
                                continue
                            elif (type(fvar) == tuple):
                                if fval != bottom_value:
                                    # fval is the mapback to the trace message
                                    assert fval is not None
                                    assert (isinstance(fval, CCallin) or
                                            isinstance(fval, CCallback))
                                    component.add_trace_msg(key, fval)


    def _get_attachment_overapprox(self):
        """ Computes an over-approximate relation of objects in the
        trace that can be attached.

        Compile a list of callbacks by active component.

        Assume no components are attached, then build an over-approximation of
        attachment using the method calls seen in the trace.
        This is similar to theFlowDroid heuristic.

        TODO: check if we see or miss the attachment in the XML.
        """
        raise NotImplementedError("_get_attachment_overapprox not implemented")


    def _get_registered_overapprox(self):
        """ Computes an over-approximate relation of the callback that can
        be registered at any point in time in the trace.

       TODO: check if we see or miss the registration in the XML.
        """
        raise NotImplementedError("_get_registered_overapprox not implemented")


    def encode(self):
        """ Create an encoding of the FlowDroid model
        """
        self._encode_lifecycle()
        self._encode_callbacks_in_lifecycle()

    def _encode_lifecycle(self):
        """ Encode the components' lifecylces

        For now we handle activities.
        """
        raise NotImplementedError("_get_attachment_overapprox not implemented")

    def _encode_callbacks_in_lifecycle(self):
        """ Encode the enabledness of the callbacks attached to
        Activities and Fragment
        """
        raise NotImplementedError("_get_attachment_overapprox not implemented")


class ObjectRepr:
    """ Construct a backward representation from the object in the
    trace to their messages to messages. """

