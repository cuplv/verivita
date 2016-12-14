package com.peilunzhang.ceaselessdistill;

import android.os.Bundle;

import android.app.ActionBar;
import android.app.Activity;
import android.app.Fragment;
import android.app.FragmentManager;
import android.app.FragmentTransaction;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.LinearInterpolator;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.w3c.dom.Text;


public class MainActivity extends Activity {

    private BuggyFragment bf;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button btn = (Button) findViewById(R.id.btn_main);
        btn.setOnClickListener(new View.OnClickListener(){
                @Override
                public void onClick(View view){
                    getFragmentManager().beginTransaction()
                            .add(R.id.fragment_container, new BuggyFragment()).commit();
                }
        });

    }

    public static class BuggyFragment extends Fragment{

        TextView mText;
        @Override
        public void onCreate(Bundle savedInstanceState)
        {
            super.onCreate(savedInstanceState);
        }
        @Override
        public View onCreateView(LayoutInflater inflater, ViewGroup container,
                                 Bundle savedInstanceState) {
            View view = inflater.inflate(R.layout.fragment_main, container,
                    false);
            return view;
        }

        @Override
        public void onActivityCreated(Bundle savedInstanceState){
            LinearLayout note = (LinearLayout) getActivity().findViewById(R.id.notes);

            View tv = getActivity().getLayoutInflater().inflate(R.layout.text_main, note);

            note.addView(tv);

        }
    }
}

