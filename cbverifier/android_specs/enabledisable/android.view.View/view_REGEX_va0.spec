//view set on click listener
//TODO: following is overapproximation assuming any registered listener can be clicked, we may want to later refine this to replacement which is the actual behavior

REGEXP view_onClick_listener_set_just(view,listener) = [TRUE[*];
	(
		[CI] [ENTRY] [view] void android.view.View.setOnClickListener(listener : android.view.View$OnClickListener)
		| [CI] [ENTRY] [view] void android.support.v7.widget.Toolbar.setNavigationOnClickListener(listener : android.view.View$OnClickListener)
		| [CI] [ENTRY] [view] void android.widget.AutoCompleteTextView.setOnClickListener(listener : android.view.View$OnClickListener)

	)
];
REGEXP view_onClick_listener_set_has(view,listener) = [view_onClick_listener_set_just(view,listener);TRUE[*]];

REGEXP view_onClick_enabled_set_just(view) = [TRUE[*];[CI] [ENTRY] [view] void android.widget.TextView.setEnabled(TRUE : boolean)];

REGEXP view_onClick_enabled_set_has(view) = [(view_onClick_enabled_set_just(view);((![CI] [ENTRY] [view] void android.widget.TextView.setEnabled(TRUE : boolean)) & TRUE)[*]) | ((![CI] [ENTRY] [view] void android.widget.TextView.setEnabled(# : boolean)) & TRUE)[*]];


//Regular expression is true when this is a view we know is attached to an Activity
REGEXP view_attached_has(act,view) = [FALSE]; //disable attachment rules

REGEXP view_lose_precision_has(view) = [TRUE[*]]; //only lose precision rules

REGEXP view_lose_precision_just(view) = [FALSE] //only lose precision rules
