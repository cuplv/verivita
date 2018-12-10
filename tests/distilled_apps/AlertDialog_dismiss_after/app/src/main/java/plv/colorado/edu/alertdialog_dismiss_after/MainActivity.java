package plv.colorado.edu.alertdialog_dismiss_after;

import android.app.Dialog;
import android.content.DialogInterface;
import android.os.CountDownTimer;
import android.support.v7.app.AlertDialog;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;

public class MainActivity extends AppCompatActivity {
    CountDownTimer dismissDialog = null;
    Dialog d = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setMessage("meh");
        builder.setPositiveButton("hi", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                Log.i("hi","hi");
            }
        });
        builder.setNegativeButton("bye", new DialogInterface.OnClickListener(){

            @Override
            public void onClick(DialogInterface dialog, int which) {
                Log.i("bye","bye");



            }
        });
        d = builder.create();
        d.show();
        dismissDialog = new CountDownTimer(10000,10){

            @Override
            public void onTick(long millisUntilFinished) {

            }

            @Override
            public void onFinish() {
                d.dismiss();
            }
        };
        dismissDialog.start();
    }
    @Override
    protected void onPause(){
        super.onPause();
        dismissDialog.cancel();
        d.cancel();
    }
}
