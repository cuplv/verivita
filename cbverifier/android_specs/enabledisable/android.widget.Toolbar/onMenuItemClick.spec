SPEC FALSE[*] |- [CB] [ENTRY] [#] boolean android.support.v7.widget.Toolbar$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);

//listener registered enable
SPEC view_attached_has(act,toolbar) &
	Toolbar_listener_registered_just(toolbar,listener) &
	Activity_writ_onResumed_has(act) |+
		[CB] [ENTRY] [listener] boolean android.support.v7.widget.Toolbar$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);


//activity resumed enable
SPEC view_attached_has(act,toolbar) &
	Toolbar_listener_registered_has(toolbar,listener) &
	Activity_writ_onResumed_just(act) |+
		[CB] [ENTRY] [listener] boolean android.support.v7.widget.Toolbar$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);


//activity paused disable
SPEC view_attached_has(act,toolbar) &
	Toolbar_listener_registered_has(toolbar,listener) &
	(TRUE[*];Activity_all_onPause(act)) |-
		[CB] [ENTRY] [listener] boolean android.support.v7.widget.Toolbar$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem)

	


//TRACE swiftnotes manual2

//[7210] [CB] [ENTRY] void com.moonpi.swiftnotes.EditActivity.onResume() (f92b9ff) 
	//class void android.support.v4.app.FragmentActivity.onResume()

//  [6551] [CI] [EXIT] 971a19f = android.view.View android.app.Activity.findViewById(int) (f92b9ff,2131296320)
//[CI] [ENTRY] void android.support.v7.widget.Toolbar.setOnMenuItemClickListener(android.support.v7.widget.Toolbar$OnMenuItemClickListener) (971a19f,f92b9ff)
//[12210] [CB] [ENTRY] boolean com.moonpi.swiftnotes.EditActivity.onMenuItemClick(android.view.MenuItem) (f92b9ff,bbfea64) 
	//interface boolean android.support.v7.widget.Toolbar$OnMenuItemClickListener.onMenuItemClick(android.view.MenuItem)
