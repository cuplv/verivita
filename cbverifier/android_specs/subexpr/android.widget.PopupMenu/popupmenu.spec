REGEXP PopupMenu_attached_to_activity_has(act,pop) = [TRUE[*];
	[CI] [ENTRY] [pop] void android.widget.PopupMenu.<init>(act : android.content.Context,# : android.view.View)
	| [CI] [ENTRY] [pop] void android.support.v7.widget.PopupMenu.<init>(act : android.content.Context,# : android.view.View)
;TRUE[*]];

REGEXP PopupMenu_losePrecision(pop) = [FALSE];

REGEXP PopupMenu_listener_registered_just(pop,list) = [TRUE[*] ; 
	[CI] [ENTRY] [pop] void android.widget.PopupMenu.setOnMenuItemClickListener(list : android.widget.PopupMenu$OnMenuItemClickListener)
	| [CI] [ENTRY] [pop] void android.support.v7.widget.PopupMenu.setOnMenuItemClickListener(list : android.support.v7.widget.PopupMenu$OnMenuItemClickListener)
]

