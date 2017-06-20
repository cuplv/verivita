//*** Allow Disallow Rules Start Activity***
SPEC FALSE[*] |- [CI] [ENTRY] [f] void android.app.Fragment.startActivity(i : android.content.Intent);
SPEC TRUE[*]; Fragment_all_onDetach(f) |- [CI] [ENTRY] [f] void android.app.Fragment.startActivity(i : android.content.Intent);
SPEC TRUE[*]; Fragment_all_onCreateView(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];Fragment_all_onAttach(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
//All back edges that lead to a running state re enable startActivity
SPEC TRUE[*];Fragment_all_onCreate(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];Fragment_all_onStart(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent);
SPEC TRUE[*];Fragment_all_onResume(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent);


//*** Allow Disallow Rules Start Activity (Intent, Bundle)***
SPEC FALSE[*] |- [CI] [ENTRY] [f] void android.app.Fragment.startActivity(i : android.content.Intent,# : android.os.Bundle);
SPEC TRUE[*]; Fragment_all_onDetach(f) |- [CI] [ENTRY] [f] void android.app.Fragment.startActivity(i : android.content.Intent,# : android.os.Bundle);
SPEC TRUE[*]; Fragment_all_onCreateView(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent,# : android.os.Bundle);
SPEC TRUE[*];Fragment_all_onAttach(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent,# : android.os.Bundle);
//All back edges that lead to a running state re enable startActivity
SPEC TRUE[*];Fragment_all_onCreate(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent,# : android.os.Bundle);
SPEC TRUE[*];Fragment_all_onStart(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent,# : android.os.Bundle);
SPEC TRUE[*];Fragment_all_onResume(f) |+ [CI] [ENTRY] [f] void android.app.Fragment.startActivity(# : android.content.Intent,# : android.os.Bundle)
