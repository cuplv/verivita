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

REGEXP Activity_not_visible_has(act) = [Activity_not_visible_just(act);TRUE[*]];


//#("void startActivity(android.content.Intent)","android.app.Activity.void startActivity(android.content.Intent)")
// ("void startActivity(android.content.Intent,android.os.Bundle)","android.app.Activity.void startActivity(android.content.Intent,android.os.Bundle)")
//N ("void startActivity(android.content.Intent,android.os.Bundle)","android.app.Fragment.void startActivity(android.content.Intent,android.os.Bundle)")
//# ("void startActivityForResult(android.content.Intent,int)","android.app.Activity.void startActivityForResult(android.content.Intent,int)")
//# ("void startActivityForResult(android.content.Intent,int)","android.support.v4.app.FragmentActivity.void startActivityForResult(android.content.Intent,int)")
//# ("void startActivityForResult(android.content.Intent,int,android.os.Bundle)","android.app.Activity.void startActivityForResult(android.content.Intent,int,android.os.Bundle)")
//N ("void startActivityForResult(android.content.Intent,int,android.os.Bundle)","android.app.Fragment.void startActivityForResult(android.content.Intent,int,android.os.Bundle)")
//# ("void startActivityForResult(android.content.Intent,int,android.os.Bundle)","android.support.v4.app.FragmentActivity.void startActivityForResult(android.content.Intent,int,android.os.Bundle)")
//# ("void startActivityForResult(android.content.Intent,int,android.os.Bundle)","android.support.v4.app.Fragment.void startActivityForResult(android.content.Intent,int,android.os.Bundle)")
//# ("void startActivityFromChild(android.app.Activity,android.content.Intent,int)","android.app.Activity.void startActivityFromChild(android.app.Activity,android.content.Intent,int)")
//# ("void startActivityFromFragment(android.app.Fragment,android.content.Intent,int,android.os.Bundle)","android.app.Activity.void startActivityFromFragment(android.app.Fragment,android.content.Intent,int,android.os.Bundle)")
//# ("void startActivityFromFragment(android.support.v4.app.Fragment,android.content.Intent,int)","android.support.v4.app.FragmentActivity.void startActivityFromFragment(android.support.v4.app.Fragment,android.content.Intent,int)")

// ("void startActivityFromFragment(android.support.v4.app.Fragment,android.content.Intent,int,android.os.Bundle)","android.support.v4.app.FragmentActivity.void startActivityFromFragment(android.support.v4.app.Fragment,android.content.Intent,int,android.os.Bundle)")
REGEXP Activity_startActivity(act) = [
	[CI] [ENTRY] [act] void android.app.Activity.startActivity(# : android.content.Intent)
	| [CI] [ENTRY] [act] void android.app.Activity.startActivity(# : android.content.Intent,#:android.os.Bundle)
	| [CI] [ENTRY] [act] void android.app.Activity.startActivityForResult(# : android.content.Intent,# : int)
	| [CI] [ENTRY] [act] void android.support.v4.app.FragmentActivity.startActivityForResult(# : android.content.Intent,# : int)
	| [CI] [ENTRY] [act] void android.app.Activity.startActivityForResult(# : android.content.Intent,# : int, # : android.os.Bundle)
	| [CI] [ENTRY] [act] void android.support.v4.app.FragmentActivity.startActivityForResult(# : android.content.Intent,# : int,# : android.os.Bundle)
	| [CI] [ENTRY] [act] void android.app.Activity.startActivityFromChild(# : android.app.Activity,# : android.content.Intent,# : int)
	| [CI] [ENTRY] [#] void android.app.Activity.startActivityFromChild(act : android.app.Activity,# : android.content.Intent,# : int)
	| [CI] [ENTRY] [act] void android.app.Activity.startActivityFromFragment(# : android.app.Fragment,# : android.content.Intent,# : int,# : android.os.Bundle)
	| [CI] [ENTRY] [act] void android.support.v4.app.FragmentActivity.startActivityFromFragment(# : android.support.v4.app.Fragment,# : android.content.Intent,# : int)
	| [CI] [ENTRY] [act] void android.support.v4.app.FragmentActivity.startActivityFromFragment(# : android.support.v4.app.Fragment,# : android.content.Intent,# : int,# : android.os.Bundle)
]
