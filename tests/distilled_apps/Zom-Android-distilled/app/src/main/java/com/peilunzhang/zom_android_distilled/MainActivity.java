package com.peilunzhang.zom_android_distilled;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.media.MediaRecorder;
import android.net.Uri;
import android.os.Build;
import android.support.annotation.NonNull;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;

import java.io.File;

public class MainActivity extends AppCompatActivity {
    MediaRecorder mMediaRecorder;
    File mAudioFilePath = null;
    boolean mIsAudioRecording = false;
    Button btn_start;
    Button btn_stop;
    int RECORD_AUDIO = 0;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        btn_start = (Button) findViewById(R.id.btn_start);
        btn_stop = (Button) findViewById(R.id.btn_stop);

        final Activity activity = this;

        btn_start.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View view){
                    startAudioRecording();
            };
        });
        btn_stop.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View view){
                stopAudioRecording(false);
            };
        });

    }

    private void startAudioRecording ()
    {
        mMediaRecorder = new MediaRecorder();

        mAudioFilePath = new File(getFilesDir(),"audiotemp.m4a");
        mMediaRecorder.reset();
        mMediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
        mMediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
        mMediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
        mMediaRecorder.setAudioChannels(1);
        mMediaRecorder.setAudioEncodingBitRate(22050);
        mMediaRecorder.setAudioSamplingRate(64000);
        mMediaRecorder.setOutputFile(mAudioFilePath.getAbsolutePath());

        try {
            mIsAudioRecording = true;
            mMediaRecorder.prepare();
            mMediaRecorder.start();
        }
        catch (Exception e)
        {
            Log.e("tag1","couldn't start audio",e);
        }
    }

    public void stopAudioRecording (boolean send)
    {
        if (mMediaRecorder != null && mAudioFilePath != null) {

            mMediaRecorder.stop();

            mMediaRecorder.reset();
            mMediaRecorder.release();

            if (send) {
                Uri uriAudio = Uri.fromFile(mAudioFilePath);
                boolean deleteFile = true;
                boolean resizeImage = false;
                boolean importContent = true;
                //handleSendDelete(uriAudio,"audio/mp4", deleteFile, resizeImage, importContent);
            }
            else
            {
                mAudioFilePath.delete();
            }

            mIsAudioRecording = false;
        }

    }


}
