//TODO: Activity
//REGEXP attached_activity_is_resumed_just(activity,view) =
//REGEXP container_on_activity_has


REGEXP attached_fragment_is_resumed_just(fragment,view) = [container_on_fragment_has(fragment,container);view_attached_chain_has(container,view)];


REGEXP container_on_fragment_has(fragment,container)= [TRUE[*];(container = [CI] [EXIT] [f] android.view.View android.app.Fragment.getView()| [CB] [ENTRY] [f] void android.app.Fragment.onViewCreated(container : android.view.View, # : android.os.Bundle));TRUE[*]]; 

//Other ways views can come from fragments eg: listFragment's getListView
//TODO: fill this out
//REGEXP fragment_special_attachment_method_has(fragment,view) = [FALSE];


//n = 1
//up to n steps of view attachment
REGEXP view_attached_chain_has(parent,child) = [TRUE[*];view_is_attached(parent,child);TRUE[*]];

//n+1 steps stating that its too deep
//TODO: add this later
//REGEXP view_too_deep_has(child) = [FALSE];

//one step of view is attached to another view
//TODO: view adding/removing
//TODO: list items
REGEXP view_is_attached(parent,child) = 
     [
         (
             child = [CI] [EXIT] [parent] android.view.View android.view.View.findViewById(_ : int) | child = [CI] [EXIT] android.view.View android.view.LayoutInflater.inflate(# : int,parent: android.view.ViewGroup,false : boolean) 
         )
     ]
