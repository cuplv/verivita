//Initial disables:
SPEC FALSE[*] |- [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);
SPEC FALSE[*] |- [CB] [ENTRY] [a] void android.app.Activity.onResume();
SPEC FALSE[*] |- [CB] [ENTRY] [a] void android.app.Activity.onPause();
SPEC FALSE[*] |- [CB] [ENTRY] [a] void android.app.Activity.onStop();
SPEC FALSE[*] |- [CB] [ENTRY] [a] void android.app.Activity.onDestroy();


//create start and resume chain
SPEC TRUE[*];[CB] [ENTRY] [a] void android.app.Activity.<init>() |+ [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);
SPEC TRUE[*];[CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);
SPEC TRUE[*];[CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle) |+ [CB] [ENTRY] [a] void android.app.Activity.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStart() |-  [CB] [ENTRY] [a] void android.app.Activity.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStart() |+ [CB] [ENTRY] [a] void android.app.Activity.onResume();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onResume() |- [CB] [ENTRY] [a] void android.app.Activity.onResume();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onResume() |+ [CB] [ENTRY] [a] void android.app.Activity.onPause();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onPause() |- [CB] [ENTRY] [a] void android.app.Activity.onPause();

//Stop branch from pause
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onPause() |+ [CB] [ENTRY] [a] void android.app.Activity.onStop();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |- [CB] [ENTRY] [a] void android.app.Activity.onStop();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onResume() |- [CB] [ENTRY] [a] void android.app.Activity.onStop();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |- [CB] [ENTRY] [a] void android.app.Activity.onResume();

SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |+ [CB] [ENTRY] [a] void android.app.Activity.onDestroy();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |+ [CB] [ENTRY] [a] void android.app.Activity.onRestart();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |+ [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |- [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);

//Resume branch from pause

SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onPause() |+ [CB] [ENTRY] [a] void android.app.Activity.onResume();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onResume() |- [CB] [ENTRY] [a] void android.app.Activity.onStop();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onResume() |- [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);

//Create branch from pause
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onPause() |+ [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);
SPEC TRUE[*];[CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [a] void android.app.Activity.onRestart();
SPEC TRUE[*];[CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [a] void android.app.Activity.onResume();
SPEC TRUE[*];[CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [a] void android.app.Activity.onStop();


//Restart branch from stop
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |+ [CB] [ENTRY] [a] void android.app.Activity.onRestart();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onRestart() |+ [CB] [ENTRY] [a] void android.app.Activity.onStart();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onRestart() |- [CB] [ENTRY] [a] void android.app.Activity.onDestroy();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onRestart() |- [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onRestart() |- [CB] [ENTRY] [a] void android.app.Activity.onRestart();

//Destroy branch from stop
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |+ [CB] [ENTRY] [a] void android.app.Activity.onDestroy();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onDestroy() |- [CB] [ENTRY] [a] void android.app.Activity.onRestart();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onDestroy() |- [CB] [ENTRY] [a] void android.app.Activity.onDestroy();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onDestroy() |- [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);


//Create branch from stop
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onStop() |+ [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle);
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onCreate(# : android.os.Bundle) |- [CB] [ENTRY] [a] void android.app.Activity.onRestart();
SPEC TRUE[*]; [CB] [ENTRY] [a] void android.app.Activity.onCreate() |- [CB] [ENTRY] [a] void android.app.Activity.onDestroy()




