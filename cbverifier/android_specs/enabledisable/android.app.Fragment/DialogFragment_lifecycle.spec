//Dialog fragment onCreateDialog

SPEC FALSE[*] |- [CB] [ENTRY] [f] android.app.Dialog android.support.v4.app.DialogFragment.onCreateDialog(# : android.os.Bundle);

SPEC TRUE[*]; Fragment_all_onCreate(f) |+ [CB] [ENTRY] [f] android.app.Dialog android.support.v4.app.DialogFragment.onCreateDialog(# : android.os.Bundle)

//based on: home/ubuntu/Documents/data/monkey_traces/fragment-startActivity-traces-2/_traces/martinmarinov-rtl_tcp_andro--bin/monkeyTraces/trace-StreamActivity-debug_2017-04-15_23:15:04.repaired we can't write the following specs
//SPEC TRUE[*]; Fragment_all_onCreateView(f) |- [CB] [ENTRY] [f] android.app.Dialog android.support.v4.app.DialogFragment.onCreateDialog(# : android.os.Bundle);

//SPEC TRUE[*]; Fragment_all_onPause(f) |- [CB] [ENTRY] [f] android.app.Dialog android.support.v4.app.DialogFragment.onCreateDialog(# : android.os.Bundle)
