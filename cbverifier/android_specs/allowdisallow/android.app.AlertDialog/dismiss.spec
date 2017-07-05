//Following commented out due to replacing them with subexpr activity
//REGEXP AlertDialog_activity_pause(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onPause())
//    | ([CB] [EXIT] [act] void android.app.FragmentActivity.onPause())
//    | ([CB] [EXIT] [act] void android.support.v4.app.Activity.onPause())
//    | ([CB] [EXIT] [act] void android.app.Activity.onPause())];
//
//REGEXP AlertDialog_activity_resume(act) = [([CB] [EXIT] [act] void android.support.v4.app.FragmentActivity.onResume())
//    | ([CB] [EXIT] [act] void android.app.FragmentActivity.onResume())
//    | ([CB] [EXIT] [act] void android.support.v4.app.Activity.onResume())
//    | ([CB] [EXIT] [act] void android.app.Activity.onResume())];

//These _disallow subexpressions are duplicated here and with dialog subexpressions, this is less than ideal so we should probably think up a better way to organize this later
REGEXP AlertDialogBuilder_init_disallow(builder,act) = [([CI] [ENTRY] [builder] void android.support.v7.app.AlertDialog$Builder.<init>(act : android.content.Context))
	| ([CI] [ENTRY] [builder] void android.app.AlertDialog$Builder.<init>(act : android.content.Context)
)];

REGEXP AlertDialog_create_disallow(builder,dialog) = [( dialog = [CI] [EXIT] [builder] android.support.v7.app.AlertDialog android.support.v7.app.AlertDialog$Builder.create())
	| ( dialog = [CI] [EXIT] [builder] android.app.AlertDialog android.app.AlertDialog$Builder.create())
	| (dialog = [CI] [EXIT] [builder] android.app.AlertDialog android.app.AlertDialog$Builder.show())
];



REGEXP AlertDialog_attached_to_activity_disallow(act,dialog) = [(AlertDialogBuilder_init_disallow(builder,act);TRUE[*];AlertDialog_create_disallow(builder,dialog)) 
	| dialog = [CI] [EXIT] [#] android.app.ProgressDialog android.app.ProgressDialog.show(act : android.content.Context, # : java.lang.CharSequence,# : java.lang.CharSequence)
	| [CI] [ENTRY] [dialog] void android.app.ProgressDialog.<init>(act : android.content.Context)
	| [CI] [ENTRY] [dialog] void android.app.AlertDialog.<init>(act : android.content.Context)
];

SPEC TRUE[*];AlertDialog_attached_to_activity_disallow(act,dialog);TRUE[*];Activity_all_onPause(act)|- [CI] [ENTRY] [dialog] void android.app.Dialog.dismiss();
SPEC TRUE[*];AlertDialog_attached_to_activity_disallow(act,dialog);TRUE[*];Activity_all_onResume(act)|+ [CI] [ENTRY] [dialog] void android.app.Dialog.dismiss()


