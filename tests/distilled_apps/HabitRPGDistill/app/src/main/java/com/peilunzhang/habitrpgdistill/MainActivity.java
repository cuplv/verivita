package com.peilunzhang.habitrpgdistill;

import android.os.Bundle;

import android.app.Activity;
import android.widget.Button;
import android.widget.LinearLayout;


public class MainActivity extends Activity {


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        LinearLayout mainView = (LinearLayout)this.findViewById(R.id.panel_main);
        Button btn_main= (Button)getLayoutInflater().inflate(R.layout.button_main, mainView);
        mainView.addView(btn_main);
    }


}

