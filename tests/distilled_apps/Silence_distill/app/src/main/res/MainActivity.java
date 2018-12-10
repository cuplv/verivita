package com.peilunzhang.android_betterpickers_distill;

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
        btn_stop = (Button) findViewById(R.id.fragmentBtn2);

        final EmptyFragment emp = new EmptyFragment();

        btn_start.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View view){
                getFragmentManager().beginTransaction().add(R.id.fragment_container, emp).
                        addToBackStack("tag").commit();
            };
        });
        btn_stop.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View view){
                getFragmentManager().beginTransaction().remove(emp);
            };
        });

    }





}
