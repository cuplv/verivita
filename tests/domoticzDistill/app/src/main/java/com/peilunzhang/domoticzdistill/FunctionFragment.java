package com.peilunzhang.domoticzdistill;

/**
 * Created by Pezh on 10/11/16.
 */
import android.app.Fragment;
import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.text.Layout;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.Toast;

import android.app.Fragment;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Created by Pezh on 9/14/16.
 */
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

// Request a string response from the provided URL.
        JsonObjectRequest jsonObjectRequest = new JsonObjectRequest(Request.Method.GET, url,  null, new Response.Listener<JSONObject>() {
            @Override
            public void onResponse(JSONObject response) {
                parseJSONResponse(response);

                //FIRST TOAST : SHOULD BE CALLED FIRST
                Toast.makeText(getActivity(), getString(R.string.mainText), Toast.LENGTH_LONG).show();

            }
        }, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                Toast.makeText(getActivity(), getString(R.string.mainText), Toast.LENGTH_LONG).show();
            }
        });

        queue.add(jsonObjectRequest);

    }
    public void parseJSONResponse(JSONObject response) {
        if (response != null || response.length() != 0) {
            try {
                JSONObject GObject = response.getJSONObject("game");
                String name = "N/A";
                if (GObject.has("name") && !GObject.isNull("name")) { name = GObject.getString("name"); }

                if (GObject.has("screenshots") && !GObject.isNull("screenshots")) {
                    JSONArray screenShotsArray = GObject.getJSONArray("screenshots");
                    for (int i = 0; i < screenShotsArray.length(); i++){
                        JSONObject screenshot = screenShotsArray.getJSONObject(i);
                        String screenshotURL = screenshot.getString("url");

                        textMain.setText(screenshotURL);
                    }
                }


            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
    }
}
