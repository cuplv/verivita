//Dialog fragment onCreateDialog

SPEC FALSE[*] |- [CB] [ENTRY] [f] android.app.Dialog android.support.v4.app.DialogFragment.onCreateDialog(# : android.os.Bundle);

SPEC TRUE[*]; Fragment_all_onCreate(f) |+ [CB] [ENTRY] [f] android.app.Dialog android.support.v4.app.DialogFragment.onCreateDialog(# : android.os.Bundle);

SPEC TRUE[*]; Fragment_all_onCreateView(f) |- [CB] [ENTRY] [f] android.app.Dialog android.support.v4.app.DialogFragment.onCreateDialog(# : android.os.Bundle)
