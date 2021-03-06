//Debugging rules


//this rule does not find a defect which is a problem
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onResume() |- [CI] [f] void android.app.Fragment.onPause();
//SPEC FALSE[*] |- [CI] [f] void android.app.Fragment.onPause(); 

//*** Allow Disallow Rules Start Activity***
SPEC FALSE[*] |- [CI] [f] void android.app.Fragment.startActivity(i : android.content.Intent);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |- [CI] [f] void android.app.Fragment.startActivity(i : android.content.Intent);
SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];[CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
//All back edges that lead to a running state re enable startActivity
SPEC TRUE[*];[CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |+ [CI] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];[CB] [f] void android.app.Fragment.onStart() |+ [CI] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];[CB] [f] void android.app.Fragment.onResume() |+ [CI] [f] void android.app.Fragment.startActivity(# : android.content.Intent);

//*** Allow Disallow Rules getString ***
SPEC TRUE[*]; [CI] [f] void android.app.Fragment.<init>() |- # = [CI] [f] java.lang.String android.app.Fragment.getString(# : int);

SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |- # = [CI] [f] java.lang.String android.app.Fragment.getString(i : int);
SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ # = [CI] [f] java.lang.String android.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ # = [CI] [f] java.lang.String android.app.Fragment.getString(# : int);

SPEC TRUE[*];[CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |+ # = [CI] [f] java.lang.String android.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [f] void android.app.Fragment.onStart() |+ # = [CI] [f] java.lang.String android.app.Fragment.getString(# : int);
SPEC TRUE[*];[CB] [f] void android.app.Fragment.onResume() |+ # = [CI] [f] java.lang.String android.app.Fragment.getString(# : int);




//*** Enable Disable Rules ***
//Initial disable rules
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
SPEC FALSE[*] |- # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle);
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onStart();
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onResume();
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onPause();
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onStop();
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onDestroyView();
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onDestroy();
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onDetach();
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onActivityCreated(# : android.os.Bundle);
SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity);


SPEC TRUE[*]; [CI] [f] void android.app.Fragment.<init>() |+ [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity);



SPEC TRUE[*];[CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |- [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |+ # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |- # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(# : android.view.LayoutInflater,# : android.view.ViewGroup,# : android.os.Bundle) |+ [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle);

//TODO: onActivityCreated and onViewStateRestored conditional on init, for now left unspecified
//When added in the below rule will also need to know whether its in the starting cycle.

SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(# : android.view.LayoutInflater,# : android.view.ViewGroup,# : android.os.Bundle) |+ [CB] [f] void android.app.Fragment.onActivityCreated(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onActivityCreated(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onActivityCreated(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStart() |- [CB] [f] void android.app.Fragment.onActivityCreated(# : android.os.Bundle);


SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle) |+ [CB] [f] void android.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStart() |- [CB] [f] void android.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStart() |+ [CB] [f] void android.app.Fragment.onResume();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onResume() |- [CB] [f] void android.app.Fragment.onResume();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onResume() |+ [CB] [f] void android.app.Fragment.onPause();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |- [CB] [f] void android.app.Fragment.onPause();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |+ [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |+ [CB] [f] void android.app.Fragment.onResume();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onResume() |- [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onResume();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle) |+ [CB] [f] void android.app.Fragment.onStop();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStop() |- [CB] [f] void android.app.Fragment.onStop();

//onStop branching control flow
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStop() |+ [CB] [f] void android.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStop() |+ [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStop() |+ [CB] [f] void android.app.Fragment.onDestroyView();

SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStart() |- [CB] [f] void android.app.Fragment.onDestroyView();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStart() |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroyView() |- [CB] [f] void android.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroyView() |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onStart();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onDestroyView();


//onDstroyView branching control
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroyView() |- [CB] [f] void android.app.Fragment.onDestroyView();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroyView() |+ [CB] [f] void android.app.Fragment.onDestroy();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroyView() |+ # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);

SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroy() |- # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |- [CB] [f] void android.app.Fragment.onDestroy();


SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroy() |- [CB] [f] void android.app.Fragment.onDestroy();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDestroy() |+ [CB] [f] void android.app.Fragment.onDetach();
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onDetach() |+ [CB] [f] void android.app.Fragment.onDetach()
