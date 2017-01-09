//SPEC FALSE[*] |- [CI] [f] void android.app.Fragment.startActivity(i : android.content.Intent);
//SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
//SPEC TRUE[*];[CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
//SPEC TRUE[*];[CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |- [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity);
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |+ # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
//SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |- # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle)
//SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(# : android.view.LayoutInflater,# : android.view.ViewGroup,# : android.os.Bundle) |+ [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle)
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle)

//TODO: onActivityCreated and onViewStateRestored conditional on init, for now left unspecified
//When added in the below rule will also need to know whether its in the starting cycle.

//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onViewCreated(# : android.view.View,# : android.os.Bundle) |+ [CB] [f] void android.app.Fragment.onStart()
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStart() |- [CB] [f] void android.app.Fragment.onStart()
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onStart() |+ [CB] [f] void android.app.Fragment.onResume();
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onResume() |- [CB] [f] void android.app.Fragment.onResume()
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onResume() |+ [CB] [f] void android.app.Fragment.onPause()
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |- [CB] [f] void android.app.Fragment.onPause()
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |+ [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle)
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onPause() |+ [CB] [f] void android.app.Fragment.onResume()
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onResume() |- [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle)
SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onSaveInstanceState(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onResume()
