// onClick is initially disabled
SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.widget.AdapterView$OnItemClickListener.onItemClick(# : android.widget.AdapterView,# : android.view.View, # : int, # : long);


////Fragment onResume enable
SPEC TRUE[*];
     listview = [CI] [EXIT] [f] android.widget.ListView android.support.v4.app.ListFragment.getListView();
     TRUE[*];
     [CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l : android.widget.AdapterView$OnItemClickListener);
     ( ! [CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l2 : android.widget.AdapterView$OnItemClickListener) ) [*];
     [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onResume()  |+ [CB] [ENTRY] [l] void android.widget.AdapterView$OnItemClickListener.onItemClick(listview : android.widget.AdapterView, # : android.view.View, # : int, # : long);

////Fragment onDetach disable (This will be a common source of bugs as the listview being detached does not prevent the click from happening)
SPEC TRUE[*];
     listview = [CI] [EXIT] [f] android.widget.ListView android.support.v4.app.ListFragment.getListView();
     TRUE[*];
     [CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l : android.widget.AdapterView$OnItemClickListener);
     ( ! [CI] [ENTRY] [listview] void android.widget.AdapterView.setOnItemClickListener( l2 : android.widget.AdapterView$OnItemClickListener) ) [*];
     [CB] [ENTRY] [f] void android.support.v4.app.Fragment.onDetach()  |+ [CB] [ENTRY] [l] void android.widget.AdapterView$OnItemClickListener.onItemClick(listview : android.widget.AdapterView, # : android.view.View, # : int, # : long)




//Change listener disable TODO

//If button comes from new Button() then we assume that it can be clicked anytime after listener registration
//TODO: write this rule     


//Activity onResume enable TODO

//Activity onPause disable TODO





// setEnabled(false) disables the button regardless of what else has happened
//TODO: current language makes it difficult to talk about too many things so we assume that setEnable(false) does not actually disable
//SPEC TRUE[*];
//     [CI] [ENTRY] [b] void android.widget.TextView.setEnabled(FALSE : boolean) |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);

