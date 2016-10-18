NGI = No GitHub Issues exit

__/frameworks/base/core/java/android/app/__

* Activity.java
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
	

* UiAutomationConnection.java
	* IllegalStateException("Already connected.");
	* IllegalStateException("Already disconnected.");
	* IllegalStateException("Error while registering UiTestAutomationService.", re);
	* IllegalStateException("Error while unregistering UiTestAutomationService",
	* IllegalStateException("Connection shutdown!");
	* IllegalStateException("Not connected!");
	
* TaskStackBuilder.java
	* IllegalStateException("No intents added to TaskStackBuilder; cannot startActivities");
	* No intents added to TaskStackBuilder; cannot getPendingIntent
	* No intents added to TaskStackBuilder; cannot getPendingIntent

* ListFragment.java
	* IllegalStateException("Can't be used with a custom content view");
	* IllegalStateException("Can't be used with a custom content view");
	* IllegalStateException("Content view not yet created");
	
* FragmentManager.java
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
__/frameworks/base/core/java/android/view/__

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