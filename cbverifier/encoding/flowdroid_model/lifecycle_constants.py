""" Define the constants used to represent the lifecycle

Representation of the object (components) in the trace_map

Take the definition of lifecycle callbacks from Flowdroid:

soot-infoflow/src/soot/jimple/infoflow/entryPointCreators/
AndroidEntryPointtConstants.java
in the repo secure-software-engineering/FlowDroid,
commit a1438c2b38a6ba453b91e38b2f7927b6670a2702.

Differently from FlowDroid we manually encode the subclasses
of Activity and Fragment that we handle (we do not use the static
information extracted from the Android class hierarchy now,
but we already have the list from the lifestate specification
activity).
"""

import string
from cbverifier.specs.spec_parser import spec_parser
from cbverifier.specs.spec_ast import *
from cbverifier.encoding.grounding import TraceMap
from cbverifier.encoding.encoder_utils import EncoderUtils

def _substitute(template, substitution):
    return string.Template(template).safe_substitute(substitution)


class Component:
    def __init__(self, class_name, inst_value, trace_map, my_var_name, my_type_const):
        self.class_name = class_name
        self.inst_value = inst_value
        self.trace_map = trace_map
        self.my_var_name = my_var_name
        self.my_type_const = my_type_const
        self.methods_msgs = {}

        for (key, cb_names) in self.get_class_cb():
            for cb_name in cb_names:
                # parse the message
                cb_name_subs = _substitute(cb_name,
                                           {self.get_mytype_const() : class_name})
                call_ast = spec_parser.parse_call(cb_name_subs)

                if call_ast is None:
                    error_msg = "Error parsing the back message %s.\n\n" \
                                "The original template message was %s\n" \
                                "\tSubstitution: " \
                                "%s = %s\n\n" % (cb_name_subs, cb_name,
                                                 self.get_mytype_const(),
                                                 class_name)
                    raise Exception(error_msg)

                # filter the message for assignments such that
                # self.my_var_name is assigned to inst_value

                # find the methods
                my_var_name_ast = new_id(self.my_var_name)
                trace_msg_list = trace_map.find_methods(call_ast, {my_var_name_ast :
                                                                   self.get_inst_value()})

                call_type = get_node_type(call_ast)
                if (CALL_ENTRY == call_type):
                    call_type_enc = EncoderUtils.ENTRY
                elif (CALL_EXIT == call_type):
                    call_type_enc = EncoderUtils.EXIT
                else:
                    raise Exception("Unkonwn node " + str(call_ast))

                for m_trace in trace_msg_list:
                    msg = EncoderUtils.get_key_from_msg(m_trace, call_type_enc)
                    self.add_trace_msg(key, msg)

    def get_inst_value(self):
        return self.inst_value

    def get_my_var_name(self):
        return self.my_var_name

    def get_mytype_const(self):
        return self.my_type_const

    def get_class_names(self):
        raise NotImplementedError("Not implemented in base component")

    def get_class_cb(self):
        raise NotImplementedError("Not implemented in base component")

    def add_trace_msg(self, key, msg):
        if key not in self.methods_msgs:
            self.methods_msgs[key] = []
        self.methods_msgs[key].append(msg)

    def has_trace_msg(self, key):
        return key in self.methods_msgs

    def get_trace_msgs(self,key):
        assert key in self.methods_msgs
        return self.methods_msgs[key]

    def get_lifecycle_msgs(self):
        """ Returns the list of messages that are used
        to define the lifecycle of the activity
        """
        lc_msgs = set()
        for (_, msg_list) in self.methods_msgs.iteritems():
            for m in msg_list:
                lc_msgs.add(m)
        return lc_msgs


################################################################################
# Activity
class Activity(Component):
    class_names = ["android.app.Activity",
                   "android.accounts.AccountAuthenticatorActivity",
                   "android.support.v7.app.ActionBarActivity",
                   "android.app.ActivityGroup",
                   "android.app.AliasActivity",
                   "android.support.v7.app.AppCompatActivity",
                   "android.app.ExpandableListActivity",
                   "android.support.v4.app.FragmentActivity",
                   "android.app.LauncherActivity",
                   "android.app.ListActivity",
                   "android.preference.PreferenceActivity",
                   "android.app.TabActivity"]

    # Constants used to specify the activity lifecycle
    ONCREATE = "ACTIVITY_ONCREATE"
    ONCREATEDESCRIPTION = "ACTIVITY_ONCREATEDESCRIPTION"
    ONDESTROY = "ACTIVITY_ONDESTROY"
    ONPAUSE = "ACTIVITY_ONPAUSE"
    ONPOSTCREATE = "ACTIVITY_ONPOSTCREATE"
    ONPOSTRESUME = "ACTIVITY_ONPOSTRESUME"
    ONRESTART = "ACTIVITY_ONRESTART"
    ONRESUME = "ACTIVITY_ONRESUME"
    ONSAVEINSTANCESTATE = "ACTIVITY_ONSAVEINSTANCESTATE"
    ONSTART = "ACTIVITY_ONSTART"
    ONSTOP = "ACTIVITY_ONSTOP"
    ONRESTOREINSTANCESTATE = "ACTIVITY_ONRESTOREINSTANCESTATE"

    ONACTIVITYSTARTED = "ACTIVITY_ONACTIVITYSTARTED"
    ONACTIVITYSTOPPED = "ACTIVITY_ONACTIVITYSTOPPED"
    ONACTIVITYSAVEINSTANCESTATE = "ACTIVITY_ONACTIVITYSAVEINSTANCESTATE"
    ONACTIVITYRESUMED = "ACTIVITY_ONACTIVITYRESUMED"
    ONACTIVITYPAUSED = "ACTIVITY_ONACTIVITYPAUSED"
    ONACTIVITYDESTROYED = "ACTIVITY_ONACTIVITYDESTROYED"
    ONACTIVITYCREATED = "ACTIVITY_ONACTIVITYCREATED"

    @staticmethod
    def is_class(class_name):
        return class_name in Activity.class_names

    def get_class_names(self):
        return Activity.class_names

    def get_class_cb(self):
        """ Defines the method signatures of the Activity
        lifecycle methods.

        We use the specification language to pattern match the method
        in the trace, also matching the parameter names.
        """

        # From activityMethods in AndroidEntryPointtConstants.java:117 and
        # list at line 39
        cb_to_find = [(Activity.ONCREATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onCreate(f : android.os.Bundle)"]),
                      (Activity.ONCREATEDESCRIPTION, ["[CB] [ENTRY] [L] java.lang.CharSequence ${MYTYPE}.onCreateDescription()"]),
                      (Activity.ONDESTROY, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDestroy()"]),
                      (Activity.ONPAUSE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPause()"]),
                      (Activity.ONPOSTCREATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPostCreate(f : android.os.Bundle)"]),
                      (Activity.ONPOSTRESUME, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPostResume()"]),
                      (Activity.ONRESTART, ["[CB] [ENTRY] [L] void ${MYTYPE}.onRestart()"]),
                      (Activity.ONRESUME, ["[CB] [ENTRY] [L] void ${MYTYPE}.onResume()"]),
                      (Activity.ONSAVEINSTANCESTATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onSaveInstanceState(f : android.os.Bundle)"]),
                      (Activity.ONSTART, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStart()"]),
                      (Activity.ONSTOP, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStop()"]),
                      (Activity.ONRESTOREINSTANCESTATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onRestoreInstanceState(f : android.os.Bundle)"]),
                      #
                      (Activity.ONACTIVITYSTARTED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityStarted(L : ${MYTYPE})"]),
                      (Activity.ONACTIVITYSTOPPED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityStopped(L : ${MYTYPE})"]),
                      (Activity.ONACTIVITYSAVEINSTANCESTATE, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivitySaveInstanceState(L : ${MYTYPE}, f : android.os.Bundle)"]),
                      (Activity.ONACTIVITYRESUMED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityResumed(L : ${MYTYPE})"]),
                      (Activity.ONACTIVITYPAUSED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityPaused(L : ${MYTYPE})"]),
                      (Activity.ONACTIVITYDESTROYED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityDestroyed(L : ${MYTYPE})"]),
                      (Activity.ONACTIVITYCREATED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityCreated(L : ${MYTYPE}, f : android.os.Bundle)"])
        ]

        # Activity.ONATTACHFRAGMENT = "[CB] [ENTRY] [L] void ${MYTYPE}.onAttachFragment(f : android.app.Fragment)"

        return cb_to_find

    def __init__(self, class_name, inst_value, trace_map):
        Component.__init__(self, class_name, inst_value, trace_map, "L", "MYTYPE")
        self._child_fragments = set()

    def add_child_fragment(self, fragment):
        self._child_fragments.add(fragment)

    def get_child_fragments(self):
        return self._child_fragments



class Fragment(Component):
    class_names = ["android.app.Fragment",
                   "android.support.v4.app.Fragment",
                   "android.support.v4.app.ListFragment",
                   "android.app.ListFragment",
                   "android.support.v4.app.DialogFragment",
                   "android.preference.PreferenceFragment",
                   "android.app.DialogFragment",
                   "android.webkit.WebViewFragment",
                   "android.support.v7.preference.PreferenceFragmentCompat"]

    ONCREATE = "FRAGMENT_ONCREATE"
    ONATTACH = "FRAGMENT_ONATTACH"
    ONCREATEVIEW = "FRAGMENT_ONCREATEVIEW"
    ONVIEWCREATED = "FRAGMENT_ONVIEWCREATED"
    ONSTART = "FRAGMENT_ONSTART"
    ONACTIVITYCREATED = "FRAGMENT_ONACTIVITYCREATED"
    ONVIEWSTATERESTORED = "FRAGMENT_ONVIEWSTATERESTORED"
    ONRESUME = "FRAGMENT_ONRESUME"
    ONPAUSE = "FRAGMENT_ONPAUSE"
    ONSTOP = "FRAGMENT_ONSTOP"
    ONDESTROYVIEW = "FRAGMENT_ONDESTROYVIEW"
    ONDESTROY = "FRAGMENT_ONDESTROY"
    ONDETACH = "FRAGMENT_ONDETACH"
    ONSAVEINSTANCESTATE = "FRAGMENT_ONSAVEINSTANCESTATE"
    ONATTACHFRAGMENT = "ACTIVITY_ONATTACHFRAGMENT"

    @staticmethod
    def is_class(class_name):
        return class_name in Fragment.class_names

    def get_class_names(self):
        return Fragment.class_names

    def __init__(self, class_name, inst_value, trace_map):
        Component.__init__(self, class_name, inst_value, trace_map, "L", "MYTYPE")
        self._parent_activities = set()

    def get_class_cb(self):
        cb_to_find = [(Fragment.ONCREATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onCreate(f : android.os.Bundle)"]),
                      (Fragment.ONATTACH, ["[CB] [ENTRY] [L] void ${MYTYPE}.onAttach(f : android.app.Activity)"]),
                      (Fragment.ONCREATEVIEW, ["[CB] [ENTRY] [L] android.view.View ${MYTYPE}.onCreateView(f1 : android.view.LayoutInflater, f2 : android.view.ViewGroup, f3 : android.os.Bundle)"]),
                      (Fragment.ONVIEWCREATED, ["[CB] [ENTRY] [L] void ${MYTYPE}.onViewCreated(f1 : android.view.View, f2 : android.os.Bundle)"]),
                      (Fragment.ONSTART, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStart()"]),
                      (Fragment.ONACTIVITYCREATED, ["[CB] [ENTRY] [L] void ${MYTYPE}.onActivityCreated(f : android.os.Bundle)"]),
                      (Fragment.ONVIEWSTATERESTORED, ["[CB] [ENTRY] [L] void ${MYTYPE}.onViewStateRestored(f : android.app.Activity)"]),
                      (Fragment.ONRESUME, ["[CB] [ENTRY] [L] void ${MYTYPE}.onResume()"]),
                      (Fragment.ONPAUSE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPause()"]),
                      (Fragment.ONSTOP, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStop()"]),
                      (Fragment.ONDESTROYVIEW, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDestroyView()"]),
                      (Fragment.ONDESTROY, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDestroy()"]),
                      (Fragment.ONDETACH, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDetach()"]),
                      (Fragment.ONSAVEINSTANCESTATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onSaveInstanceState(f : android.os.Bundle)"]),
                      (Fragment.ONATTACHFRAGMENT, ["[CB] [ENTRY] [f] void android.app.Activity.onAttachFragment(L : ${MYTYPE})"])]

                      # (Fragment.ONATTACHFRAGMENT,
                      #  [_substitute("[CB] [ENTRY] [f] void ${activity_class}.onAttachFragment(L : ${MYTYPE})",
                      #               ("activity_class" : activity_class)) for activity_class in Activity.class_names])

        return cb_to_find

    def add_parent_activity(self, activity):
        """ Add one activity that attach the fragment (or
        a fragment that attach the fragment) """
        self._parent_activities.add(activity)

    def get_parent_activities(self):
        return self._parent_activities



