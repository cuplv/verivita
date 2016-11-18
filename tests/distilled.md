
1. domoticz-android
   * Issue: https://github.com/domoticz/domoticz-android/issues/326
   * Hash of bug: `af323aa`
   * Hash of fix: `751af69`
   * Exception: `llegalStateException: Fragment Preference{21662bf} not attached to Activity`
   * Distilled app: https://github.com/cuplv/callback-verification/tree/tests/tests/distilled_apps/domoticzDistill
   * Fix of Distilled: https://github.com/cuplv/callback-verification/tree/tests/tests/distilled_apps/domoticzDistillFix
   * Cause of bug:
     * Fragment `A` is attached to Activity `main`
     * In Fragment `A`, there is a HTTPRequest for getting information from certain website.
     * Before the request is done, replace Fragment `A` by Fragment `B`
     * When the HTTP request is done, it tries to call `getString` but at this time, Fragment `A` isn't attached to the `main` Activity, so the app crashes.
   * To reproduce in Distilled app:
      1. Press `First Fragment` Button and quickly press `Second Fragment` Button
    
  
2. watchlater
  * Issue: https://github.com/lambdasoup/watchlater/issues/29
  * Hash of bug: 1c3e264
  * Hash of fix: e11255b
  * Exception: `IllegalStateException: Can not perform this action after onSaveInstanceState`
  * Distilled app: https://github.com/cuplv/callback-verification/tree/tests/tests/distilled_apps/watchlaterDistill
  * Fix of Distilled app: https://github.com/cuplv/callback-verification/tree/tests/tests/distilled_apps/watchlaterDistillFix
  * Cause of Bug:
    * There is a countdowntimer(cdt) in the `main` Activity. When it finishes, it will commit a fragment transaction
    * Before the cdt finishes, we start the second activity, which results in the first activity being __paused__
    * If the first activity is __paused__ and the cdt finishes, fragment transaction will crash the app.
  * To reproduce in Distilled app:
    * Open the app and before the cdt finishes, click `Click Me` button
  
 
 3. watchlater
  * Issue: https://github.com/lambdasoup/watchlater/issues/29
  * Hash of bug: 1c3e264
  * Hash of fix: e11255b 
  * Exception: `IllegalStateException: Activity has been destroyed`
  * Distilled app: https://github.com/cuplv/callback-verification/tree/tests/tests/distilled_apps/watchlaterDistill2
  * Fix of Distilled app: https://github.com/cuplv/callback-verification/tree/tests/tests/distilled_apps/watchlaterDistill2Fix
  * Cause of Bug:
    * There is a countdowntimer(cdt) in the `main` Activity. When it finishes, it will commit a fragment transaction
    * Before the cdt finishes, we start the second activity, which results in the first activity being __destroyed__(due to memory pressure)
    * If the first activity is __destroyed__ and the cdt finishes, fragment transaction will crash the app.
  * To reproduce in Distilled app:
    * Open the app and before the cdt finishes, click `Click Me` button


 
 4. Original Repo:
  Url: https://github.com/ceaseless-prayer/CeaselessAndroid
Hash of bug: 7028dc1
Hash of fix: 6569055