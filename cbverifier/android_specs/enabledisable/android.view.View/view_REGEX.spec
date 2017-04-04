//view set on click listener
//TODO: following is overapproximation assuming any registered listener can be clicked, we may want to later refine this to replacement which is the actual behavior
REGEXP view_onClick_listener_set_just(view,listener) = [TRUE[*];[CI] [ENTRY] [view] void android.view.View.setOnClickListener(listener : android.view.View$OnClickListener)];
REGEXP view_onClick_listener_set_has(view,listener) = [view_onClick_listener_set_just(view,listener);TRUE[*]];


