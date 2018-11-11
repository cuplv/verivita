
// onClick is initially disabled
SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(view : android.view.View);


//setOnClickListener enable lose precision
SPEC view_lose_precision_has(view) & view_onClick_enabled_set_has(view) & view_onClick_listener_set_just(view,listener) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(# : android.view.View);

//setEnable enable lose precision
SPEC view_onClick_listener_set_has(view,listener) & view_onClick_enabled_set_just(view) & view_lose_precision_has(view) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(# : android.view.View);


SPEC view_onClick_listener_set_has(view,listener) & view_onClick_enabled_set_has(view) & view_lose_precision_just(view) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(# : android.view.View);


//activity resumed enable
SPEC view_attached_has(act,view) & 
	(TRUE[*]; Activity_all_onResume(act)) & //JUST
	view_onClick_listener_set_has(view,listener) & 
	view_onClick_enabled_set_has(view) 
		|+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(# : android.view.View);


//setOnClickListener enable activity attached and resumed

SPEC view_attached_has(act,view) & 
	(TRUE[*] ; Activity_all_onResume(act) ; ((!Activity_all_onPause(act)) & TRUE)[*]) & 
	view_onClick_listener_set_just(view,listener) & //JUST
	view_onClick_enabled_set_has(view)
		|+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(# : android.view.View);

//setEnable enable lose precision activity attached and resumed TODO
SPEC view_attached_has(act,view) & 
	(TRUE[*] ; Activity_all_onResume(act) ; ((!Activity_all_onPause(act)) & TRUE)[*]) & 
	view_onClick_listener_set_has(view,listener) &
	view_onClick_enabled_set_just(view)
		|+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(# : android.view.View);




//setEnable disable
SPEC TRUE[*]; [CI] [ENTRY] [view] void android.widget.TextView.setEnabled(FALSE : boolean) |- [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View);
//note: possible to have setOnClickListener(null) as disallow, but trace corpus never uses it


//activity pause disable
//Note: I could trigger this off either the listener or the view, the view is more direct so will likely cause fewer simulation problems, the listener is more precise
//Note: starting another activity allows pending clicks to still occur same with finishing
SPEC (TRUE[*]; view_attached_has(act,view)) & 
	((!Activity_startActivity(act,#)) & TRUE)[*] & 
	((!Activity_finish(act)) & TRUE)[*] &
	Activity_startingActivityNotFinishing(act) &
	view_onClick_listener_set_has(view,listener) &
	Activity_not_visible_just(act) |- [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(# : android.view.View);

//lose precision when developer calls this method, why is this even public???
SPEC TRUE[*]; [CI] [ENTRY] [view] boolean android.view.View.performClick() |+[CB] [ENTRY] [#] void android.view.View$OnClickListener.onClick(view : android.view.View)
