
// onClick is initially disabled
SPEC FALSE[*] |- [CB] [ENTRY] [l] void android.view.View$OnClickListener.onClick(view : android.view.View);


//setOnClickListener enable
SPEC TRUE[*] ; view_onClick_enabled_set_has(view);view_onClick_listener_set_just(view,listener) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View);

SPEC TRUE[*] ; view_onClick_listener_set_has(view,listener);view_onClick_enabled_set_just(view) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View);

SPEC TRUE[*]; [CI] [ENTRY] [view] void android.widget.TextView.setEnabled(FALSE : boolean) |- [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View);


//onClick litener used in toolbar (just overapprox for now)
SPEC TRUE[*]; [CI] [ENTRY] [toolbar] void android.support.v7.widget.Toolbar.setNavigationOnClickListener(listener : android.view.View$OnClickListener) |+ [CB] [ENTRY] [listener] void android.view.View$OnClickListener.onClick(view : android.view.View)
