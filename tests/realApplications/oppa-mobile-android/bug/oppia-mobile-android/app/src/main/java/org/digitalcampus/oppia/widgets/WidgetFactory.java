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

import org.digitalcampus.oppia.model.Activity;
import org.digitalcampus.oppia.model.Course;

import android.content.SharedPreferences;
import android.support.v4.app.Fragment;

public abstract class WidgetFactory extends Fragment {
	
	public final static String TAG = WidgetFactory.class.getSimpleName();
	protected Activity activity = null;
	protected Course course = null;
	protected SharedPreferences prefs;
	protected boolean isBaseline = false;
    protected boolean readAloud = false;

	protected long startTime = 0;
    protected long spentTime = 0;
	protected boolean currentTimeAccounted = false;
	
	public abstract boolean getActivityCompleted();
	public abstract void saveTracker();
	
	public abstract String getContentToRead();
	public abstract HashMap<String,Object> getWidgetConfig();
	public abstract void setWidgetConfig(HashMap<String,Object> config);
	
	public void setReadAloud(boolean readAloud){
		this.readAloud = true;
	}
	
	protected String getDigest() {
		return activity.getDigest();
	}

	public void setIsBaseline(boolean isBaseline) {
		this.isBaseline = isBaseline;
	}
	
	protected void setStartTime(long startTime){
		this.startTime = (startTime != 0) ? startTime : (System.currentTimeMillis()/1000);
        currentTimeAccounted = false;
	}
	
	public long getStartTime(){
		return (startTime != 0) ? startTime : (System.currentTimeMillis()/1000);
	}

    private void addSpentTime(){
        long start = getStartTime();
        long now = System.currentTimeMillis()/1000;

        long spent = now - start;
        spentTime += spent;
        currentTimeAccounted = true;
    }

    public void resetTimeTracking(){
        spentTime = 0;
        startTime = System.currentTimeMillis() / 1000;
        currentTimeAccounted = false;
    }

    public void resumeTimeTracking(){
        startTime = System.currentTimeMillis() / 1000;
        currentTimeAccounted = false;
    }

    public void pauseTimeTracking(){
        addSpentTime();
    }

    public long getSpentTime(){
        if (!currentTimeAccounted){
            addSpentTime();
        }
        return this.spentTime;
    }
}
