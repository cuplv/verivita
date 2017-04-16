REGEXP AlertDialogBuilder_init_show(builder,act) = [([CI] [ENTRY] [builder] void android.support.v7.app.AlertDialog$Builder.<init>(act : android.content.Context))
    | ([CI] [ENTRY] [builder] void android.app.AlertDialog$Builder.<init>(act : android.content.Context))];
REGEXP AlertDialog_create_show(builder,dialog) = [( dialog = [CI] [EXIT] [builder] android.support.v7.app.AlertDialog android.support.v7.app.AlertDialog$Builder.create())
    | ( dialog = [CI] [EXIT] [builder] android.app.AlertDialog android.app.AlertDialog$Builder.create())];

REGEXP AlertDialog_activity_pause_show(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onPause())
    | ([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onPause())];
REGEXP AlertDialog_activity_resume_show(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onResume())
    | ([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onResume())];


SPEC TRUE[*];AlertDialogBuilder_init_show(builder,act);AlertDialog_create_show(builder,dialog);AlertDialog_activity_pause_show(act)|- [CI] [ENTRY] [dialog] void android.app.Dialog.show();
SPEC TRUE[*];AlertDialogBuilder_init_show(builder,act);AlertDialog_create_show(builder,dialog);AlertDialog_activity_resume_show(act)|+ [CI] [ENTRY] [dialog] void android.app.Dialog.show()
