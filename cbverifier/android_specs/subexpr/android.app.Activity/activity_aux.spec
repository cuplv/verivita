//manually combined pieces of activity spec

//writ means "written" or I wrote these by hand as opposed to script generated specs such as Activity_all and Fragment_all
REGEXP Activity_writ_onResumed_has(act) = [(TRUE[*] ; Activity_all_onResume(act) ; (
	(
		((!Activity_all_onPause(act))
		& (!Activity_all_onDestroy(act)))
	) & TRUE)[*]

)
];
REGEXP Activity_writ_onResumed_just(act) = [TRUE[*]; Activity_all_onResume(act)];

REGEXP Activity_not_visible_just(act) = [TRUE[*]; 
	(Activity_all_onPause(act)
	| Activity_all_onDestroy(act))];

REGEXP Activity_not_visible_has(act) = [Activity_not_visible_just(act);TRUE[*]]
