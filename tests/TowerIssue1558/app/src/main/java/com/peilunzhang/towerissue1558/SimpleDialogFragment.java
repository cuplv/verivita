package com.peilunzhang.towerissue1558;

import android.app.DialogFragment;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
/**
 * Created by Pezh on 9/21/16.
 */
public class SimpleDialogFragment extends DialogFragment{
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        View view = inflater.inflate(R.layout.fragment_simple_dialog, container, false);
        getDialog().setTitle("Simple Dialog");
        return view;
    }
    public void overrideTheMethod(){
        return;
    }
}
