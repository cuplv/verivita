##Fragment not attached to Activity
* Kistenstapeln-Android 
	- Issue: https://github.com/d120/Kistenstapeln-Android/issues/1
	- Description: `getString` after the fragment is replaced.
	- Original Repo: 
		- Url: https://github.com/d120/Kistenstapeln-Android		- Hash of bug: `5e54c44`
		- Hash of fix: not fix yet
	- Distilled App:
		- Buggy: 
			- `KistenstapelnDistill`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/KistenstapelnDistill
		- Fix: 
			- `KistenstapelnDistillFix`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/KistenstapelnDistillFix
	
* Domoticz-android
	- Issue: https://github.com/domoticz/domoticz-android/issues/326
	- Replace activity before the the HTTP request is done.
	- Original Repo:
		- Url: https://github.com/domoticz/domoticz-android
		- Hash of bug: `af323aa`
		- Hash of fix: `751af69`
	- Distilled App:
		- Buggy: 
			- `domoticzDistill`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/domoticzDistill
		- Fix:
			- `domoticzDistillFix`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/domoticzDistillFix

##AddView RemoveView
* Ceaselese
	- Original Repo:
		- Url: https://github.com/ceaseless-prayer/CeaselessAndroid
		- Hash of bug: `7028dc1`
		- Hash of fix: `6569055`
	- Distilled App:
		- Buggy: 
			- `CeaselessDistill`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/CeaselessDistill
		- Fix:
			- `CeaselessDistillFix`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/CeaselessDistillFix


##Add/Remove Fragment
	* Plunjr
	
	* AndFChat

##Activity has been destroyed
* watchlater
	- Issue: https://github.com/lambdasoup/watchlater/issues/29
	- Fragment Transaction after the activity is destroyed
	- Original Repo:
		- Url: https://github.com/lambdasoup/watchlater			- Hash of bug: `1c3e264`
			- Hash of fix: `e11255b`
	
	- Distilled App:
		- Buggy: 
			- `watchlaterDistill2`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/watchlaterDistillFix		
		- Fix:
			- `watchlaterDistill2Fix`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/watchlaterDistill2Fix
## Fragment context

## onSaveStateInstance

* watchlater
	- Original Repo:
		- Url: https://github.com/lambdasoup/watchlater			- Hash of bug: `1c3e264`
			- Hash of fix: `e11255b`
	
	- Distilled App:
		- Buggy: 
			- `watchlaterDistill`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/watchlaterDistillFix		
		- Fix:
			- `watchlaterDistillFix`
			- https://github.com/cuplv/callback-verification/tree/tests/tests/watchlaterDistill2Fix

## Content view not yet created

* aard2-android:
	* issue: https://github.com/itkach/aard2-android/issues/6
	* Setting up ListFragment before view is created