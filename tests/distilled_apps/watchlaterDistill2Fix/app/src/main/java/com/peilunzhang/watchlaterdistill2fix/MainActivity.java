package com.peilunzhang.watchlaterdistill2fix;

import android.content.Intent;
import android.os.CountDownTimer;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends AppCompatActivity {
    CountDownTimer cdt;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button firstFragmentBtn = (Button) findViewById(R.id.fragmentBtn1);
        final Intent intent = new Intent(this, SecondActivity.class);
        firstFragmentBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view){
                startActivity(intent);
                finish();
            };
        });

        final TextView textView = new TextView(this);
        textView.setTextSize(40);
        textView.setText("second");
        ViewGroup layout = (ViewGroup) findViewById(R.id.fragment_container);
        layout.addView(textView);

        cdt = new CountDownTimer(10000, 1000) {

            public void onTick(long millisUntilFinished) {
                textView.setText("seconds remaining: " + millisUntilFinished / 1000);
            }

            public void onFinish() {
                textView.setText("Finished");
                getFragmentManager().beginTransaction().replace(R.id.fragment_container, new FunctionFragment()).commit();
            }
        };
        cdt.start();

    }

    @Override
    public void onDestroy(){
        super.onDestroy();
        cdt.cancel();
    }
}
