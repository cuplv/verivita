SPEC FALSE[*] |- [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(# : android.content.DialogInterface,# : int);

//activity just resumed
SPEC (TRUE[*]; AlertDialog_builder_click_reg_just(dialog, clickListener);TRUE[*]) & (TRUE[*];Activity_all_onResume(act)) & (TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*])
 |+ [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int);

//just registered

SPEC (TRUE[*]; AlertDialog_builder_click_reg_just(dialog, clickListener)) & (TRUE[*];Activity_all_onResume(act);TRUE[*]) & (TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*])
  |+ [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int);

//activity just paused
SPEC (TRUE[*]; AlertDialog_builder_click_reg_just(dialog, clickListener)) & (TRUE[*];Activity_all_onPause(act);TRUE[*]) & (TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*])
 |- [CB] [ENTRY] [clickListener] void android.content.DialogInterface$OnClickListener.onClick(dialog : android.content.DialogInterface,# : int)

