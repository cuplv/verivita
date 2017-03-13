#g!/\[\d\d*\]\ \[\(CB\|CI\)\]\ \[ENTRY/d

a = [
6464 #[CB] [ENTRY] boolean de.d120.ophasekistenstapeln.MainActivity.dispatchTouchEvent(android.view.MotionEvent) (a4b42a1,ce1f5de)
]

out = ""
for t in a:
	out += str(t) + ":"

print out
