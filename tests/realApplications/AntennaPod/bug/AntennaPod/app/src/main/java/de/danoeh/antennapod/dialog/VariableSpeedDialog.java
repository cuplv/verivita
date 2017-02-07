package de.danoeh.antennapod.dialog;

import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.util.Log;
import android.view.View;

import com.afollestad.materialdialogs.DialogAction;
import com.afollestad.materialdialogs.MaterialDialog;

import java.util.Arrays;
import java.util.List;

import de.danoeh.antennapod.R;
import de.danoeh.antennapod.core.preferences.UserPreferences;
import de.danoeh.antennapod.core.util.IntentUtils;

public class VariableSpeedDialog {

	private static final String TAG = VariableSpeedDialog.class.getSimpleName();

	private static final Intent playStoreIntent = new Intent(Intent.ACTION_VIEW,
		Uri.parse("market://details?id=com.falconware.prestissimo"));

	private VariableSpeedDialog() {
	}

	public static void showDialog(final Context context) {
		if (org.antennapod.audio.MediaPlayer.isPrestoLibraryInstalled(context)
			|| UserPreferences.useSonic()) {
			showSpeedSelectorDialog(context);
		} else {
			showGetPluginDialog(context);
		}
	}

	private static void showGetPluginDialog(final Context context) {
		MaterialDialog.Builder builder = new MaterialDialog.Builder(context);
		builder.title(R.string.no_playback_plugin_title);
		builder.content(R.string.no_playback_plugin_or_sonic_msg);
		builder.positiveText(R.string.download_plugin_label);
		builder.negativeText(R.string.enable_sonic);
		builder.neutralText(R.string.close_label);
		builder.callback(new MaterialDialog.ButtonCallback() {
			@Override
			public void onPositive(MaterialDialog dialog) {
				try {
					context.startActivity(playStoreIntent);
				} catch (ActivityNotFoundException e) {
					// this is usually thrown on an emulator if the Android market is not installed
					Log.e(TAG, Log.getStackTraceString(e));
				}
			}

			@Override
			public void onNegative(MaterialDialog dialog) {
				if (Build.VERSION.SDK_INT >= 16) { // just to be safe
					UserPreferences.enableSonic(true);
					showSpeedSelectorDialog(context);
				}
			}

			@Override
			public void onNeutral(MaterialDialog dialog) {
				super.onNeutral(dialog);
			}
		});
		builder.forceStacking(true);
		MaterialDialog dialog = builder.show();
		if(!IntentUtils.isCallable(context.getApplicationContext(), playStoreIntent)) {
			View pos = dialog.getActionButton(DialogAction.POSITIVE);
			pos.setEnabled(false);
		}
		if (Build.VERSION.SDK_INT < 16) {
			View pos = dialog.getActionButton(DialogAction.NEGATIVE);
			pos.setEnabled(false);
		}
	}

	private static void showSpeedSelectorDialog(final Context context) {
		final String[] speedValues = context.getResources().getStringArray(
				R.array.playback_speed_values);
		// According to Java spec these get initialized to false on creation
		final boolean[] speedChecked = new boolean[speedValues.length];

		// Build the "isChecked" array so that multiChoice dialog is
		// populated correctly
		List<String> selectedSpeedList = Arrays.asList(UserPreferences
				.getPlaybackSpeedArray());
		for (int i = 0; i < speedValues.length; i++) {
			speedChecked[i] = selectedSpeedList.contains(speedValues[i]);
		}

		AlertDialog.Builder builder = new AlertDialog.Builder(context);
		builder.setTitle(R.string.set_playback_speed_label);
		builder.setMultiChoiceItems(R.array.playback_speed_values,
			speedChecked, (dialog, which, isChecked) -> {
				speedChecked[which] = isChecked;
			});
		builder.setNegativeButton(android.R.string.cancel, null);
		builder.setPositiveButton(android.R.string.ok,
			(dialog, which) -> {
				int choiceCount = 0;
				for (int i = 0; i < speedChecked.length; i++) {
					if (speedChecked[i]) {
						choiceCount++;
					}
				}
				String[] newSpeedValues = new String[choiceCount];
				int newSpeedIndex = 0;
				for (int i = 0; i < speedChecked.length; i++) {
					if (speedChecked[i]) {
						newSpeedValues[newSpeedIndex++] = speedValues[i];
					}
				}

				UserPreferences.setPlaybackSpeedArray(newSpeedValues);

			});
		builder.create().show();
	}

}
