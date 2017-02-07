package de.danoeh.antennapod.dialog;

import android.app.Dialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.View;
import android.view.Window;
import android.view.inputmethod.InputMethodManager;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Toast;

import java.util.concurrent.TimeUnit;

import de.danoeh.antennapod.R;

public abstract class SleepTimerDialog extends Dialog {
    
    private static final String TAG = SleepTimerDialog.class.getSimpleName();

    private static final int DEFAULT_SPINNER_POSITION = 1;

    private Context context;
    private String PREF_NAME = "SleepTimerDialog";
    private String PREF_VALUE = "LastValue";
    private String PREF_TIME_UNIT = "LastTimeUnit";
    private String PREF_VIBRATE = "Vibrate";
    private String PREF_SHAKE_TO_RESET = "ShakeToReset";
    private SharedPreferences prefs;

    private EditText etxtTime;
    private Spinner spTimeUnit;
    private CheckBox cbShakeToReset;
    private CheckBox cbVibrate;
    private Button butConfirm;
    private Button butCancel;

    private TimeUnit[] units = { TimeUnit.SECONDS, TimeUnit.MINUTES, TimeUnit.HOURS };

    public SleepTimerDialog(Context context, int titleTextId, int leftButtonTextId) {
        super(context);
        this.context = context;
        prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        String[] spinnerContent = new String[] {
                context.getString(R.string.time_seconds),
                context.getString(R.string.time_minutes),
                context.getString(R.string.time_hours) };

        setContentView(R.layout.time_dialog);
        etxtTime = (EditText) findViewById(R.id.etxtTime);
        spTimeUnit = (Spinner) findViewById(R.id.spTimeUnit);
        cbShakeToReset = (CheckBox) findViewById(R.id.cbShakeToReset);
        cbVibrate = (CheckBox) findViewById(R.id.cbVibrate);
        butConfirm = (Button) findViewById(R.id.butConfirm);
        butCancel = (Button) findViewById(R.id.butCancel);

        setTitle(R.string.set_sleeptimer_label);

        etxtTime.setText(prefs.getString(PREF_VALUE, "15"));
        etxtTime.addTextChangedListener(new TextWatcher() {
            @Override
            public void afterTextChanged(Editable s) {
                checkInputLength(s.length());
            }

            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {
            }

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
            }
        });
        etxtTime.postDelayed(new Runnable() {
            @Override
            public void run() {
                InputMethodManager imm = (InputMethodManager) context.getSystemService(Context.INPUT_METHOD_SERVICE);
                imm.showSoftInput(etxtTime, InputMethodManager.SHOW_IMPLICIT);
            }
        }, 100);

        ArrayAdapter<String> spinnerAdapter = new ArrayAdapter<>(this.getContext(),
                android.R.layout.simple_spinner_item, spinnerContent);
        spinnerAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spTimeUnit.setAdapter(spinnerAdapter);
        int selection = prefs.getInt(PREF_TIME_UNIT, DEFAULT_SPINNER_POSITION);
        spTimeUnit.setSelection(selection);

        cbShakeToReset.setChecked(prefs.getBoolean(PREF_SHAKE_TO_RESET, true));
        cbVibrate.setChecked(prefs.getBoolean(PREF_VIBRATE, true));

        butConfirm.setText(R.string.set_sleeptimer_label);
        butConfirm.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    savePreferences();
                    long input = readTimeMillis();
                    onTimerSet(input, cbShakeToReset.isChecked(), cbVibrate.isChecked());
                    dismiss();
                } catch (NumberFormatException e) {
                    e.printStackTrace();
                    Toast toast = Toast.makeText(context, R.string.time_dialog_invalid_input,
                            Toast.LENGTH_LONG);
                    toast.show();
                }
            }
        });

        butCancel.setText(R.string.cancel_label);
        butCancel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                dismiss();
            }
        });
    }

    private void checkInputLength(int length) {
        if (length > 0) {
            Log.d(TAG, "Length is larger than 0, enabling confirm button");
            butConfirm.setEnabled(true);
        } else {
            Log.d(TAG, "Length is smaller than 0, disabling confirm button");
            butConfirm.setEnabled(false);
        }
    }

    public abstract void onTimerSet(long millis, boolean shakeToReset, boolean vibrate);

    private long readTimeMillis() {
        TimeUnit selectedUnit = units[spTimeUnit.getSelectedItemPosition()];
        long value = Long.valueOf(etxtTime.getText().toString());
        return selectedUnit.toMillis(value);
    }

    private void savePreferences() {
        prefs.edit()
                .putString(PREF_VALUE, etxtTime.getText().toString())
                .putInt(PREF_TIME_UNIT, spTimeUnit.getSelectedItemPosition())
                .putBoolean(PREF_SHAKE_TO_RESET, cbShakeToReset.isChecked())
                .putBoolean(PREF_VIBRATE, cbVibrate.isChecked())
                .apply();
    }

}
