// setEnabled(true) enables the button click if it has been registered
SPEC TRUE[*];
     [CI] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener);
     ( ! [CI] [b] void android.view.View.setOnClickListener(l2 : android.view.View$OnClickListener) ) [*];
     [CI] [b] void android.widget.TextView.setEnabled(TRUE : boolean) |+ [CB] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);

// if now setEnable(false) is triggered then the onClickListener enables the on Click
SPEC TRUE[*];
     ( ! [CI] [b] void android.widget.TextView.setEnabled(FALSE : boolean))[*];
     [CI] [b] void android.view.View.setOnClickListener(l : android.view.View$OnClickListener)
     |+
      [CB] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);

// setEnabled(false) disables the button regardless of what else has happened
SPEC TRUE[*];
     [CI] [b] void android.widget.TextView.setEnabled(FALSE : boolean) |- [CB] [l] void android.view.View$OnClickListener.onClick(b : android.view.View);

// onClick is initially disabled
SPEC FALSE[*] |- [CB] [l] void android.view.View$OnClickListener.onClick(b : android.view.View)
