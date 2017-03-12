//*** Allow Disallow Rules getString ***
SPEC TRUE[*]; [CI] [ENTRY] [f] void android.support.v4.app.Fragmentg.<init>() |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int);

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onPause() |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(i : int);
SPEC TRUE[*]; [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragmentg.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int);

SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onCreate(# : android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onStart() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onResume() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int);

//format args version of getString
SPEC TRUE[*]; [CI] [ENTRY] [f] void android.support.v4.app.Fragmentg.<init>() |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int, # : java.lang.Object[]);

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onPause() |- [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(i : int, # : java.lang.Object[]);
SPEC TRUE[*]; [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragmentg.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int, # : java.lang.Object[]);

SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onCreate(# : android.os.Bundle) |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onStart() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int, # : java.lang.Object[]);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragmentg.onResume() |+ [CI] [ENTRY] [f] java.lang.String android.support.v4.app.Fragmentg.getString(# : int, # : java.lang.Object[])
