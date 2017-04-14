
// onClick is initially disabled
SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(view : android.view.View);


//setOnClickListener enable
SPEC  view_onClick_enabled_set_has(view);view_onClick_listener_set_just(view,listener) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View);

SPEC view_onClick_listener_set_has(view,listener);view_onClick_enabled_set_just(view) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View);

SPEC [CI] [ENTRY] [view] void android.widget.TextView.setEnabled(FALSE : boolean) |- [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View)

