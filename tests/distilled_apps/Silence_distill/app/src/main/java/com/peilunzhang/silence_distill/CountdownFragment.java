package com.peilunzhang.silence_distill;

import android.app.Fragment;
import android.app.ListFragment;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

/**
 * Created by Pezh on 9/14/16.
 */
public class CountdownFragment extends Fragment {
    private TextView textMain;
    private CountDownTimer cdt;
    private ListFragment lf;
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        View view = inflater.inflate(R.layout.fragment_countdown, container,
                false);
        lf = new ListFragment();
        return view;
    }
    @Override
    public void onActivityCreated(Bundle savedInstanceState){
        super.onActivityCreated(savedInstanceState);
        textMain = (TextView) getView().findViewById(R.id.textMain);

        cdt = new CountDownTimer(10000, 1000) {

            public void onTick(long millisUntilFinished) {
                textMain.setText("seconds remaining: " + millisUntilFinished / 1000);
            }

            public void onFinish() {
               lf.setListShown(true);
            }
        }.start();
    }
}
