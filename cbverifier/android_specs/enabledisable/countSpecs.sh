LC="/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/DialogFragment_lifecycle.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifecycle.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment_lifecycle.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.AsyncTask/AsyncTask_justinit.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Activity/activity_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Fragment/fragment_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Activity/activity_aux.spec"


LS0="/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/DialogFragment_lifecycle.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.view.View/view_REGEX_va0.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.CountdownTimer/countdowntimer.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.view.View/onClick_listener_setenabled.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.AsyncTask/AsyncTask.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifestate.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.AlertDialog/dialog_va0.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.AlertDialog/DialogInterfaces_OnClickListener.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.widget.PopupMenu/popupmenu_va0.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.widget.PopupMenu/PopupMenu.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.widget.Toolbar/toolbar.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.widget.Toolbar/onMenuItemClick.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Activity/activity_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Fragment/fragment_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Activity/activity_aux.spec"

LS1="/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/DialogFragment_lifecycle.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.view.View/view_REGEX.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.CountdownTimer/countdowntimer.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.view.View/onClick_listener_setenabled.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.AsyncTask/AsyncTask.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifestate.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.AlertDialog/dialog.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.AlertDialog/DialogInterfaces_OnClickListener.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.widget.PopupMenu/popupmenu.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.widget.PopupMenu/PopupMenu.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.widget.Toolbar/toolbar.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.widget.Toolbar/onMenuItemClick.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Activity/activity_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Fragment/fragment_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Activity/activity_aux.spec"


#lifecycle
LC_SPEC_COUNT="0"
LC_REGEXP_COUNT="0"
for r in $(echo $LC |sed -e "s/:/ /g")
do
	#echo $r
	#echo ""
	LC_SPEC_COUNT="$LC_SPEC_COUNT + $(cat $r |egrep "^SPEC" |wc -l)"
	LC_REGEXP_COUNT="$LC_SPEC_COUNT + $(cat $r |egrep "^REGEXP" |wc -l)"
done 
echo "LC SPEC COUNT $(expr $LC_SPEC_COUNT)"
echo "LC REGEXP COUNT $(expr $LC_REGEXP_COUNT)"

#lifestate va0
LS0_SPEC_COUNT="0"
LS0_REGEXP_COUNT="0"
for r in $(echo $LS0 |sed -e "s/:/ /g")
do
	#echo $r
	#echo ""
	LS0_SPEC_COUNT="$LS0_SPEC_COUNT + $(cat $r |egrep "^SPEC" |wc -l)"
	LS0_REGEXP_COUNT="$LS0_SPEC_COUNT + $(cat $r |egrep "^REGEXP" |wc -l)"
done 
echo "LS0 SPEC COUNT $(expr $LS0_SPEC_COUNT)"
echo "LS0 REGEXP COUNT $(expr $LS0_REGEXP_COUNT)"


#lifestate va1
LS1_SPEC_COUNT="0"
LS1_REGEXP_COUNT="0"
for r in $(echo $LS1 |sed -e "s/:/ /g")
do
	#echo $r
	#echo ""
	LS1_SPEC_COUNT="$LS1_SPEC_COUNT + $(cat $r |egrep "^SPEC" |wc -l)"
	LS1_REGEXP_COUNT="$LS1_SPEC_COUNT + $(cat $r |egrep "^REGEXP" |wc -l)"
done 
echo "LS1 SPEC COUNT $(expr $LS1_SPEC_COUNT)"
echo "LS1 REGEXP COUNT $(expr $LS1_REGEXP_COUNT)"
