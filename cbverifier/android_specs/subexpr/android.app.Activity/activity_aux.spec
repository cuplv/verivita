//manually combined pieces of activity spec

//writ means "written" or I wrote these by hand as opposed to script generated specs such as Activity_all and Fragment_all
REGEXP Activity_writ_onResumed_has(act) = [(TRUE[*] ; Activity_all_onResume(act) ; ((!Activity_all_onPause(act)) & TRUE)[*])];
REGEXP Activity_writ_onResumed_just(act) = [TRUE[*]; Activity_all_onResume(act)]