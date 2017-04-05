//view setEnabled
//TODO


// onClick is initially disabled
SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(view : android.view.View);

//Fragment onResume enable

SPEC view_onClick_listener_set_has(view,listener) 
	& may_attached_fragment_is_resumed_just(fragment,view) 
	|+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View)
	ALIASES android.app.Fragment.getView = [android.appFragment.getView,android.support.v4.app.Fragment.getView],
	android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],
	android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume];

//Fragment onPause disable
SPEC view_onClick_listener_set_has(view,listener) & must_attached_fragment_is_paused_just(fragment,view) |-[CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View)
	ALIASES android.app.Fragment.getView = [android.appFragment.getView,android.support.v4.app.Fragment.getView],
	android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],
	android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume];


//Activity onResume enable


//setOnClickListener enable
SPEC may_attached_fragment_is_resumed_has(fragment,view) & view_onClick_listener_set_just(view,listener) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View)
     ALIASES android.app.Fragment.getView = [android.appFragment.getView,android.support.v4.app.Fragment.getView],
     android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],
     android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume]

//





//** old pre REGEXP specs
//Fragment onResume enable
//SPEC TRUE[*];
//     (container = [CI] [EXIT] [f] android.view.View android.app.Fragment.getView()| [CB] [ENTRY] [f] void android.app.Fragment.onViewCreated(container : android.view.View, # : android.os.Bundle)); 
//     TRUE[*];
//     //view_is_attached(container,b);
//     b = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int);
//     TRUE[*];
//     [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
//     ( ! [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
//     [CB] [ENTRY] [f] void android.app.Fragment.onResume()  |+ [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View) 
//     ALIASES android.app.Fragment.getView = [android.appFragment.getView,android.support.v4.app.Fragment.getView],
//     android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],
//     android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume]
//
////Fragment onPause disable
//SPEC TRUE[*];
//     (container = [CI] [EXIT] [f] android.view.View android.app.Fragment.getView()| [CB] [ENTRY] [f] void android.app.Fragment.onViewCreated(container : android.view.View, # : android.os.Bundle));
//     TRUE[*];
//     b = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int);
//     TRUE[*];
//     [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
//     ( ! [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
//     [CB] [ENTRY] [f] void android.app.Fragment.onPause()  |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View)
//     ALIASES
//     android.app.Fragment.getView = [android.appFragment.getView,android.support.v4.app.Fragment.getView],
//     android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],
//     android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume];
//
//
////Activity onResume enable
//SPEC TRUE[*];
//     b = [CI] [EXIT] [activity] android.view.View android.app.Activity.findViewById(_ : int);
//     TRUE[*];
//     [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
//     ( ! [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
//     [CB] [ENTRY] [f] void android.app.Activity.onResume()  |+ [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);
//
//
////Activity onPause disable
//SPEC TRUE[*];
//     b = [CI] [EXIT] [activity] android.view.View android.app.Activity.findViewById(_ : int);
//     TRUE[*];
//     [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
//     ( ! [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
//     [CB] [ENTRY] [f] void android.app.Activity.onPause()  |+ [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View)
//
//
//

//If button comes from new Button() then we assume that it can be clicked anytime after listener registration
//TODO: write this rule     


//Activity onResume enable TODO

//Activity onPause disable TODO





// setEnabled(false) disables the button regardless of what else has happened
//TODO: current language makes it difficult to talk about too many things so we assume that setEnable(false) does not actually disable
//SPEC TRUE[*];



