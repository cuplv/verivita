//*** Enable Disable Rules ***
//Initial disable rules
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle);
SPEC FALSE[*] |-  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle);
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart();
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume();
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause();
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop();
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView();
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroy();
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach();
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onActivityCreated(# : android.os.Bundle);
SPEC FALSE[*] |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity);


SPEC TRUE[*]; [CI] [ENTRY] [f] void android.support.v4.app.Fragment.<init>() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity);


SPEC TRUE[*]; [CI] [EXIT] [f] void android.support.v4.app.Fragment.<init>() |- [CI] [EXIT] [f] void android.support.v4.app.Fragment.<init>();



SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity) |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |+  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*];  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |-  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*];  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(# : android.view.LayoutInflater,# : android.view.ViewGroup,# : android.os.Bundle) |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle);

//TODO: onActivityCreated and onViewStateRestored conditional on init, for now left unspecified
//When added in the below rule will also need to know whether its in the starting cycle.

SPEC TRUE[*];  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(# : android.view.LayoutInflater,# : android.view.ViewGroup,# : android.os.Bundle) |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onActivityCreated(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onActivityCreated(# : android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onActivityCreated(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onActivityCreated(# : android.os.Bundle);


SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle) |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onPause() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onSaveInstanceState(# : android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume();
//SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onSaveInstanceState(# : android.os.Bundle) |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onSaveInstanceState(# : android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop();

//onStop branching control flow
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStop() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView();

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView();


//onDstroyView branching control
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroy();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroyView() |+  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);

SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroy() |-  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*];  [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroy();


SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroy() |- [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroy();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDestroy() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach();
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach() |+ [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach()
