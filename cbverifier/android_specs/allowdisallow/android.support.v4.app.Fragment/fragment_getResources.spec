//*** Allow Disallow Rules getString ***
SPEC TRUE[*]; [CI] [ENTRY] [f] void android.support.v4.app.Fragment.<init>() |- [CI] [ENTRY] [f] android.content.res.Resources android.support.v4.app.Fragment.getResources();

SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] android.content.res.Resources android.support.v4.app.Fragment.getResources();

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach() |- [CI] [ENTRY] [f] android.content.res.Resources android.support.v4.app.Fragment.getResources()

////format args version of getString
//SPEC TRUE[*]; [CI] [ENTRY] [f] void android.support.v4.app.Fragment.<init>() |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
//
//SPEC TRUE[*]; [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
//SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
//
//SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
//SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[]);
//SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragment.getString(# : int, # : java.lang.Object[])
