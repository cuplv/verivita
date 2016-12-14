package com.peilunzhang.silence_distill_fix;

import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.Button;

public class MainActivity extends AppCompatActivity {
    Button btn_start;
    Button btn_stop;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        btn_start = (Button) findViewById(R.id.fragmentBtn1);

        final EmptyFragment emp = new EmptyFragment();

        btn_start.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View view){
                getFragmentManager().beginTransaction().replace(R.id.fragment_container, emp).commit();
            };
        });
    }





}
