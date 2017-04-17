
REGEXP AlertDialog_show_activity_pause(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onPause())
    | ([CB] [EXIT] [act] void android.app.FragmentActivity.onPause())
    | ([CB] [EXIT] [act] void android.support.v4.app.Activity.onPause())
    | ([CB] [EXIT] [act] void android.app.Activity.onPause())];

REGEXP AlertDialog_show_activity_resume(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onResume())
    | ([CB] [EXIT] [act] void android.app.FragmentActivity.onResume())
    | ([CB] [EXIT] [act] void android.support.v4.app.Activity.onResume())
    | ([CB] [EXIT] [act] void android.app.Activity.onResume())];

REGEXP AlertDialog_show_attached_to_activity(act,dialog) = [(AlertDialogBuilder_init(builder,act);TRUE[*];AlertDialog_create(builder,dialog)) | 
dialog = [CI] [EXIT] [#] android.app.ProgressDialog android.app.ProgressDialog.show(act : android.content.Context, # : java.lang.CharSequence,# : java.lang.CharSequence)];

SPEC TRUE[*];AlertDialog_show_attached_to_activity(act,dialog);TRUE[*];AlertDialog_show_activity_pause(act)|- [CI] [ENTRY] [dialog] void android.app.Dialog.show();
SPEC TRUE[*];AlertDialog_show_attached_to_activity(act,dialog);TRUE[*];AlertDialog_show_activity_resume(act)|+ [CI] [ENTRY] [dialog] void android.app.Dialog.show()


