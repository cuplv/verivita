/* 
 * This file is part of OppiaMobile - https://digital-campus.org/
 * 
 * OppiaMobile is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * OppiaMobile is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with OppiaMobile. If not, see <http://www.gnu.org/licenses/>.
 */

package org.digitalcampus.oppia.widgets;

import java.util.HashMap;
import java.util.Locale;

import org.digitalcampus.mobile.learning.R;
import org.digitalcampus.oppia.activity.CourseActivity;
import org.digitalcampus.oppia.activity.PrefsActivity;
import org.digitalcampus.oppia.application.MobileLearning;
import org.digitalcampus.oppia.application.Tracker;
import org.digitalcampus.oppia.model.Activity;
import org.digitalcampus.oppia.model.Course;
import org.digitalcampus.oppia.utils.MetaDataUtils;
import org.json.JSONException;
import org.json.JSONObject;

import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.webkit.WebSettings.PluginState;
import android.webkit.WebViewClient;
import android.widget.LinearLayout.LayoutParams;
import android.widget.TextView;

public class UrlWidget extends WidgetFactory {

	public static final String TAG = UrlWidget.class.getSimpleName();	
	
	public static UrlWidget newInstance(Activity activity, Course course, boolean isBaseline) {
		UrlWidget myFragment = new UrlWidget();

		Bundle args = new Bundle();
		args.putSerializable(Activity.TAG, activity);
		args.putSerializable(Course.TAG, course);
		args.putBoolean(CourseActivity.BASELINE_TAG, isBaseline);
		myFragment.setArguments(args);

		return myFragment;
	}

	public UrlWidget() {

	}
	
	@SuppressWarnings("unchecked")
	@Override
	public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
		prefs = PreferenceManager.getDefaultSharedPreferences(super.getActivity());
		course = (Course) getArguments().getSerializable(Course.TAG);
		activity = (org.digitalcampus.oppia.model.Activity) getArguments().getSerializable(org.digitalcampus.oppia.model.Activity.TAG);
		this.setIsBaseline(getArguments().getBoolean(CourseActivity.BASELINE_TAG));
		View vv = super.getLayoutInflater(savedInstanceState).inflate(R.layout.widget_url, null);
		LayoutParams lp = new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT);
		vv.setLayoutParams(lp);
		vv.setId(activity.getActId());
		if ((savedInstanceState != null) && (savedInstanceState.getSerializable("widget_config") != null)){
			setWidgetConfig((HashMap<String, Object>) savedInstanceState.getSerializable("widget_config"));
		}
		return vv;
	}

	@Override
	public void onActivityCreated(Bundle savedInstanceState) { 
		super.onActivityCreated(savedInstanceState);
		
		// show description if any
		String desc = activity.getDescription(prefs.getString(PrefsActivity.PREF_LANGUAGE, Locale.getDefault().getLanguage()));

		TextView descTV = (TextView) getView().findViewById(R.id.widget_url_description);
		if (desc.length() > 0){
			descTV.setText(desc);
		} else {
			descTV.setVisibility(View.GONE);
		}
		
		WebView wv = (WebView) getView().findViewById(R.id.widget_url_webview);
		int defaultFontSize = Integer.parseInt(prefs.getString(PrefsActivity.PREF_TEXT_SIZE, "16"));
		wv.getSettings().setDefaultFontSize(defaultFontSize);
		wv.getSettings().setJavaScriptEnabled(true);
		wv.setWebViewClient(new WebViewClient() {
	        @Override
	        public boolean shouldOverrideUrlLoading(WebView view, String url)
	        {
	            return false;
	        }
	    });
		wv.loadUrl(activity.getLocation(prefs.getString(PrefsActivity.PREF_LANGUAGE, Locale.getDefault().getLanguage())));
		
		
	}
	
	
	@Override
	public boolean getActivityCompleted() {
		// TODO Auto-generated method stub
		return false;
	}

	@Override
	public void saveTracker(){
		long timetaken = this.getSpentTime();
		if (timetaken < MobileLearning.URL_READ_TIME) {
			return;
		}
		Tracker t = new Tracker(super.getActivity());
		JSONObject obj = new JSONObject();
		
		// add in extra meta-data
		try {
			MetaDataUtils mdu = new MetaDataUtils(super.getActivity());
			obj.put("timetaken", timetaken);
			obj = mdu.getMetaData(obj);
			String lang = prefs.getString(PrefsActivity.PREF_LANGUAGE, Locale.getDefault().getLanguage());
			obj.put("lang", lang);
			// if it's a baseline activity then assume completed
			if(this.isBaseline){
				t.saveTracker(course.getCourseId(), activity.getDigest(), obj, true);
			} else {
				t.saveTracker(course.getCourseId(), activity.getDigest(), obj, this.getActivityCompleted());
			}
		} catch (JSONException e) {
			// Do nothing
		} catch (NullPointerException npe){
			//do nothing
		}
	}

	@Override
	public String getContentToRead() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public HashMap<String, Object> getWidgetConfig() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void setWidgetConfig(HashMap<String, Object> config) {
		// TODO Auto-generated method stub
		
	}

}
