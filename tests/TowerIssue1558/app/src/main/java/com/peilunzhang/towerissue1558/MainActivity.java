package com.peilunzhang.towerissue1558;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        SimpleDialogFragment sdf = new SimpleDialogFragment(){
            @Override
            public void overrideTheMethod(){
                return;
            }
        };
        sdf.show(getFragmentManager(), "New Dialog");
    }
}
