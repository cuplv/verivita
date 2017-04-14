//*** Allow Disallow Rules Start Activity***
SPEC FALSE[*] |- [CI] [ENTRY] [f] void android.support.v4.app.Fragment.startActivity(i : android.content.Intent);
SPEC TRUE[*]; [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach() |- [CI] [ENTRY] [f] void android.support.v4.app.Fragment.startActivity(i : android.content.Intent);
SPEC TRUE[*]; [CB] [ENTRY] [f] android.view.View android.support.v4.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |+ [CI] [ENTRY] [f] void android.support.v4.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [ENTRY] [f] void android.support.v4.app.Fragment.startActivity(# : android.content.Intent);
//All back edges that lead to a running state re enable startActivity
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onCreate(# : android.os.Bundle) |+ [CI] [ENTRY] [f] void android.support.v4.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onStart() |+ [CI] [ENTRY] [f] void android.support.v4.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];[CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume() |+ [CI] [ENTRY] [f] void android.support.v4.app.Fragment.startActivity(# : android.content.Intent)

