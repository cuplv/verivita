// onClick is initially disabled
//TODO:
//SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.widget.AdapterView$OnItemClickListener.onItemClick(# : android.widget.AdapterView,# : android.view.View, # : int, # : long);


////Fragment onResume enable
//     listview = [CI] [EXIT] [f] android.widget.ListView android.support.v4.app.ListFragment.getListView();

//( ! [CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l2 : android.widget.AdapterView$OnItemClickListener) ) [*])
SPEC 
     (
     (TRUE[*];[CB] [ENTRY] [f] void android.app.Fragment.onViewCreated(listview2 : android.view.View, # : android.os.Bundle);TRUE[*])
     &
     (TRUE[*];[CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l : android.widget.AdapterView$OnItemClickListener); TRUE[*])
     );
     [CB] [ENTRY] [f] void android.app.Fragment.onResume()  |+ [CB] [ENTRY] [l] void android.widget.AdapterView$OnItemClickListener.onItemClick(listview : android.widget.AdapterView, # : android.view.View, # : int, # : long)
     ALIASES android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume]





//ALIASES android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume];


//Fragment onDetach disable (This will be a common source of bugs as the listview being detached does not prevent the click from happening)
//TODO:
//SPEC TRUE[*];
//     listview = [CI] [EXIT] [f] android.widget.ListView android.support.v4.app.ListFragment.getListView();
//     TRUE[*];
//     [CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l : android.widget.AdapterView$OnItemClickListener);
//     ( ! [CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l2 : android.widget.AdapterView$OnItemClickListener) ) [*];
//     [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach()  |+ [CB] [ENTRY] [l] void android.widget.AdapterView$OnItemClickListener.onItemClick(listview : android.widget.AdapterView, # : android.view.View, # : int, # : long)




//Change listener disable TODO

//If button comes from new Button() then we assume that it can be clicked anytime after listener registration
//TODO: write this rule     


//Activity onResume enable TODO

//Activity onPause disable TODO





// setEnabled(false) disables the button regardless of what else has happened
//TODO: current language makes it difficult to talk about too many things so we assume that setEnable(false) does not actually disable
//SPEC TRUE[*];
//     [CI] [ENTRY] [b] void android.widget.TextView.setEnabled(FALSE : boolean) |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);


