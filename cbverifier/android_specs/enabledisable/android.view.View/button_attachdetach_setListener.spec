// onClick is initially disabled
SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);


//Fragment onResume enable
SPEC TRUE[*];
     container = [CI] [EXIT] [f] android.view.View android.app.Fragment.getView();
     TRUE[*];
     b = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int);
     TRUE[*];
     [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
     ( ! [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
     [CB] [ENTRY] [f] void android.app.Fragment.onResume()  |+ [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);

//Fragment onPause disable
SPEC TRUE[*];
     container = [CI] [EXIT] [f] android.view.View android.app.Fragment.getView();
     TRUE[*];
     b = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int);
     TRUE[*];
     [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
     ( ! [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
     [CB] [ENTRY] [f] void android.app.Fragment.onPause()  |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View)

//Change listener disable TODO

//If button comes from new Button() then we assume that it can be clicked anytime after listener registration
//TODO: write this rule     


//Activity onResume enable TODO

//Activity onPause disable TODO





// setEnabled(false) disables the button regardless of what else has happened
//TODO: current language makes it difficult to talk about too many things so we assume that setEnable(false) does not actually disable
//SPEC TRUE[*];
//     [CI] [ENTRY] [b] void android.widget.TextView.setEnabled(FALSE : boolean) |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);


