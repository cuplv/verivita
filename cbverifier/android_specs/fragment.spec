//SPEC FALSE[*] |- [CI] [f] void android.app.Fragment.startActivity(i : android.content.Intent);
//SPEC FALSE[*] |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
//SPEC TRUE[*];[CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CI] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
//SPEC TRUE[*];[CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |- [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity);
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onAttach(# : android.app.Activity) |+ [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |- [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle);
//SPEC TRUE[*]; [CB] [f] void android.app.Fragment.onCreate(# : android.os.Bundle) |+ # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle);
SPEC TRUE[*]; # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle) |- # = [CB] [f] android.view.View android.app.Fragment.onCreateView(#:android.view.LayoutInflater,#:android.view.ViewGroup,#:android.os.Bundle)


