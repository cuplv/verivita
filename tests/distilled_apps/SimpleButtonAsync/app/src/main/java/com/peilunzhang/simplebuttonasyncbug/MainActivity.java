package com.peilunzhang.simplebuttonasyncbug;

import android.os.AsyncTask;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;


public class MainActivity extends AppCompatActivity {

    BgTask t;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Button b = (Button) findViewById(R.id.btn_exec);
        t = new BgTask();
        b.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View view){
                t.execute();
            }
        });

    }

    private class BgTask extends AsyncTask<String, Void, String> {

        @Override
        protected String doInBackground(String... params) {
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            return "Executed";
        }

        @Override
        protected void onPreExecute() {
            Button b = (Button) findViewById(R.id.btn_exec);
            //Should gimme an exception with next line commented
            b.setEnabled(false);
            //b.setVisibility(View.GONE);
            TextView tv = (TextView) findViewById(R.id.text_main);
            tv.setText(R.string.pre_exec_text);


        }
        @Override
        protected void onPostExecute(String result) {
            //Button b = (Button) findViewById(R.id.btn_exec);
            //b.setEnabled(true);
            TextView tv = (TextView) findViewById(R.id.text_main);
            tv.setText(R.string.post_exec_text);

        }
    }
}
