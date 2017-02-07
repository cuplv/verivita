package de.danoeh.antennapod.fragment;

import android.app.Activity;
import android.os.Bundle;
import android.support.v4.app.ListFragment;
import android.util.Log;
import android.view.View;
import android.widget.ListView;

import java.util.List;

import de.danoeh.antennapod.R;
import de.danoeh.antennapod.activity.MainActivity;
import de.danoeh.antennapod.adapter.DownloadedEpisodesListAdapter;
import de.danoeh.antennapod.core.feed.EventDistributor;
import de.danoeh.antennapod.core.feed.FeedItem;
import de.danoeh.antennapod.core.storage.DBReader;
import de.danoeh.antennapod.core.storage.DBWriter;
import rx.Observable;
import rx.Subscription;
import rx.android.schedulers.AndroidSchedulers;
import rx.schedulers.Schedulers;

/**
 * Displays all running downloads and provides a button to delete them
 */
public class CompletedDownloadsFragment extends ListFragment {

    private static final String TAG = CompletedDownloadsFragment.class.getSimpleName();

    private static final int EVENTS =
            EventDistributor.DOWNLOAD_HANDLED |
                    EventDistributor.DOWNLOADLOG_UPDATE |
                    EventDistributor.UNREAD_ITEMS_UPDATE;

    private List<FeedItem> items;
    private DownloadedEpisodesListAdapter listAdapter;

    private boolean viewCreated = false;
    private boolean itemsLoaded = false;

    private Subscription subscription;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        loadItems();
    }

    @Override
    public void onStart() {
        super.onStart();
        EventDistributor.getInstance().register(contentUpdate);
    }

    @Override
    public void onStop() {
        super.onStop();
        EventDistributor.getInstance().unregister(contentUpdate);
        if(subscription != null) {
            subscription.unsubscribe();
        }
    }

    @Override
    public void onDetach() {
        super.onDetach();
        if(subscription != null) {
            subscription.unsubscribe();
        }
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        listAdapter = null;
        viewCreated = false;
        if(subscription != null) {
            subscription.unsubscribe();
        }
    }

    @Override
    public void onAttach(Activity activity) {
        super.onAttach(activity);
        if (viewCreated && itemsLoaded) {
            onFragmentLoaded();
        }
    }

    @Override
    public void onViewCreated(View view, Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        // add padding
        final ListView lv = getListView();
        lv.setClipToPadding(false);
        final int vertPadding = getResources().getDimensionPixelSize(R.dimen.list_vertical_padding);
        lv.setPadding(0, vertPadding, 0, vertPadding);

        viewCreated = true;
        if (itemsLoaded && getActivity() != null) {
            onFragmentLoaded();
        }
    }

    @Override
    public void onListItemClick(ListView l, View v, int position, long id) {
        super.onListItemClick(l, v, position, id);
        FeedItem item = listAdapter.getItem(position - l.getHeaderViewsCount());
        if (item != null) {
            ((MainActivity) getActivity()).loadChildFragment(ItemFragment.newInstance(item.getId()));
        }

    }

    private void onFragmentLoaded() {
        if (listAdapter == null) {
            listAdapter = new DownloadedEpisodesListAdapter(getActivity(), itemAccess);
            setListAdapter(listAdapter);
        }
        setListShown(true);
        listAdapter.notifyDataSetChanged();
    }

    private DownloadedEpisodesListAdapter.ItemAccess itemAccess = new DownloadedEpisodesListAdapter.ItemAccess() {
        @Override
        public int getCount() {
            return (items != null) ? items.size() : 0;
        }

        @Override
        public FeedItem getItem(int position) {
            return (items != null) ? items.get(position) : null;
        }

        @Override
        public void onFeedItemSecondaryAction(FeedItem item) {
            DBWriter.deleteFeedMediaOfItem(getActivity(), item.getMedia().getId());
        }
    };

    private EventDistributor.EventListener contentUpdate = new EventDistributor.EventListener() {
        @Override
        public void update(EventDistributor eventDistributor, Integer arg) {
            if ((arg & EVENTS) != 0) {
                loadItems();
            }
        }
    };

    private void loadItems() {
        if(subscription != null) {
            subscription.unsubscribe();
        }
        if (!itemsLoaded && viewCreated) {
            setListShown(false);
        }
        subscription = Observable.defer(() -> Observable.just(DBReader.getDownloadedItems()))
                .subscribeOn(Schedulers.newThread())
                .observeOn(AndroidSchedulers.mainThread())
                .subscribe(result -> {
                    if (result != null) {
                        items = result;
                        itemsLoaded = true;
                        if (viewCreated && getActivity() != null) {
                            onFragmentLoaded();
                        }
                    }
                }, error -> {
                    Log.e(TAG, Log.getStackTraceString(error));
                });
    }

}
