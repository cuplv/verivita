## Instructions 

###TowerIssue1558

This directory reproduces this issue: https://github.com/DroidPlanner/Tower/issues/1558 

* __Step to reproduce__:
	1. Run this app
	2. Change the orientation
* __What I think causes this bug__:
	* In the Tower app, `SlideToUnlockDialog` fragment is abstract. Everytime you need it, you need to implement the abstract methods.(I think this behavior is treated as an anonymous class). In code(of my sample app):
	
			SimpleDialogFragment sdf = new SimpleDialogFragment(){
            	/** Overriding the methods crashes the app **/
            	@Override 
            	public void overrideTheMethod(){
                	return;
            	}
        	};
	
	 If we are creating the Fragment without overriding the method, it won't crash.
	 
	* When you rotates, the Activity is recreated and the fragment is re-instantiated, which crashes the App.
	
	
	
	
* Fix:
	1. Tower version: override `onPause()` method of the fragment, call `dismiss()` in that
	2. StackOverflow: Put __setRetainInstance(true)__ inside DialogFragment.
		