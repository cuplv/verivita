//Addons to the Fragment v4 spec
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.ListFragment.onViewCreated(# : android.view.View,# : android.os.Bundle);
SPEC FALSE[*] |-  [CB] [ENTRY] [f] android.view.View android.support.v4.app.ListFragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView();
SPEC TRUE[*]; [CI] [ENTRY] [f] void android.support.v4.app.ListFragment.<init>() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |+  [CB] [ENTRY] [f] android.view.View android.support.v4.app.ListFragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*];  [CB] [ENTRY] [f] android.view.View android.support.v4.app.ListFragment.onCreateView(# : android.view.LayoutInflater,# : android.view.ViewGroup,# : android.os.Bundle) |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onActivityCreated(# : android.os.Bundle);
SPEC TRUE[*];  [CB] [ENTRY] [f] android.view.View android.support.v4.app.ListFragment.onCreateView(# : android.view.LayoutInflater,# : android.view.ViewGroup,# : android.os.Bundle) |+ [CB] [ENTRY] [f] void android.support.v4.app.ListFragment.onViewCreated(# : android.view.View,# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.ListFragment.onViewCreated(# : android.view.View,# : android.os.Bundle) |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart()
