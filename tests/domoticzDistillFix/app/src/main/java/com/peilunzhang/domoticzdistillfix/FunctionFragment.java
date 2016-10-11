package com.peilunzhang.domoticzdistillfix;

/**
 * Created by Pezh on 10/11/16.
 */

import android.app.Fragment;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.Toast;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;


public class FunctionFragment extends Fragment {
    private TextView textMain;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        View view = inflater.inflate(R.layout.fragment_function, container,
                false);

        return view;
    }
    @Override
    public void onActivityCreated(Bundle savedInstanceState){
        super.onActivityCreated(savedInstanceState);
        textMain = (TextView) getView().findViewById(R.id.textMain);

        RequestQueue queue = Volley.newRequestQueue(getActivity());
        String url ="http://tieba.baidu.com/";

        JsonObjectRequest jsonObjectRequest = new JsonObjectRequest(Request.Method.GET, url,  null, new Response.Listener<JSONObject>() {
            @Override
            public void onResponse(JSONObject response) {
                parseJSONResponse(response);
                if(isAdded()) Toast.makeText(getActivity(), getString(R.string.mainText), Toast.LENGTH_LONG).show();

            }
        }, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                if(isAdded()) Toast.makeText(getActivity(), getString(R.string.mainText), Toast.LENGTH_LONG).show();
            }
        });

        queue.add(jsonObjectRequest);

    }
    public void parseJSONResponse(JSONObject response) {

        String text = "";
        try {
            text = response.getString(null);
        } catch (JSONException e){
            e.printStackTrace();
        }
        textMain.setText(text);
    }
}
