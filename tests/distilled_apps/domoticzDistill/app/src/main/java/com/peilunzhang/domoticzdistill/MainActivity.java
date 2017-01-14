package com.peilunzhang.domoticzdistill;

import android.app.FragmentManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

public class MainActivity extends AppCompatActivity {


    FragmentManager fragmentManager = getFragmentManager();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button firstFragmentBtn = (Button) findViewById(R.id.fragmentBtn1);
        Button secondFragmentBtn = (Button) findViewById(R.id.fragmentBtn2);

        firstFragmentBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view){
                fragmentManager.beginTransaction().
                        replace(R.id.fragment_container, new FunctionFragment()).commit();

            };
        });
        secondFragmentBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view){
                fragmentManager.beginTransaction().
                        replace(R.id.fragment_container, new EmptyFragment()).commit();

            };
        });

    }
}