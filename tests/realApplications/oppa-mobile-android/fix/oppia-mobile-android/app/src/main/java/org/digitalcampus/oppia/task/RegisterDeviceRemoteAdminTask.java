package org.digitalcampus.oppia.task;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.AsyncTask;
import android.provider.Settings;
import android.util.Log;

import com.splunk.mint.Mint;

import org.apache.http.client.ClientProtocolException;
import org.digitalcampus.oppia.activity.PrefsActivity;
import org.digitalcampus.oppia.application.MobileLearning;
import org.digitalcampus.oppia.utils.HTTPClientUtils;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.io.UnsupportedEncodingException;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class RegisterDeviceRemoteAdminTask extends AsyncTask<Payload, Void, Payload> {

    public static final String TAG = RegisterDeviceRemoteAdminTask.class.getSimpleName();

    private Context ctx;
    private SharedPreferences prefs;

    public RegisterDeviceRemoteAdminTask(Context appContext, SharedPreferences sharedPrefs){
        this.ctx = appContext;
        prefs = sharedPrefs;
    }

    @Override
    protected Payload doInBackground(Payload... args) {

        Payload payload = new Payload();
        boolean success = registerDevice(ctx, prefs);
        payload.setResult(success);
        return payload;
    }

    public static boolean registerDevice(Context ctx, SharedPreferences prefs){

        Log.d(TAG, "Checking if is needed to send the token");
        String username = prefs.getString(PrefsActivity.PREF_USER_NAME, "");
        boolean tokenSent = prefs.getBoolean(PrefsActivity.GCM_TOKEN_SENT, false);
        //If there is no user logged in or the token has already been sent, we exit the task
        if (tokenSent || username.equals("")){
            return false;
        }

        String token = prefs.getString(PrefsActivity.GCM_TOKEN_ID, "");
        String deviceModel = android.os.Build.BRAND + " " + android.os.Build.MODEL;
        String deviceID = Settings.Secure.getString(ctx.getContentResolver(), Settings.Secure.ANDROID_ID);

        Log.d(TAG, "Registering device in remote admin list");
        try {
            JSONObject json = new JSONObject();
            json.put("dev_id", deviceID);
            json.put("reg_id", token);
            json.put("user", username);
            json.put("model_name", deviceModel);

            OkHttpClient client = HTTPClientUtils.getClient(ctx);
            Request request = new Request.Builder()
                    .url(HTTPClientUtils.getFullURL(ctx, MobileLearning.DEVICEADMIN_ADD_PATH))
                    .post(RequestBody.create(HTTPClientUtils.MEDIA_TYPE_JSON, json.toString()))
                    .build();

            Response response = client.newCall(request).execute();
            if (response.isSuccessful()){
                Log.d(TAG, "Successful registration!");
                SharedPreferences.Editor editor = prefs.edit();
                editor.putBoolean(PrefsActivity.GCM_TOKEN_SENT, true).apply();
            }
            else{
                Log.d(TAG, "Bad request");
                return false;
            }

        } catch (UnsupportedEncodingException | ClientProtocolException e) {
            e.printStackTrace();
            Log.d(TAG, e.toString());
        } catch (IOException | JSONException e) {
            e.printStackTrace();
            Mint.logException(e);
        }

        return true;
    }
}
