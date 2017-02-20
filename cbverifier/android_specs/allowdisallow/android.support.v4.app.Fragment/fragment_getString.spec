//*** Allow Disallow Rules getString ***
SPEC TRUE[*]; [CI] [ENTRY] [f] void android.support.v4.app.Fragment.<init>() |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause() |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(i : int);
SPEC TRUE[*]; [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);

SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int)
