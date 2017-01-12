package com.ianhanniballake.contractiontimer.ui;

import android.app.AlertDialog;
import android.app.Dialog;
import android.content.AsyncQueryHandler;
import android.content.DialogInterface;
import android.content.DialogInterface.OnClickListener;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.DialogFragment;
import android.support.v4.content.LocalBroadcastManager;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;

import com.google.analytics.tracking.android.EasyTracker;
import com.ianhanniballake.contractiontimer.BuildConfig;
import com.ianhanniballake.contractiontimer.R;
import com.ianhanniballake.contractiontimer.provider.ContractionContract;

/**
 * Reset Confirmation Dialog box
 */
public class ResetDialogFragment extends DialogFragment
{
	/**
	 * Action associated with this fragment closing
	 */
	public final static String RESET_CLOSE_ACTION = "com.ianhanniballake.contractiontimer.RESET_CLOSE";

	@Override
	public void onCancel(final DialogInterface dialog)
	{
		if (BuildConfig.DEBUG)
			Log.d(getClass().getSimpleName(), "Received cancelation event");
		EasyTracker.getTracker().trackEvent("Note", "Cancel", "", 0L);
		super.onCancel(dialog);
	}

	@Override
	public Dialog onCreateDialog(final Bundle savedInstanceState)
	{
		final LayoutInflater inflater = getActivity().getLayoutInflater();
		final View layout = inflater.inflate(R.layout.dialog_reset, null);
		final AsyncQueryHandler asyncQueryHandler = new AsyncQueryHandler(getActivity().getContentResolver())
		{
			// No call backs needed
		};
		return new AlertDialog.Builder(getActivity()).setTitle(R.string.reset_dialog_title).setView(layout)
				.setInverseBackgroundForced(true)
				.setPositiveButton(R.string.reset_dialog_confirm, new OnClickListener()
				{
					@Override
					public void onClick(final DialogInterface dialog, final int which)
					{
						if (BuildConfig.DEBUG)
							Log.d(ResetDialogFragment.this.getClass().getSimpleName(), "Received positive event");
						EasyTracker.getTracker().trackEvent("Reset", "Positive", "", 0L);
						asyncQueryHandler.startDelete(0, 0, ContractionContract.Contractions.CONTENT_URI, null, null);
					}
				}).setNegativeButton(R.string.reset_dialog_cancel, new OnClickListener()
				{
					@Override
					public void onClick(final DialogInterface dialog, final int which)
					{
						if (BuildConfig.DEBUG)
							Log.d(ResetDialogFragment.this.getClass().getSimpleName(), "Received negative event");
						EasyTracker.getTracker().trackEvent("Reset", "Negative", "", 0L);
					}
				}).create();
	}

	@Override
	public void onDismiss(final DialogInterface dialog)
	{
		final LocalBroadcastManager localBroadcastManager = LocalBroadcastManager.getInstance(getActivity());
		localBroadcastManager.sendBroadcast(new Intent(RESET_CLOSE_ACTION));
		super.onDismiss(dialog);
	}
}
