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

class FlowDroidModelBuidler:

    def __init__(self, ts_encoder):
        """ Initialize the model builder taking as input an instance
        of the ts_encoder (to use traces, other encoders...).
        """
        self.ts_encoder = ts_encoder
        self.trace = ts_encoder.trace

        self.components_list = []    # list of components
        # map from activity to a list of contained objects
        self.activity2contained = {}

        # map from an object to one of its back messages
        self._obj2backmsg = {}
        # List of messages used in the the model builder
        self._msgs = []

        # Populate the list of all components from the trace
        self._get_all_components()
        # Get an over-approximation of the objects that may
        # be attached to the activities/fragments
        self._get_attachment_overapprox()


        raise NotImplementedError("Initialization of the fd model")

    def get_calls(self):
        """ Get all the calls that are observed in the FlowDroid
        model.

        """
        raise NotImplementedError("get_calls not implemented")

    def _get_all_components(self):
        """ Populate the list of all components from the trace.

        The components we are interested in are Activities
        """
        raise NotImplementedError("get_calls not implemented")

    def _get_attachment_overapprox(self):
        """ Computes an over-approximate relation of objects in the
        trace that can be contained in other objects

        Compile a list of callbakcs by active component
        """

        raise NotImplementedError("_get_attachment_overapprox not implemented")

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
