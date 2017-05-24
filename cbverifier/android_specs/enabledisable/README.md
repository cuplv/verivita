**Specs for no view attachment hierarchy**

/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.view.View/view_REGEX.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.CountdownTimer/countdowntimer.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.view.View/onClick_listener_setenabled.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.AsyncTask/AsyncTask.spec
/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifestate.spec
TODO: ListView spec for no attach hierarchy

**Lifecycle with async task init**
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.AsyncTask/AsyncTask_justinit.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifecycle.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment_lifecycle.spec


**Specs for lifecycle**
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifecycle.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment_lifecycle.spec
//AsyncTask and CountdownTimer have no lifecycle since we only have two callbacks, onPreExecute and onPostExecute

**Allow and disallow specs**

/home/s/Documents/source/callback-verification/cbverifier/android_specs/allowdisallow/fragment/fragment_getString.spec


**View attachment hierarchy (not completed)**
//We are not currently doing view attachment hierarchy due to state space explosion
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.widget.ListView/listView_attachdetach_setListener.spec
/home/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.view.View/button_attachdetach_setListener.spec:
