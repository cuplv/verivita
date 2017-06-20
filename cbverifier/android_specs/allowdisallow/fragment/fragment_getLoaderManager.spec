//*** Allow Disallow Rules getString ***
SPEC TRUE[*]; Fragment_all_init(f) |- [CI] [ENTRY] [f] android.app.LoaderManager android.app.Fragment.getLoaderManager();

SPEC TRUE[*]; Fragment_all_onPause(f) |- [CI] [ENTRY] [f] android.app.LoaderManager android.app.Fragment.getLoaderManager();
SPEC TRUE[*]; Fragment_all_onCreateView(f) |+ [CI] [ENTRY] [f] android.app.LoaderManager android.app.Fragment.getLoaderManager();
SPEC TRUE[*]; Fragment_all_onAttach(f) |+ [CI] [ENTRY] [f] android.app.LoaderManager android.app.Fragment.getLoaderManager();

SPEC TRUE[*];Fragment_all_onCreate(f) |+ [CI] [ENTRY] [f] android.app.LoaderManager android.app.Fragment.getLoaderManager();
SPEC TRUE[*];Fragment_all_onStart(f) |+ [CI] [ENTRY] [f] android.app.LoaderManager android.app.Fragment.getLoaderManager();
SPEC TRUE[*];Fragment_all_onResume(f) |+ [CI] [ENTRY] [f] android.app.LoaderManager android.app.Fragment.getLoaderManager()
