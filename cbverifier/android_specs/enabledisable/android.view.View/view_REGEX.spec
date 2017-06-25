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

REGEXP view_onClick_enabled_set_has(view) = [(view_onClick_enabled_set_just(view);(![CI] [ENTRY] [view] void android.widget.TextView.setEnabled(TRUE : boolean))[*]) | (![CI] [ENTRY] [view] void android.widget.TextView.setEnabled(# : boolean))[*]]


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
