REGEXP AlertDialogBuilder_show_init(builder,act) = [([CI] [ENTRY] [builder] void android.support.v7.app.AlertDialog$Builder.<init>(act : android.content.Context))
    | ([CI] [ENTRY] [builder] void android.app.AlertDialog$Builder.<init>(act : android.content.Context))];
REGEXP AlertDialog_show_create(builder,dialog) = [( dialog = [CI] [EXIT] [builder] android.support.v7.app.AlertDialog android.support.v7.app.AlertDialog$Builder.create())
    | ( dialog = [CI] [EXIT] [builder] android.app.AlertDialog android.app.AlertDialog$Builder.create())];


//REGEXP AlertDialog_show_activity_pause(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onPause())
//    | ([CB] [EXIT] [act] void android.app.FragmentActivity.onPause())
//    | ([CB] [EXIT] [act] void android.support.v4.app.Activity.onPause())
//    | ([CB] [EXIT] [act] void android.app.Activity.onPause())];
//
//REGEXP AlertDialog_show_activity_resume(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onResume())
//    | ([CB] [EXIT] [act] void android.app.FragmentActivity.onResume())
//    | ([CB] [EXIT] [act] void android.support.v4.app.Activity.onResume())
//    | ([CB] [EXIT] [act] void android.app.Activity.onResume())];

REGEXP AlertDialog_show_attached_to_activity(act,dialog) = [(AlertDialogBuilder_show_init(builder,act);TRUE[*];AlertDialog_show_create(builder,dialog)) | 
dialog = [CI] [EXIT] [#] android.app.ProgressDialog android.app.ProgressDialog.show(act : android.content.Context, # : java.lang.CharSequence,# : java.lang.CharSequence)
| [CI] [ENTRY] [dialog] void android.app.ProgressDialog.<init>(act : android.content.Context)];

SPEC TRUE[*];AlertDialog_show_attached_to_activity(act,dialog);TRUE[*];Activity_all_onPause(act)|- [CI] [ENTRY] [dialog] void android.app.Dialog.show();
SPEC TRUE[*];AlertDialog_show_attached_to_activity(act,dialog);TRUE[*];Activity_all_onResume(act)|+ [CI] [ENTRY] [dialog] void android.app.Dialog.show();

SPEC TRUE[*];AlertDialog_show_attached_to_activity(act,dialog);TRUE[*];Activity_all_onCreate(act)|+ [CI] [ENTRY] [dialog] void android.app.Dialog.show();
SPEC TRUE[*];AlertDialog_show_attached_to_activity(act,dialog);TRUE[*];Activity_all_onDestroy(act)|- [CI] [ENTRY] [dialog] void android.app.Dialog.show()

