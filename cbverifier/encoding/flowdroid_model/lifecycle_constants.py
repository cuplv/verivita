""" Define the constants used to represent the lifecycle

Representation of the object (components) in the trace

"""


import string
from cbverifier.specs.spec_parser import spec_parser

def _substitute(template, substitution):
    return string.Template(template).safe_substitute(substitution)

class Component:
    def __init__(self, class_name, inst_value, my_var_name, my_type_const):
        self.class_name = class_name
        self.inst_value = inst_value
        self.my_var_name = my_var_name
        self.my_type_const = my_type_const
        self.methods_names = {}
        self.methods_msgs = {}

        for (key, cb_names) in self.get_class_cb():
            for cb_name in cb_names:
                # construct a well formed message
                inst_value_str = self.inst_value.get_value()
                cb_name_subs = _substitute(cb_name,
                                           {self.get_mytype_const() : class_name,
                                            self.get_my_var_name() : inst_value_str})
                # parse the message
                message = spec_parser.parse_call(cb_name_subs)

                if message is None:
                    error_msg = "Error parsing the back message %s.\n" \
                                "The original template message was %s with the " \
                                "following substitutsion:\n" \
                                "%s = %s\n" \
                                "%s = %s\n\n" % (cb_name_subs, cb_name,
                                                 self.get_mytype_const(),
                                                 class_name,
                                                 self.get_my_var_name(),
                                                 inst_value_str)
                    raise Exception(error_msg)

                self.add_method_names(key, message)

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

    def get_methods_names(self, key):
        return self.methods_names[key]

    def has_methods_names(self, key):
        return key in self.methods_names

    def add_method_names(self, key, cb):
        if not self.has_methods_names(key):
            self.methods_names[key] = [cb]
        else:
            self.methods_names[key].add(cb)

    def add_trace_msg(self, key, msg):
        assert self.has_methods_names(key)
        if key not in self.methods_msgs:
            self.methods_msgs[key] = []
        self.methods_msgs[key] = msg

    def has_trace_msg(self, key):
        return key in self.methods_msgs

    def get_trace_msgs(self,key):
        assert key in self.methods_msgs
        return self.methods_msgs[key]


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

    # Constants used to specify the lifecycle
    INIT = "INIT"
    ONCREATE = "ONCREATE"
    # ONRESUME = "ONRESUME"

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
        on_create_names = (Activity.ONCREATE, ["[CB] [ENTRY] [${l}] void ${MYTYPE}.onCreate(f : android.os.Bundle)"])
        cb_to_find = [(Activity.INIT, ["[CB] [ENTRY] [${l}] void ${MYTYPE}.<init>()"])]

        # TODO
        # , on_resume_names, on_pause_names,
        # on_stop_names, on_start_names, on_destroy_names, on_restart_names]

        return cb_to_find

    def __init__(self, class_name, inst_value):
        Component.__init__(self, class_name, inst_value, "l", "MYTYPE")


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

    INIT = "INIT"

    @staticmethod
    def is_class(class_name):
        return class_name in Fragment.class_names

    def get_class_names(self):
        return Fragment.class_names

    def __init__(self, class_name, inst_value):
        Component.__init__(self, class_name, inst_value, "l", "MYTYPE")

    def get_class_cb(self):
        cb_to_find = [(Fragment.INIT, ["[CB] [ENTRY] [${l}] void ${MYTYPE}.<init>()"])]
        return cb_to_find



    # TODO

# onStart","onResume", "onPause","onSaveInstanceState","onDestroy","onDetach",
#           "onCreateView","onViewCreated","onDestroyView", "<init>","onStop","onCreate","onAttach", "onActivityCreated", "isDetached", "isResumed"},

             # "android.support.v14.preference.EditTextPreferenceDialogFragment",
             # "android.support.v14.preference.ListPreferenceDialogFragment",
             # "android.support.v14.preference.MultiSelectListPreferenceDialogFragment",
             # "android.support.v14.preference.PreferenceDialogFragment",
             # "android.support.v17.leanback.app.BrandedFragment",
             # "android.support.v17.leanback.app.GuidedStepFragment",
             # "android.support.v17.leanback.app.HeadersFragment",
             # "android.support.v17.preference.LeanbackPreferenceDialogFragment",
             # "android.support.v17.preference.LeanbackSettingsFragment",
             # "android.support.v17.leanback.app.OnboardingFragment",
             # "android.support.v17.leanback.app.PlaybackFragment",
             # "android.support.v17.leanback.app.RowsFragment",
             # "android.support.v17.leanback.app.SearchFragment",
             # "android.support.v17.preference.BaseLeanbackPreferenceFragment",
             # "android.support.v17.leanback.app.BrowseFragment",
             # "android.support.v17.leanback.app.DetailsFragment",
             # "android.support.v17.leanback.app.ErrorFragment",
             # "android.support.v17.preference.LeanbackListPreferenceDialogFragment",
             # "android.support.v17.preference.LeanbackPreferenceFragment",
             # "android.support.v17.leanback.app.PlaybackOverlayFragment",
             # "android.support.v17.leanback.app.VerticalGridFragment",
             # "android.support.v17.leanback.app.VideoFragment"


