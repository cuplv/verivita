// onClick is initially disabled
SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);

//Old view attachment detection
//TRUE[*];
//     (
//         b = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int) |
//         (b1 = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int);
//             b = [CI] [EXIT] [#] android.view.View android.view.LayoutInflater.inflate(_ : int,b1 : android.view.ViewGroup,false : boolean) )|
//         (b1 = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int);
//             b2 = [CI] [EXIT] [#] android.view.View android.view.LayoutInflater.inflate(_ : int,b1 : android.view.ViewGroup,false : boolean);
//             b = [CI] [EXIT] [b2] android.view.View android.view.View.findViewById(_ : int))
//
//     );
//Fragment onResume enable
SPEC TRUE[*];
     (container = [CI] [EXIT] [f] android.view.View android.app.Fragment.getView()| [CB] [ENTRY] [f] void android.app.Fragment.onViewCreated(container : android.view.View, # : android.os.Bundle));
     //Attachment chain len 1
     (
         b = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int) | b = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,container : android.view.ViewGroup,false : boolean) 
     )| 

     //Attach chain len 2
     (
         (container2 = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int) | container2 = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,container : android.view.ViewGroup,false : boolean));
         (b = [CI] [EXIT] [container2] android.view.View android.view.View.findViewById(_ : int) | b = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,container2 : android.view.ViewGroup,false : boolean))
     );
     //Attach chain len 3
     (
         (container2 = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int) | container2 = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,container : android.view.ViewGroup,false : boolean));
         (container3 = [CI] [EXIT] [container2] android.view.View android.view.View.findViewById(_ : int) | container3 = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,container2 : android.view.ViewGroup,false : boolean));
         (b = [CI] [EXIT] [container3] android.view.View android.view.View.findViewById(_ : int) | b = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,container3 : android.view.ViewGroup,false : boolean))
     );
     TRUE[*];
     [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
     ( ! [CI] [ENTRY] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
     [CB] [ENTRY] [f] void android.app.Fragment.onResume()  |+ [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(b : android.view.View) 
     ALIASES android.app.Fragment.getView = [android.appFragment.getView,android.support.v4.app.Fragment.getView],
     android.app.Fragment.onViewCreated = [android.support.v4.app.Fragment.onViewCreated,android.app.Fragment.onViewCreated],
     android.app.Fragment.onResume = [android.support.v4.app.Fragment.onResume,android.app.Fragment.onResume]
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



