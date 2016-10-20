* IllegalStateException("onMeasure() did not set the" + " measured dimension by calling" + " setMeasuredDimension()")
		* https://github.com/MikeOrtiz/TouchImageView/issues/47
		
		
*  "Fragment already active".
		* https://github.com/HeinrichReimer/material-intro/issues/109
			* B
		* https://github.com/unfoldingWord-dev/ts-android/issues/945
			* B
		* http://stackoverflow.com/questions/10364478/got-exception-fragment-already-active
	
	
* "IllegalStateException: Fragment x is not currently in the FragmentManager"
			* https://github.com/avuton/controldlna/commit/8a2145c6dff6d800c0a88eff46a5b52c758dd5e4
			* B
	
	
ListView.java

*	IllegalStateException("The content of the adapter has changed but " +)
		* https://github.com/YoKeyword/IndexableRecyclerView/issues/7
		* "When calling'addHeaderView' to ListView, Adapter will be converted into HeaderViewAdapter, so when you click back quickly, it crash because itemCount 


* 	Cannot add header view to list -- setAdapter has already been called.
	* https://github.com/toggl/mobile/pull/1492
	* Add MainDrawer HeaderView before setting the adapter



java.lang.IllegalStateException: Content view not yet created

* https://github.com/itkach/aard2-android/issues/6

		private void setBusy(boolean busy) {
        	setListShown(!busy); //*** Exception thrown from here
        	if (!busy) {
            TextView emptyText = ((TextView)emptyView.findViewById(R.id.empty_text));
            String msg = "";
            String query = app.getLookupQuery();
            if (query != null && !query.toString().equals("")) {
                msg = getString(R.string.lookup_nothing_found);
            }
            emptyText.setText(msg);
        	}
   	 	}	
* void setListShown (boolean shown)
*  OnCreateOptionMenu -> setListShown() x
*	
    
 