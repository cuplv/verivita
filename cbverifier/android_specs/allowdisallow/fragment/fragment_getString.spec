//*** Allow Disallow Rules getString ***
SPEC TRUE[*]; [CI] [ENTRY] [f] void android.app.Fragment.<init>() |- [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int);

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.app.Fragment.onPause() |- [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(i : int);
SPEC TRUE[*]; [CB] [ENTRY] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int);

SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onStart() |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onResume() |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int);

//format args version of getString
SPEC TRUE[*]; [CI] [ENTRY] [f] void android.app.Fragment.<init>() |- [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int, # : java.lang.Object[]);

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.app.Fragment.onPause() |- [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(i : int, # : java.lang.Object[]);
SPEC TRUE[*]; [CB] [ENTRY] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int, # : java.lang.Object[]);

SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onStart() |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onResume() |+ [CI] [ENTRY] [f] java.lang.String android.app.Fragment.getString(# : int, # : java.lang.Object[])
