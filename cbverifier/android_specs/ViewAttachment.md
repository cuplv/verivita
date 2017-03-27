This document is the common location for the regular expressions which state "View v is attached to parent p" where view can be any UI object and parent is an Activity or Fragment

Get container from fragment

```
container = [CI] [EXIT] [f] android.view.View android.app.Fragment.getView()
[CB] [ENTRY] [f] void android.app.Fragment.onViewCreated(container : android.view.View, # : android.os.Bundle))
TRUE[*];
```

Get any attached view from activity including container

```
p = [CI] [EXIT] [activity] android.view.View android.app.Activity.findViewById(_ : int); 
```

Is sub view of another view:

```
p  = [CI] [EXIT] [container] android.view.View android.view.View.findViewById(_ : int);
p = [CI] [EXIT] [#] android.view.View android.view.LayoutInflater.inflate(_ : int,v : android.view.ViewGroup,false : boolean)
```
TODO: addView on "ViewGroup" children

Is not sub view of another view:

TODO: removeView on "ViewGroup" children
