package com.peilunzhang.silence_distill;


import android.app.Fragment;
import android.app.ListFragment;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Created by Pezh on 9/14/16.
 */
public class EmptyFragment extends ListFragment {
    private TextView textMain;
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        View rootView = inflater.inflate(R.layout.fragment_empty, container,
                false);
        View superview = super.onCreateView(inflater, (ViewGroup) rootView, savedInstanceState);
        LinearLayout listContainer = (LinearLayout) rootView.findViewById(R.id.list_container);
        listContainer.addView(superview);

        setListShown(true);

        return rootView;
    }
    @Override
    public void onActivityCreated(Bundle savedInstanceState){
        super.onActivityCreated(savedInstanceState);
        textMain = (TextView) getView().findViewById(android.R.id.empty);
        textMain.setText("Fragment Replaced");
    }
}

