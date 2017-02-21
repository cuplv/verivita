SPEC TRUE[*]; [CI] [m] void android.media.MediaPlayer.<init>() |- [CI] [m] void android.media.MediaPlayer.start();
SPEC TRUE[*]; [CB] [l] void android.media.MediaPlayer$OnPreparedListener.onPrepared(m : android.media.MediaPlayer) |+ [CI] [m] void android.media.MediaPlayer.start();
SPEC TRUE[*]; [CI] [m] void android.media.MediaPlayer.prepareAsync() |+ [CB] [l] void android.media.MediaPlayer$OnPreparedListener.onPrepared(m : android.media.MediaPlayer);
SPEC FALSE[*] |- [CI] [m] void android.media.MediaPlayer.start()
