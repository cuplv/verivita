REGEXP AlertDialogBuilder_init(builder,act) = [([CI] [ENTRY] [builder] void android.support.v7.app.AlertDialog$Builder.<init>(act : android.content.Context))
    | ([CI] [ENTRY] [builder] void android.app.AlertDialog$Builder.<init>(act : android.content.Context))];
REGEXP AlertDialog_create(builder,dialog) = [( dialog = [CI] [EXIT] [builder] android.support.v7.app.AlertDialog android.support.v7.app.AlertDialog$Builder.create())
    | ( dialog = [CI] [EXIT] [builder] android.app.AlertDialog android.app.AlertDialog$Builder.create())];

REGEXP AlertDialog_attached_to_activity(act,dialog) = [(AlertDialogBuilder_init(builder,act);TRUE[*];AlertDialog_create(builder,dialog)) | 
dialog = [CI] [EXIT] [#] android.app.ProgressDialog android.app.ProgressDialog.show(act : android.content.Context, # : java.lang.CharSequence,# : java.lang.CharSequence)
| [CI] [ENTRY] [dialog] void android.app.ProgressDialog.<init>(act : android.content.Context)];

//TODO: this needs the registration from the dialog itself
REGEXP AlertDialog_builder_click_reg_just(dialog, clickListener) = [ 
	([CI] [ENTRY] [builder] android.app.AlertDialog$Builder android.app.AlertDialog$Builder.setPositiveButton(# : int, clickListener : android.content.DialogInterface$OnClickListener) 
		| [CI] [ENTRY] [builder] android.app.AlertDialog$Builder android.app.AlertDialog$Builder.setNegativeButton(# : int,clickListener : android.content.DialogInterface$OnClickListener)); TRUE[*];
	dialog = [CI] [EXIT] [builder] android.app.AlertDialog android.app.AlertDialog$Builder.create()
]
