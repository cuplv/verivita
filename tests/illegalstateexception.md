NGI = No GitHub Issues exits
### /frameworks/base/core/java/android/widget/
* __PopupWindow.java__
	* IllegalStateException("You must specify a valid content view by "
		* NGI
* __RelativeLayout.java__
	* IllegalStateException("Circular dependencies cannot exist"
		* https://github.com/flavienlaurent/datetimepicker/issues/45

* __AbsListView.java__
	* IllegalStateException("AbsListView: attempted to start selection mode " +
		* NGI
	* IllegalStateException("You cannot call onTextChanged with a non "
		* NGI
* __TextView.java__
	* IllegalStateException("focus search returned a view " +
		* NGI
* __ListView.java__
	* IllegalStateException("The content of the adapter has changed but " +)
		* https://github.com/YoKeyword/IndexableRecyclerView/issues/7
		* "When calling'addHeaderView' to ListView, Adapter will be converted into HeaderViewAdapter, so when you click back quickly, it crash because itemCount checking goes wrong "
		* https://github.com/realm/realm-android-adapters/issues/11
		* __Developer think there's a race condition. So it would be interesting__
		
		
###/frameworks/base/core/java/android/app/

* __Activity.java__
	* IllegalStateException("Can only be called on top-level activity");
		* https://github.com/alibaba/freeline/issues/171 (open issue, not fixed)
	* IllegalStateException("Must be called from main thread");
		* No useful ones.
	* IllegalStateException("Can not be called from an embedded activity");
		* NGI
	* IllegalStateException("Can not be called to deliver a result");
		* NGI
	* IllegalStateException("System services not available to Activities before onCreate()");
		* https://github.com/cuplv/callback-verification/wiki/Activity-getSystemService-before-onCreate
	* IllegalStateException("Derived class did not call super.onSaveInstanceState()");
		* NGI
	* IllegalStateException("Derived class did not call super.onRestoreInstanceState()")
		* NGI
	* IllegalStateException("This view must be attached to a window first");
		* Only issue on github:
			* https://github.com/SimonVT/android-menudrawer/issues/19
	* IllegalStateException("onMeasure() did not set the" + " measured dimension by calling" + " setMeasuredDimension()")
		* https://github.com/MikeOrtiz/TouchImageView/issues/47
	

* __UiAutomationConnection.java__
	* IllegalStateException("Already connected.");
	* IllegalStateException("Already disconnected.");
	* IllegalStateException("Error while registering UiTestAutomationService.", re);
	* IllegalStateException("Error while unregistering UiTestAutomationService",
	* IllegalStateException("Connection shutdown!");
	* IllegalStateException("Not connected!");
	
* __TaskStackBuilder.java__
	* IllegalStateException("No intents added to TaskStackBuilder; cannot startActivities");
	* No intents added to TaskStackBuilder; cannot getPendingIntent
	* No intents added to TaskStackBuilder; cannot getPendingIntent

* __ListFragment.java__
	* IllegalStateException("Can't be used with a custom content view");
	* IllegalStateException("Can't be used with a custom content view");
	* IllegalStateException("Content view not yet created");
	
* __Fragment.java__
	* IllegalStateException("Fragment already active");
		* https://github.com/Flaredown/FlaredownAndroid/issues/61
		* https://github.com/unfoldingWord-dev/ts-android/issues/945
		* TODO: there're more issues. Need to find useful ones.
		
	* IllegalStateException("Fragment " + this + " not attached to Activity");
	* IllegalStateException("Can't retain fragements that are nested in other fragments");
		* https://github.com/roomorama/Caldroid/issues/186
	* IllegalStateException("Fragment does not have a view");
		* NGI


* __FragmentManager.java__
	* IllegalStateException("Fragment " + fragment + " is not currently in the FragmentManager")
		* https://github.com/avuton/controldlna/issues/1
		
	* IllegalStateException("Fragement no longer exists for key " + key + ": index " + index
		* https://github.com/avast/android-styled-dialogs/pull/19
	
	* IllegalStateException("No activity");
	* IllegalStateException("Fragment already added: " + fragment);
	* IllegalStateException("Fragment not added: " + fragment);
	* IllegalStateException("Can not perform this action after onSaveInstanceState");
	
	* IllegalStateException("Can not perform this action inside of " + mNoTransactionsBecause);
			
	* IllegalStateException("Activity has been destroyed");
	* IllegalStateException("Recursive entry to executePendingTransactions");
	* IllegalStateException("Must be called from main thread of process");
	* IllegalStateException("Failure saving state: active " + f + " has cleared index: " + f.mIndex));
	* IllegalStateException("Failure saving state: " + f + " has target not in fragment manager: 
	* IllegalStateException( "No instantiated fragment for index #");
		* https://github.com/enviroCar/enviroCar-app/issues/268
	* IllegalStateException("Already added!");
	* IllegalStateException("Already attached");
	
* __DialogFragment.java__
	* IllegalStateException("DialogFragment can not be attached to a container view");
	* IllegalStateException("You can not set Dialog's OnCancelListener or OnDismissListener");
		* https://github.com/VKCOM/vk-android-sdk/issues/206

* __BackStackRecord.java__
	* IllegalStateException("Not on back stack");
	* IllegalStateException("Can't change tag of fragment "
	* IllegalStateException("Can't change container ID of fragment "
	* IllegalStateException("This FragmentTransaction is not allowed to be added to the back stack.")
	* IllegalStateException("This transaction is already being added to the back stack");
	*  IllegalStateException("commit already called");
		* https://github.com/robolectric/robolectric/issues/1326
		* https://github.com/roughike/BottomBar/issues/465
	*  IllegalStateException("addToBackStack() called after commit()");

* __LoaderManager.java__
	* IllegalStateException("Called while creating a loader");
	* 
* __AppOpsManager.java__
	* IllegalStateException("sOpToSwitch length " + sOpToSwitch.length + " should be " + _NUM_OP);
	* IllegalStateException("sOpToString length " + sOpToSwitch.length + " should be " + _NUM_OP);
	* IllegalStateException("sOpNames length " + sOpToSwitch.length + " should be " + _NUM_OP);
	* IllegalStateException("sOpPerms length " + sOpToSwitch.length + " should be " + _NUM_OP);
	* IllegalStateException("sOpDefaultMode length " + sOpToSwitch.length + " should be " + _NUM_OP);
	* IllegalStateException("sOpDisableReset length " + sOpToSwitch.length + " should be " + _NUM_OP);
	
	* All NGI
* __MediaRouteActionProvider.java__
	* IllegalStateException("The MediaRouteActionProvider's Context "
	
* __DownloadManager.java__
	* IllegalStateException("Failed to get external storage files directory");
	* IllegalStateException(file.getAbsolutePath() +
	* IllegalStateException("Unable to create directory: "+
	* IllegalStateException("Failed to get external storage public directory");
	* IllegalStateException(file.getAbsolutePath() +
	* IllegalStateException("Unable to create directory: "+
* __LoadedApk.java__
 	* IllegalStateException("Unable to get package info for "
 	* IllegalStateException("Unbinding Receiver " + r
 	* IllegalStateException("Receiver " + mReceiver + " registered with differing Context
 	* IllegalStateException("Receiver " + mReceiver + " registered with differing handler
 	* IllegalStateException("Unbinding Service " + c + " from Context that is no longer in use: 

* __LocalActivityManager.java__
	* "Activities can't be added until the containing group has been created."
* __Dialog.java__
	* "OnDismissListener is already taken by "
		* https://github.com/mattrey555/visibleautomation/issues/1
	* "OnCancelListener is already taken by "
 
* __MediaRouteButton.java__
	* IllegalStateException("The MediaRouteButton's Context is not an Activity."); 
 	
 
### __/frameworks/base/core/java/android/view/__

* LayoutInflater.java
	* IllegalStateException("A factory has already been set on this LayoutInflater");
	
	
	
* PointerIcon.java
	* IllegalStateException("The icon is not loaded.");
* HardwareRenderer.java
	* IllegalStateException("HardwareRenderer cannot be used "+ "from multiple threads")
	* IllegalStateException("Could not create an EGL context. eglCreateContext failed with error: ")
		* This appears to be an issue with the Nexus 4, rather than specific to app.	
		* http://stackoverflow.com/q/19748856
		
	* IllegalStateException("eglMakeCurrent failed ")
	* IllegalStateException(""Hardware acceleration can only be used with a " +
"single UI thread.")
		* https://github.com/mapbox/mapbox-gl-native/issues/4911
	 
* TextureView.java
	* IllegalStateException("Could not acquire hardware rendering context");
* View.java
	*  IllegalStateException("VIEW_STATE_IDs array length does not match ViewDrawableStates style array")
	*  IllegalStateException("Could not find a method " +                                               handlerName + "(View) in the activity "+ getContext().getClass() + " for onClick handler" + " on view " + View.this.getClass() + idText, e);
		* Looks like a xml error
		* https://github.com/JakeWharton/butterknife/issues/254
	
	* IllegalStateException("Could not execute non " + "public method of the activity", e);
		* NGI
		
		* https://github.com/pennlabs/penn-mobile-android/pull/332
		
__/frameworks/base/core/java/android/content/__
	
* CursorEntityIterator.java
	* IllegalStateException("calling hasNext() when the iterator is closed"); 
		* No GitHub Issues
	* IllegalStateException("calling next() when the iterator is closed");
		* NGI
	* IllegalStateException("you may only call next() if hasNext() is true");
		* NGI
	* IllegalStateException("calling reset() when the iterator is closed");
		* NGI
	* IllegalStateException("closing when already closed");
		* NGI
		
* SyncAdapterType.java
	* IllegalStateException("this method is not allowed to be called when this is a key");
		* NGI
	* IllegalStateException("Could not execute " + "method of the activity", e);
	
__/frameworks/base/core/java/com/android/internal/util/__

* JournaledFile.java
	*  IllegalStateException("uncommitted write already in progress");
		* NGI
	* IllegalStateException("no file to commit");
		* Issues not match
	* IllegalStateException("no file to roll back");
		* NGI

__/frameworks/base/core/java/android/database/__

* Observable.java	
	* IllegalStateException("Observer " + observer + " is already registered.");
		* https://github.com/ongakuer/CircleIndicator/issues/54
		* https://github.com/gabrielemariotti/cardslib/issues/191
		* https://github.com/JakeWharton/ActionBarSherlock/issues/557
		
	* IllegalStateException("Observer " + observer + " was not registered.");
		* https://github.com/orhanobut/simplelistview/issues/4
		

__/frameworks/base/core/java/android/util/__


__/frameworks/base/core/java/android/widget/__

*	ArrayAdapter.java
	* IllegalStateException("ArrayAdapter requires the resource ID to be a TextView")
		* https://github.com/DonLiangGit/Perfatch/issues/7