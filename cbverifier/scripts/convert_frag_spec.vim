"Fragment
%s/\[CB.*onStart()/Fragment_all_onStart(f)/gc
%s/\[CB.*onCreate(.*|/Fragment_all_onCreate(f)\ |/gc
%s/\[CB.*onAttach(.*|/Fragment_all_onAttach(f)\ |/gc
%s/\[CB.*onCreateView(.*)\ |/Fragment_all_onCreateView(f)\ |/gc
%s/\[CB.*onPause()/Fragment_all_onPause(f)/gc
%s/\[CI.*init>()/Fragment_all_init(f)/gc
%s/\[CB.*onResume()/Fragment_all_onResume(f)/gc
%s/\[CB.*onDetach()/Fragment_all_onDetach(f)/gc

"Activity
