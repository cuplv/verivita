SPEC FALSE[*] |- [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(# : android.content.DialogInterface,# : int);

//activity just resumed
SPEC (TRUE[*]; AlertDialog_builder_show_just(dialog, clickListener);TRUE[*]) & (TRUE[*];Activity_all_onResume(act)) & (TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*])
 |+ [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int);


//just registered

//TODO: activity not visible macro replacement
SPEC (TRUE[*]; AlertDialog_builder_show_just(dialog, clickListener)) &  (TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*]) & (TRUE[*]; Activity_all_onResume(act);((!(Activity_all_onPause(act))) & TRUE)[*])
  |+ [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int);

////DEBUG SPEC: TODO REMOVE WHEN DEBUGGED
//SPEC (TRUE[*]; AlertDialog_builder_show_just(dialog, clickListener))  
//  |+ [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int)



//activity just paused
SPEC (TRUE[*]; AlertDialog_builder_show_just(dialog, clickListener);TRUE[*]) & Activity_not_visible_just(act) & (TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*])
 |- [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int);

//show with no activity attached

SPEC (TRUE[*]; AlertDialog_builder_show_just(dialog, clickListener)) & AlertDialog_losePrecision(dialog)
  |+ [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int);

//DialogPreference init Note: DialogPreference itself is a DialogInterface$OnClickListener so just instantiating it registers it, we will add precision later as needed
SPEC TRUE[*];[CB] [ENTRY] [clickListener] void android.preference.DialogPreference.<init>(# : android.content.Context, # : android.util.AttributeSet) |+ [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(# : android.content.DialogInterface,# : int)
