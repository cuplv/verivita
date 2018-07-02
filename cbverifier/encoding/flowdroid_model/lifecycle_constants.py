""" Define the constants used to represent the lifecycle

Representation of the object (components) in the trace

"""


import string
def _substitute(template, substitution):
    return string.Template(template).safe_substitute(substitution)


class Component:
    def __init__(self, class_name, my_type_const):
        self.class_name = class_name
        self.my_type_const = my_type_const
        self.methods_names = {}

        for (key, cb_names) in self.get_class_cb():
            for cb_name in cb_names:
                cb_name = _substitute(cb_name, {self.get_mytype_const() : class_name})
                self.add_method_names(key, cb_name)

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



################################################################################
# Activity
class Activity(Component):
    """ Represents an activity """

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

    INIT = "INIT"
    ONCREATE = "ONCREATE"
    # ONRESUME = "ONRESUME"

    @staticmethod
    def is_class_activity(class_name):
        return class_name in Activity.class_names

    def get_class_names(self):
        return Activity.class_names

    def get_class_cb(self):
        init_names = (Activity.INIT, ["[CB] [ENTRY] [l] ${MYTYPE} <init>()"])
        on_create_names = (Activity.ONCREATE, ["[CB] [ENTRY] [l] ${MYTYPE} onCreate()"])
        cb_to_find = [init_names, on_create_names]
                      # , on_resume_names, on_pause_names,
                      # on_stop_names, on_start_names, on_destroy_names, on_restart_names]
        return cb_to_find

    def __init__(self, class_name):
        Component.__init__(self, class_name, "MYTYPE")


class FragmentConst:
    class_names = []

    # TODO

# onStart","onResume", "onPause","onSaveInstanceState","onDestroy","onDetach",
#           "onCreateView","onViewCreated","onDestroyView", "<init>","onStop","onCreate","onAttach", "onActivityCreated", "isDetached", "isResumed"},
#             {"android.support.v4.app.Fragment", "android.support.v4.app.ListFragment","android.app.ListFragment",
#                "android.support.v4.app.DialogFragment","android.preference.PreferenceFragment",
#              "android.app.DialogFragment",
#              "android.webkit.WebViewFragment",
#              "android.support.v7.preference.PreferenceFragmentCompat"
#              # "android.support.v14.preference.EditTextPreferenceDialogFragment",
#              # "android.support.v14.preference.ListPreferenceDialogFragment",
#              # "android.support.v14.preference.MultiSelectListPreferenceDialogFragment",
#              # "android.support.v14.preference.PreferenceDialogFragment",
#              # "android.support.v17.leanback.app.BrandedFragment",
#              # "android.support.v17.leanback.app.GuidedStepFragment",
#              # "android.support.v17.leanback.app.HeadersFragment",
#              # "android.support.v17.preference.LeanbackPreferenceDialogFragment",
#              # "android.support.v17.preference.LeanbackSettingsFragment",
#              # "android.support.v17.leanback.app.OnboardingFragment",
#              # "android.support.v17.leanback.app.PlaybackFragment",
#              # "android.support.v17.leanback.app.RowsFragment",
#              # "android.support.v17.leanback.app.SearchFragment",
#              # "android.support.v17.preference.BaseLeanbackPreferenceFragment",
#              # "android.support.v17.leanback.app.BrowseFragment",
#              # "android.support.v17.leanback.app.DetailsFragment",
#              # "android.support.v17.leanback.app.ErrorFragment",
#              # "android.support.v17.preference.LeanbackListPreferenceDialogFragment",
#              # "android.support.v17.preference.LeanbackPreferenceFragment",
#              # "android.support.v17.leanback.app.PlaybackOverlayFragment",
#              # "android.support.v17.leanback.app.VerticalGridFragment",
#              # "android.support.v17.leanback.app.VideoFragment"


