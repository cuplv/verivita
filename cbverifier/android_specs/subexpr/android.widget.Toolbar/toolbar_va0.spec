//currently just a placeholder
REGEXP Toolbar_listener_registered_just(toolbar,listener) = [TRUE[*]; [CI] [ENTRY] [toolbar] void android.support.v7.widget.Toolbar.setOnMenuItemClickListener(listener : android.support.v7.widget.Toolbar$OnMenuItemClickListener)];
REGEXP Toolbar_listener_registered_has(toolbar,listener) = [Toolbar_listener_registered_just(toolbar,listener);TRUE[*]]
