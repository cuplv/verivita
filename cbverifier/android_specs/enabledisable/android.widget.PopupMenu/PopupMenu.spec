SPEC FALSE[*] |- [CB] [ENTRY] [#] boolean android.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);

//Listener registration enable
SPEC (PopupMenu_attached_to_activity_has(act,pop)) & (TRUE[*];Activity_all_onResume(act); ((!(Activity_all_onPause(act))) & TRUE)[*]) & PopupMenu_listener_registered_just(pop,list) |+ [CB] [ENTRY] [list] boolean android.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);

//SPEC (PopupMenu_attached_to_activity_has(act,pop)) & (TRUE[*];Activity_all_onResume(act); (((!(Activity_all_onPause(act)))[*]))) & PopupMenu_listener_registered_just(pop,list) |+ [CB] [ENTRY] [list] boolean android.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);

//Activity resume enable
//TODO: write this when simulation fails because of it

//Activity pause disable
SPEC (PopupMenu_attached_to_activity_has(act,pop)) & (PopupMenu_listener_registered_just(pop,list);TRUE[*]) & (TRUE[*];Activity_all_onPause(act)) |- [CB] [ENTRY] [list] boolean android.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);


//support v7 version

SPEC FALSE[*] |- [CB] [ENTRY] [#] boolean android.support.v7.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);

//Listener registration enable
SPEC (PopupMenu_attached_to_activity_has(act,pop)) & (TRUE[*];Activity_all_onResume(act); ((!(Activity_all_onPause(act))) & TRUE)[*]) & PopupMenu_listener_registered_just(pop,list) |+ [CB] [ENTRY] [list] boolean android.support.v7.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);

//SPEC (PopupMenu_attached_to_activity_has(act,pop)) & (TRUE[*];Activity_all_onResume(act); (((!(Activity_all_onPause(act)))[*]))) & PopupMenu_listener_registered_just(pop,list) |+ [CB] [ENTRY] [list] boolean android.support.v7.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem);

//Activity resume enable
//TODO: write this when simulation fails because of it

//Activity pause disable
SPEC (PopupMenu_attached_to_activity_has(act,pop)) & (PopupMenu_listener_registered_just(pop,list);TRUE[*]) & (TRUE[*];Activity_all_onPause(act)) |- [CB] [ENTRY] [list] boolean android.support.v7.widget.PopupMenu$OnMenuItemClickListener.onMenuItemClick(# : android.view.MenuItem)
