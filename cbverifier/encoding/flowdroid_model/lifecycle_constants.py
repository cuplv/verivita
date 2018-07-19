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
from cbverifier.encoding.encoder_utils import EncoderUtils, Subs

def _substitute(template, substitution):
    return string.Template(template).safe_substitute(substitution)


class Component:
    def __init__(self, class_names, inst_value, trace_map, my_var_name,
                 my_type_const):
        self.class_names = class_names
        self.inst_value = inst_value
        self.trace_map = trace_map
        self.my_var_name = my_var_name
        self.my_type_const = my_type_const
        self.methods_msgs = {}

        for class_name in self.class_names:
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
    class_names = set(["android.app.Activity",
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
                       "android.app.TabActivity"])

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

    # From activityMethods in AndroidEntryPointtConstants.java:117 and
    # list at line 39
    cb_to_repl = [(ONCREATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onCreate(f : android.os.Bundle)"]),
                  (ONCREATEDESCRIPTION, ["[CB] [ENTRY] [L] java.lang.CharSequence ${MYTYPE}.onCreateDescription()"]),
                  (ONDESTROY, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDestroy()"]),
                  (ONPAUSE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPause()"]),
                  (ONPOSTCREATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPostCreate(f : android.os.Bundle)"]),
                  # FlowDroid misses
                  # onPostCreate(Bundle savedInstanceState, PersistableBundle persistentState)
                  (ONPOSTRESUME, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPostResume()"]),
                  (ONRESTART, ["[CB] [ENTRY] [L] void ${MYTYPE}.onRestart()"]),
                  (ONRESUME, ["[CB] [ENTRY] [L] void ${MYTYPE}.onResume()"]),
                  (ONSAVEINSTANCESTATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onSaveInstanceState(f : android.os.Bundle)"]),
                  (ONSTART, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStart()"]),
                  (ONSTOP, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStop()"]),
                  (ONRESTOREINSTANCESTATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onRestoreInstanceState(f : android.os.Bundle)"]),
                  # FlowDroid misses the onRestoreInstanceState(Bundle savedInstanceState, PersistableBundle persistentState) version
                  # called if R.attr.persistableMode set to persistAcrossReboots
                  #
                  (ONACTIVITYSTARTED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityStarted(L : ${MYTYPE})"]),
                  (ONACTIVITYSTOPPED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityStopped(L : ${MYTYPE})"]),
                  (ONACTIVITYSAVEINSTANCESTATE, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivitySaveInstanceState(L : ${MYTYPE}, f : android.os.Bundle)"]),
                  (ONACTIVITYRESUMED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityResumed(L : ${MYTYPE})"]),
                  (ONACTIVITYPAUSED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityPaused(L : ${MYTYPE})"]),
                  (ONACTIVITYDESTROYED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityDestroyed(L : ${MYTYPE})"]),
                  (ONACTIVITYCREATED, ["[CB] [ENTRY] [listener] void android.app.Application.ActivityLifecycleCallbacks.onActivityCreated(L : ${MYTYPE}, f : android.os.Bundle)"])]

    cb_to_find = [ (key, EncoderUtils.enum_types_list(list_to_repl,
                                                      [])) # Subs(["MYTYPE"],[[c] for c in class_names])
                   for (key, list_to_repl) in cb_to_repl]

    def get_class_names(self):
        return Activity.class_names

    def get_class_cb(self):
        return Activity.get_class_cb_static()

    @staticmethod
    def get_class_cb_static():
        """ Defines the method signatures of the Activity
        lifecycle methods.

        We use the specification language to pattern match the method
        in the trace, also matching the parameter names.
        """


        # Activity.ONATTACHFRAGMENT = "[CB] [ENTRY] [L] void ${MYTYPE}.onAttachFragment(f : android.app.Fragment)"

        return Activity.cb_to_find

    def __init__(self, class_names, inst_value, trace_map):
        Component.__init__(self, class_names, inst_value, trace_map, "L",
                           "MYTYPE")
        self._child_fragments = set()

    def add_child_fragment(self, fragment):
        self._child_fragments.add(fragment)

    def get_child_fragments(self):
        return self._child_fragments



class Fragment(Component):
    class_names = set(["android.app.Fragment",
                       "android.support.v4.app.Fragment",
                       "android.support.v4.app.ListFragment",
                       "android.app.ListFragment",
                       "android.support.v4.app.DialogFragment",
                       "android.preference.PreferenceFragment",
                       "android.app.DialogFragment",
                       "android.webkit.WebViewFragment",
                       "android.support.v7.preference.PreferenceFragmentCompat"])

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

    cb_to_repl = [(ONCREATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onCreate(f : android.os.Bundle)"]),
                  (ONATTACH, ["[CB] [ENTRY] [L] void ${MYTYPE}.onAttach(f : ${ACTIVITY_TYPE})"]),
                  (ONCREATEVIEW, ["[CB] [ENTRY] [L] android.view.View ${MYTYPE}.onCreateView(f1 : android.view.LayoutInflater, f2 : android.view.ViewGroup, f3 : android.os.Bundle)"]),
                  (ONVIEWCREATED, ["[CB] [ENTRY] [L] void ${MYTYPE}.onViewCreated(f1 : android.view.View, f2 : android.os.Bundle)"]),
                  (ONSTART, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStart()"]),
                  (ONACTIVITYCREATED, ["[CB] [ENTRY] [L] void ${MYTYPE}.onActivityCreated(f : android.os.Bundle)"]),
                  (ONVIEWSTATERESTORED, ["[CB] [ENTRY] [L] void ${MYTYPE}.onViewStateRestored(f : ${ACTIVITY_TYPE})"]),
                  (ONRESUME, ["[CB] [ENTRY] [L] void ${MYTYPE}.onResume()"]),
                  (ONPAUSE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onPause()"]),
                  (ONSTOP, ["[CB] [ENTRY] [L] void ${MYTYPE}.onStop()"]),
                  (ONDESTROYVIEW, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDestroyView()"]),
                  (ONDESTROY, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDestroy()"]),
                  (ONDETACH, ["[CB] [ENTRY] [L] void ${MYTYPE}.onDetach()"]),
                  (ONSAVEINSTANCESTATE, ["[CB] [ENTRY] [L] void ${MYTYPE}.onSaveInstanceState(f : android.os.Bundle)"]),
                  (ONATTACHFRAGMENT, ["[CB] [ENTRY] [f] void ${ACTIVITY_TYPE}.onAttachFragment(L : ${MYTYPE})"])]

    cb_to_find = [ (key, EncoderUtils.enum_types_list(list_to_repl,
                                                      [Subs(["ACTIVITY_TYPE"],[[c] for c in Activity.class_names])]))
                   for (key, list_to_repl) in cb_to_repl]

    def get_class_names(self):
        return Fragment.class_names

    def __init__(self, class_names, inst_value, trace_map):
        Component.__init__(self, class_names, inst_value, trace_map, "L", "MYTYPE")
        self._parent_activities = set()

    def get_class_cb(self):
        return Fragment.get_class_cb_static()

    @staticmethod
    def get_class_cb_static():
        return Fragment.cb_to_find

    def add_parent_activity(self, activity):
        """ Add one activity that attach the fragment (or
        a fragment that attach the fragment) """
        self._parent_activities.add(activity)

    def get_parent_activities(self):
        return self._parent_activities




class KnownAndroidListener:
    listener_classes = frozenset(["android.accounts.OnAccountsUpdateListener",
                                  "android.animation.Animator$AnimatorListener",
                                  "android.animation.LayoutTransition$TransitionListener",
                                  "android.animation.TimeAnimator$TimeListener",
                                  "android.animation.ValueAnimator$AnimatorUpdateListener",
                                  "android.app.ActionBar$OnMenuVisibilityListener",
                                  "android.app.ActionBar$OnNavigationListener",
                                  "android.app.ActionBar$TabListener",
                                  "android.app.Application$ActivityLifecycleCallbacks",
                                  "android.app.DatePickerDialog$OnDateSetListener",
                                  "android.app.FragmentBreadCrumbs$OnBreadCrumbClickListener",
                                  "android.app.FragmentManager$OnBackStackChangedListener",
                                  "android.app.KeyguardManager$OnKeyguardExitResult",
                                  "android.app.LoaderManager$LoaderCallbacks",
                                  "android.app.PendingIntent$OnFinished",
                                  "android.app.SearchManager$OnCancelListener",
                                  "android.app.SearchManager$OnDismissListener",
                                  "android.app.TimePickerDialog$OnTimeSetListener",
                                  "android.bluetooth.BluetoothProfile$ServiceListener",
                                  "android.content.ClipboardManager$OnPrimaryClipChangedListener",
                                  "android.content.ComponentCallbacks",
                                  "android.content.ComponentCallbacks2",
                                  "android.content.DialogInterface$OnCancelListener",
                                  "android.content.DialogInterface$OnClickListener",
                                  "android.content.DialogInterface$OnDismissListener",
                                  "android.content.DialogInterface$OnKeyListener",
                                  "android.content.DialogInterface$OnMultiChoiceClickListener",
                                  "android.content.DialogInterface$OnShowListener",
                                  "android.content.IntentSender$OnFinished",
                                  "android.content.Loader$OnLoadCanceledListener",
                                  "android.content.Loader$OnLoadCompleteListener",
                                  "android.content.SharedPreferences$OnSharedPreferenceChangeListener",
                                  "android.content.SyncStatusObserver",
                                  "android.database.sqlite.SQLiteTransactionListener",
                                  "android.drm.DrmManagerClient$OnErrorListener",
                                  "android.drm.DrmManagerClient$OnEventListener",
                                  "android.drm.DrmManagerClient$OnInfoListener",
                                  "android.gesture.GestureOverlayView$OnGestureListener",
                                  "android.gesture.GestureOverlayView$OnGesturePerformedListener",
                                  "android.gesture.GestureOverlayView$OnGesturingListener",
                                  "android.graphics.SurfaceTexture$OnFrameAvailableListener",
                                  "android.hardware.Camera$AutoFocusCallback",
                                  "android.hardware.Camera$AutoFocusMoveCallback",
                                  "android.hardware.Camera$ErrorCallback",
                                  "android.hardware.Camera$FaceDetectionListener",
                                  "android.hardware.Camera$OnZoomChangeListener",
                                  "android.hardware.Camera$PictureCallback",
                                  "android.hardware.Camera$PreviewCallback",
                                  "android.hardware.Camera$ShutterCallback",
                                  "android.hardware.SensorEventListener",
                                  "android.hardware.display.DisplayManager$DisplayListener",
                                  "android.hardware.input.InputManager$InputDeviceListener",
                                  "android.inputmethodservice.KeyboardView$OnKeyboardActionListener",
                                  "android.location.GpsStatus$Listener",
                                  "android.location.GpsStatus$NmeaListener",
                                  "android.location.LocationListener",
                                  "android.media.AudioManager$OnAudioFocusChangeListener",
                                  "android.media.AudioRecord$OnRecordPositionUpdateListener",
                                  "android.media.JetPlayer$OnJetEventListener",
                                  "android.media.MediaPlayer$OnBufferingUpdateListener",
                                  "android.media.MediaPlayer$OnCompletionListener",
                                  "android.media.MediaPlayer$OnErrorListener",
                                  "android.media.MediaPlayer$OnInfoListener",
                                  "android.media.MediaPlayer$OnPreparedListener",
                                  "android.media.MediaPlayer$OnSeekCompleteListener",
                                  "android.media.MediaPlayer$OnTimedTextListener",
                                  "android.media.MediaPlayer$OnVideoSizeChangedListener",
                                  "android.media.MediaRecorder$OnErrorListener",
                                  "android.media.MediaRecorder$OnInfoListener",
                                  "android.media.MediaScannerConnection$MediaScannerConnectionClient",
                                  "android.media.MediaScannerConnection$OnScanCompletedListener",
                                  "android.media.SoundPool$OnLoadCompleteListener",
                                  "android.media.audiofx.AudioEffect$OnControlStatusChangeListener",
                                  "android.media.audiofx.AudioEffect$OnEnableStatusChangeListener",
                                  "android.media.audiofx.BassBoost$OnParameterChangeListener",
                                  "android.media.audiofx.EnvironmentalReverb$OnParameterChangeListener",
                                  "android.media.audiofx.Equalizer$OnParameterChangeListener",
                                  "android.media.audiofx.PresetReverb$OnParameterChangeListener",
                                  "android.media.audiofx.Virtualizer$OnParameterChangeListener",
                                  "android.media.audiofx.Visualizer$OnDataCaptureListener",
                                  "android.media.effect$EffectUpdateListener",
                                  "android.net.nsd.NsdManager$DiscoveryListener",
                                  "android.net.nsd.NsdManager$RegistrationListener",
                                  "android.net.nsd.NsdManager$ResolveListener",
                                  "android.net.sip.SipRegistrationListener",
                                  "android.net.sip.SipAudioCall$Listener",
                                  "android.net.sip.SipSession$Listener",
                                  "android.net.wifi.p2p.WifiP2pManager$ActionListener",
                                  "android.net.wifi.p2p.WifiP2pManager$ChannelListener",
                                  "android.net.wifi.p2p.WifiP2pManager$ConnectionInfoListener",
                                  "android.net.wifi.p2p.WifiP2pManager$DnsSdServiceResponseListener",
                                  "android.net.wifi.p2p.WifiP2pManager$DnsSdTxtRecordListener",
                                  "android.net.wifi.p2p.WifiP2pManager$GroupInfoListener",
                                  "android.net.wifi.p2p.WifiP2pManager$PeerListListener",
                                  "android.net.wifi.p2p.WifiP2pManager$ServiceResponseListener",
                                  "android.net.wifi.p2p.WifiP2pManager$UpnpServiceResponseListener",
                                  "android.os.CancellationSignal$OnCancelListener",
                                  "android.os.IBinder$DeathRecipient",
                                  "android.os.MessageQueue$IdleHandler",
                                  "android.os.RecoverySystem$ProgressListener",
                                  "android.preference.Preference$OnPreferenceChangeListener",
                                  "android.preference.Preference$OnPreferenceClickListener",
                                  "android.preference.PreferenceFragment$OnPreferenceStartFragmentCallback",
                                  "android.preference.PreferenceManager$OnActivityDestroyListener",
                                  "android.preference.PreferenceManager$OnActivityResultListener",
                                  "android.preference.PreferenceManager$OnActivityStopListener",
                                  "android.security.KeyChainAliasCallback",
                                  "android.speech.RecognitionListener",
                                  "android.speech.tts.TextToSpeech$OnInitListener",
                                  "android.speech.tts.TextToSpeech$OnUtteranceCompletedListener",
                                  "android.view.ActionMode$Callback",
                                  "android.view.ActionProvider$VisibilityListener",
                                  "android.view.GestureDetector$OnDoubleTapListener",
                                  "android.view.GestureDetector$OnGestureListener",
                                  "android.view.InputQueue$Callback",
                                  "android.view.KeyEvent$Callback",
                                  "android.view.MenuItem$OnActionExpandListener",
                                  "android.view.MenuItem$OnMenuItemClickListener",
                                  "android.view.ScaleGestureDetector$OnScaleGestureListener",
                                  "android.view.SurfaceHolder$Callback",
                                  "android.view.SurfaceHolder$Callback2",
                                  "android.view.TextureView$SurfaceTextureListener",
                                  "android.view.View$OnAttachStateChangeListener",
                                  "android.view.View$OnClickListener",
                                  "android.view.View$OnCreateContextMenuListener",
                                  "android.view.View$OnDragListener",
                                  "android.view.View$OnFocusChangeListener",
                                  "android.view.View$OnGenericMotionListener",
                                  "android.view.View$OnHoverListener",
                                  "android.view.View$OnKeyListener",
                                  "android.view.View$OnLayoutChangeListener",
                                  "android.view.View$OnLongClickListener",
                                  "android.view.View$OnSystemUiVisibilityChangeListener",
                                  "android.view.View$OnTouchListener",
                                  "android.view.ViewGroup$OnHierarchyChangeListener",
                                  "android.view.ViewStub$OnInflateListener",
                                  "android.view.ViewTreeObserver$OnDrawListener",
                                  "android.view.ViewTreeObserver$OnGlobalFocusChangeListener",
                                  "android.view.ViewTreeObserver$OnGlobalLayoutListener",
                                  "android.view.ViewTreeObserver$OnPreDrawListener",
                                  "android.view.ViewTreeObserver$OnScrollChangedListener",
                                  "android.view.ViewTreeObserver$OnTouchModeChangeListener",
                                  "android.view.accessibility.AccessibilityManager$AccessibilityStateChangeListener",
                                  "android.view.animation.Animation$AnimationListener",
                                  "android.view.inputmethod.InputMethod$SessionCallback",
                                  "android.view.inputmethod.InputMethodSession$EventCallback",
                                  "android.view.textservice.SpellCheckerSession$SpellCheckerSessionListener",
                                  "android.webkit.DownloadListener",
                                  "android.widget.AbsListView$MultiChoiceModeListener",
                                  "android.widget.AbsListView$OnScrollListener",
                                  "android.widget.AbsListView$RecyclerListener",
                                  "android.widget.AdapterView$OnItemClickListener",
                                  "android.widget.AdapterView$OnItemLongClickListener",
                                  "android.widget.AdapterView.OnItemSelectedListener",
                                  "android.widget.AutoCompleteTextView$OnDismissListener",
                                  "android.widget.CalendarView$OnDateChangeListener",
                                  "android.widget.Chronometer$OnChronometerTickListener",
                                  "android.widget.CompoundButton$OnCheckedChangeListener",
                                  "android.widget.DatePicker$OnDateChangedListener",
                                  "android.widget.ExpandableListView$OnChildClickListener",
                                  "android.widget.ExpandableListView$OnGroupClickListener",
                                  "android.widget.ExpandableListView$OnGroupCollapseListener",
                                  "android.widget.ExpandableListView$OnGroupExpandListener",
                                  "android.widget.Filter$FilterListener",
                                  "android.widget.NumberPicker$OnScrollListener",
                                  "android.widget.NumberPicker$OnValueChangeListener",
                                  "android.widget.NumberPicker$OnDismissListener",
                                  "android.widget.PopupMenu$OnMenuItemClickListener",
                                  "android.widget.PopupWindow$OnDismissListener",
                                  "android.widget.RadioGroup$OnCheckedChangeListener",
                                  "android.widget.RatingBar$OnRatingBarChangeListener",
                                  "android.widget.SearchView$OnCloseListener",
                                  "android.widget.SearchView$OnQueryTextListener",
                                  "android.widget.SearchView$OnSuggestionListener",
                                  "android.widget.SeekBar$OnSeekBarChangeListener",
                                  "android.widget.ShareActionProvider$OnShareTargetSelectedListener",
                                  "android.widget.SlidingDrawer$OnDrawerCloseListener",
                                  "android.widget.SlidingDrawer$OnDrawerOpenListener",
                                  "android.widget.SlidingDrawer$OnDrawerScrollListener",
                                  "android.widget.TabHost$OnTabChangeListener",
                                  "android.widget.TextView$OnEditorActionListener",
                                  "android.widget.TimePicker$OnTimeChangedListener",
                                  "android.widget.ZoomButtonsController$OnZoomListener"])
