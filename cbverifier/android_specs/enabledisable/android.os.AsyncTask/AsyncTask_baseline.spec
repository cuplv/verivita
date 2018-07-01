//SPEC TRUE[*];[CI] [ENTRY] [a] android.os.AsyncTask android.os.AsyncTask.execute(# : java.lang.Object[]) |- [CI] [ENTRY] [a] android.os.AsyncTask android.os.AsyncTask.execute(# : java.lang.Object[]) ;
//SPEC TRUE[*];[CI] [ENTRY] [a] android.os.AsyncTask android.os.AsyncTask.executeOnExecutor(# : java.util.concurrent.Executor,# : java.lang.Object[]) |- [CI] [ENTRY] [a] android.os.AsyncTask android.os.AsyncTask.executeOnExecutor(# : java.util.concurrent.Executor, # : java.lang.Object[])

SPEC FALSE[*] |- [CB] [ENTRY] [a] void android.os.AsyncTask.onPreExecute();
SPEC FALSE[*] |- [CB] [ENTRY] [a] void android.os.AsyncTask.onPostExecute(# : java.lang.Object);
SPEC TRUE[*];[CI] [EXIT] [a] void android.os.AsyncTask.<init>() |- [CI] [EXIT] [a] void android.os.AsyncTask.<init>();
SPEC TRUE[*];[CI] [EXIT] [a] void android.os.AsyncTask.<init>() |+ [CB] [ENTRY] [a] void android.os.AsyncTask.onPreExecute();
//SPEC TRUE[*];[CI] [ENTRY] [a] android.os.AsyncTask android.os.AsyncTask.execute(# : java.lang.Object[]) |+ [CB] [ENTRY] [a] void android.os.AsyncTask.onPreExecute();
//SPEC TRUE[*];[CI] [ENTRY] [a] android.os.AsyncTask android.os.AsyncTask.executeOnExecutor(# : java.util.concurrent.Executor,# : java.lang.Object[]) |+ [CB] [ENTRY] [a] void android.os.AsyncTask.onPreExecute();
SPEC TRUE[*];[CB] [ENTRY] [a] void android.os.AsyncTask.onPreExecute() |- [CB] [ENTRY] [a] void android.os.AsyncTask.onPreExecute();
SPEC TRUE[*];[CB] [ENTRY] [a] void android.os.AsyncTask.onPreExecute() |+ [CB] [ENTRY] [a] void android.os.AsyncTask.onPostExecute(# : java.lang.Object);
SPEC TRUE[*];[CB] [ENTRY] [a] void android.os.AsyncTask.onPostExecute(# : java.lang.Object) |- [CB] [ENTRY] [a] void android.os.AsyncTask.onPostExecute(# : java.lang.Object);
SPEC TRUE[*];[CI] [ENTRY] [a] boolean android.os.AsyncTask.cancel(# : boolean) |- [CB] [ENTRY] [a] void android.os.AsyncTask.onPostExecute(# : java.lang.Object)


