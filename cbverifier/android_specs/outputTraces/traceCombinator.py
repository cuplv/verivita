#g!/\[\d\d*\]\ \[\(CB\|CI\)\]\ \[ENTRY/d

a = [
5048, # [CB] [ENTRY] boolean de.d120.ophasekistenstapeln.MainActivity.dispatchTouchEvent(android.view.MotionEvent) (a4b42a1,ce1f5de)
5308, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment.onAttach(android.app.Activity) (a634044,a4b42a1)
5316, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment.onCreate(android.os.Bundle) (a634044,NULL)
5344, # [CB] [ENTRY] android.view.View de.d120.ophasekistenstapeln.CountdownFragment.onCreateView(android.view.LayoutInflater,android.view.ViewGroup,android.os.Bundle) (a634044,a6b18bd,7c4edc8,NULL)
5820, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment.onActivityCreated(android.os.Bundle) (a634044,NULL)
5845, # [CI] [ENTRY] void android.view.View.setOnClickListener(android.view.View$OnClickListener) (34bd93c,5d05058)
6500, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment$2.onClick(android.view.View) (5d05058,34bd93c)
6517, # [CI] [ENTRY] android.os.CountDownTimer android.os.CountDownTimer.start() (c2fd244)
5816, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment.onViewCreated(android.view.View,android.os.Bundle) (a634044,5195dff,NULL)
5866, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment.onStart() (a634044)
5870, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment.onResume() (a634044)
18294, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment.onPause() (a634044)
17274, # [CB] [ENTRY] void de.d120.ophasekistenstapeln.CountdownFragment$4.onFinish() (c2fd244)
17275 # [CI] [ENTRY] java.lang.String android.app.Fragment.getString(int) (a634044,2131034115)
]
out = ""
for t in a:
	out += str(t) + ":"

print out
