SPEC TRUE[*];
     [CI] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
     ( ! [CI] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener) ) [*];
     [CI] [b] void android.widget.TextView.setEnabled(1 : boolean) |+ [CB] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);

SPEC TRUE[*];
     ( ! [CI] [b] void android.widget.TextView.setEnabled(0 : boolean))[*];
     [CI] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener)
     |+
      [CB] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);
SPEC TRUE[*];
     [CI] [b] void android.widget.TextView.setEnabled(0 : boolean) |- [CB] [l] void android.view.View$OnClickListener.onClick(b : android.view.View)
