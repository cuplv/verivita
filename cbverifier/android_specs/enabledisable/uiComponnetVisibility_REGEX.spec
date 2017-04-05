//TODO: Activity
//REGEXP attached_activity_is_resumed_just(activity,view) =
//REGEXP container_on_activity_has


//*** Fragment resume/pause/destroy

REGEXP may_attached_fragment_is_resumed_just(fragment,view) = [((container_on_fragment_has(fragment,container)&view_attached_chain_has(container,view)) | view_lose_precision(view)); [CB] [ENTRY] [fragment] void android.app.Fragment.onResume()];



REGEXP may_attached_fragment_is_resumed_has(fragment,view) = [(TRUE[*];[CB] [ENTRY] [fragment] void android.app.Fragment.onResume();(![CB] [ENTRY] [fragment] void android.app.Fragment.onPause())[*]) & ((container_on_fragment_has(fragment,continer); view_attached_chain_has(container,view)) | view_lose_precision(view) )];

REGEXP must_attached_fragment_is_paused_just(fragment,view) = [((container_on_fragment_has(fragment,container)&view_attached_chain_has(container,view))); [CB] [ENTRY] [fragment] void android.app.Fragment.onPause()];





//*** View attachment

//Fragment attachment

REGEXP container_on_fragment_has(fragment,container)= [TRUE[*];(container = [CI] [EXIT] [fragment] android.view.View android.app.Fragment.getView()| [CB] [ENTRY] [fragment] void android.app.Fragment.onViewCreated(container : android.view.View, # : android.os.Bundle));TRUE[*]]; 


//View attached to parent view
//n = 2
//up to n steps of view attachment
REGEXP view_attached_chain_has(parent,child) = [view_is_attached(parent,child) 
	| (view_is_attached(parent,child1);view_is_attached(child1,child)) 
	];


//TODO: detach and other difficult things should also go here
REGEXP view_lose_precision(view) = [view_is_attached(parent,child1);view_is_attached(child1,child2);view_is_attached(child2,view)];

REGEXP view_is_attached(parent,child) = 
     [TRUE[*];
         (
             child = [CI] [EXIT] [parent] android.view.View android.view.View.findViewById(# : int) | child = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,parent: android.view.ViewGroup,false : boolean) 
         )
     ;TRUE[*]]
