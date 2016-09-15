
##Apps
###AsyncTask
`SimpleButtonAsync`
  
`SimpleButtonAsyncBug` - AsyncTask exec twice bug
###Fragments

`FragmentsReplaceInteractionBug` - reproducing the bug of Kistenstapeln-Android

* Steps to reproduce the bug:
	1. Click the 'First Fragment' Button
	2. Before the counting down is over, click the 'Second Fragment' button
	3. The app will crash and throw an IllegalStatusException when the countdown is over.
* The reason why it is crashing:
	1. The second fragment replaced the first fragment with `replace` method
	2. The first fragment is then __NOT attached__ to the activity. So calling any Fragment method(in this case `getString`) will crash it.


