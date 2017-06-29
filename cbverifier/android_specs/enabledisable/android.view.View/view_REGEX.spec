//view set on click listener
//TODO: following is overapproximation assuming any registered listener can be clicked, we may want to later refine this to replacement which is the actual behavior

REGEXP view_onClick_listener_set_just(view,listener) = [TRUE[*];
	(
		[CI] [ENTRY] [view] void android.view.View.setOnClickListener(listener : android.view.View$OnClickListener)
		| [CI] [ENTRY] [toolbar] void android.support.v7.widget.Toolbar.setNavigationOnClickListener(listener : android.view.View$OnClickListener)
	)
];
REGEXP view_onClick_listener_set_has(view,listener) = [view_onClick_listener_set_just(view,listener);TRUE[*]];

REGEXP view_onClick_enabled_set_just(view) = [TRUE[*];[CI] [ENTRY] [view] void android.widget.TextView.setEnabled(TRUE : boolean)];

REGEXP view_onClick_enabled_set_has(view) = [(view_onClick_enabled_set_just(view);((![CI] [ENTRY] [view] void android.widget.TextView.setEnabled(TRUE : boolean)) & TRUE)[*]) | ((![CI] [ENTRY] [view] void android.widget.TextView.setEnabled(# : boolean)) & TRUE)[*]];


//Regular expression is true when this is a view we know is attached to an Activity
REGEXP view_attached_has(act,view) = [TRUE[*];view = [CI] [EXIT] [act] android.view.View android.app.Activity.findViewById(# : int);TRUE[*]]; 

//Circumstances where we say we lose precision (later this should handle findViewByID on view objects and other nested things)
//All of these probably could be specified but we need to lazily instantiate to avoid too much work
REGEXP view_lose_precision(view) = [TRUE[*];
	(
		view = [CI] [EXIT] [#] android.view.View android.app.Dialog.findViewById(# : int)
		| view = [CI] [EXIT] [#] android.view.View android.view.LayoutInflater.inflate(# : int,# : android.view.ViewGroup,# : boolean)
	)
;TRUE[*]] 


////Activity attachment
//REGEXP view_activity_attachment_method(act,v) = [ Activity_all_findViewByID_ci(act,v)];
//
////REGEXP view_view_attachment_method = [ ];
//
//REGEXP view_lose_precision_method = [ FALSE ];
//
//REGEXP view_attached_Activity(view,activity) = [TRUE[*]; view_activity_attachment_method(activity,view); TRUE[*]];
//
//REGEXP view_unknown_attachment(view) = [ FALSE ]
