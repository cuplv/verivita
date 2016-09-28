

#### What we are interested in
##### 1. FragmentsReplaceInteractionBug
* Steps to reproduce the bug:
	1. Click the 'First Fragment' Button
	2. Before the counting down is over, click the 'Second Fragment' button
	3. The app will crash and throw an IllegalStatusException when the countdown is over.
* The reason why it is crashing:
	1. The second fragment replaced the first fragment with `replace` method
	2. The first fragment is then __NOT attached__ to the activity. So calling any Fragment method(in this case `getString`) will crash it.

* Related Codes:
	In this file
	`app/src/main/java/com/peilunzhang/fragmentsreplaceinteractionbug/CountdownFragment.java`
	at line 36-28:
	
	 	public void onFinish() {
        	textMain.setText(getString(R.string.mainText));
        }
    `getString` method crashes the app

#### What we might be interested in

##### 1. FragmentContext

* Steps to reproduce:
	1. Open the `FragmentContext` app
	2. Click the button
* Related Code:

	In `app/src/main/java/com/peilunzhang/fragmentcontext/FunctionFragment.java`
	at line 17
	
		LinearLayout layout = new LinearLayout(this.getActivity());
		
	`getActivity` and `getContext` cannot be called before `onCreate` method get called.
	
* This might be too trivial so put this as what we might be interested in		


#### What we are not interested in


#####1. TowerIssue1558:

This directory reproduces this issue: https://github.com/DroidPlanner/Tower/issues/1558 

* __Step to reproduce__:
	1. Run `TowerIssue1558` app
	2. Change the orientation of the devices
* __What I think causes this bug__:



	In this file:
	`app/src/main/java/com/peilunzhang/towerissue1558/MainActivity.java`
	
	at line 12-17:
	
	
		SimpleDialogFragment sdf = new SimpleDialogFragment(){
        	@Override
            public void overrideTheMethod(){
                return;
            }
        };
	
	
	Overring the method is making an anonymous class./** TODO: add more about this **/
	
		
* Fix:
	1. Tower version: override `onPause()` method of the fragment, call `dismiss()` in that
	2. StackOverflow: Put __setRetainInstance(true)__ inside DialogFragment.