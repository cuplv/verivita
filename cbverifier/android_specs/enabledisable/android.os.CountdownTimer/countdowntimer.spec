SPEC FALSE[*] |- [CB] [ENTRY] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; [CI] [ENTRY] [t] android.os.CountDownTimer android.os.CountDownTimer.start() |+ [CB] [ENTRY] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; [CI] [ENTRY] [t] android.os.CountDownTimer android.os.CountDownTimer.start() |+ [CB] [ENTRY] [t] void android.os.CountDownTimer.onTick(l : long);
SPEC TRUE[*]; [CB] [ENTRY] [t] void android.os.CountDownTimer.onFinish() |- [CB] [ENTRY] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; [CI] [ENTRY] [t] void android.os.CountDownTimer.cancel() |- [CB] [ENTRY] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; [CB] [ENTRY] [t] void android.os.CountDownTimer.onFinish() |- [CB] [ENTRY] [t] void android.os.CountDownTimer.onTick(l : long)
