SPEC FALSE[*] |- [CB] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; # = [CI] [t] android.os.CountDownTimer android.os.CountDownTimer.start() |+ [CB] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; # = [CI] [t] android.os.CountDownTimer android.os.CountDownTimer.start() |+ [CB] [t] void android.os.CountDownTimer.onTick(l : long);
SPEC TRUE[*]; [CB] [t] void android.os.CountDownTimer.onFinish() |- [CB] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; [CI] [t] void android.os.CountDownTimer.cancel() |- [CB] [t] void android.os.CountDownTimer.onFinish();
SPEC TRUE[*]; [CB] [t] void android.os.CountDownTimer.onFinish() |- [CB] [t] void android.os.CountDownTimer.onTick(l : long)
