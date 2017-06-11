//*** Allow Disallow Rules getString ***
SPEC TRUE[*]; Fragment_all_init(f) |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);

SPEC TRUE[*]; Fragment_all_onPause(f) |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);
SPEC TRUE[*]; Fragment_all_onCreateView(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);
SPEC TRUE[*]; Fragment_all_onAttach(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);

SPEC TRUE[*]; Fragment_all_onCreate(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);
SPEC TRUE[*]; Fragment_all_onStart(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);
SPEC TRUE[*]; Fragment_all_onResume(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);

//format args version of getString
SPEC TRUE[*]; Fragment_all_init(f) |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);

SPEC TRUE[*]; Fragment_all_onPause(f) |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*]; Fragment_all_onCreateView(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*]; Fragment_all_onAttach(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);

SPEC TRUE[*]; Fragment_all_onCreate(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*]; Fragment_all_onStart(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*]; Fragment_all_onResume(f) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[])
