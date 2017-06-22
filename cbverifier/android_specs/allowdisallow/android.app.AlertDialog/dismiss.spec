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

SPEC TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*];Activity_all_onPause(act)|- [CI] [ENTRY] [dialog] void android.app.Dialog.dismiss();
SPEC TRUE[*];AlertDialog_attached_to_activity(act,dialog);TRUE[*];Activity_all_onResume(act)|+ [CI] [ENTRY] [dialog] void android.app.Dialog.dismiss()


