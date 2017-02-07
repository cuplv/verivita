package de.danoeh.antennapod.fragment;

import android.app.Activity;
import android.content.res.TypedArray;
import android.os.Bundle;
import android.os.Handler;
import android.support.v4.app.ListFragment;
import android.support.v4.util.Pair;
import android.support.v4.view.MenuItemCompat;
import android.util.Log;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.widget.ListView;

import java.util.List;
import java.util.concurrent.atomic.AtomicReference;

import de.danoeh.antennapod.R;
import de.danoeh.antennapod.activity.MainActivity;
import de.danoeh.antennapod.adapter.DefaultActionButtonCallback;
import de.danoeh.antennapod.adapter.FeedItemlistAdapter;
import de.danoeh.antennapod.core.asynctask.DownloadObserver;
import de.danoeh.antennapod.core.feed.EventDistributor;
import de.danoeh.antennapod.core.feed.FeedItem;
import de.danoeh.antennapod.core.feed.FeedMedia;
import de.danoeh.antennapod.core.event.QueueEvent;
import de.danoeh.antennapod.core.service.download.Downloader;
import de.danoeh.antennapod.core.storage.DBReader;
import de.danoeh.antennapod.core.storage.DBWriter;
import de.danoeh.antennapod.core.util.LongList;
import de.greenrobot.event.EventBus;
import rx.Observable;
import rx.Subscription;
import rx.android.schedulers.AndroidSchedulers;
import rx.schedulers.Schedulers;

public class PlaybackHistoryFragment extends ListFragment {

    public static final String TAG = "PlaybackHistoryFragment";

    private static final int EVENTS = EventDistributor.PLAYBACK_HISTORY_UPDATE |
            EventDistributor.PLAYER_STATUS_UPDATE;

    private List<FeedItem> playbackHistory;
    private LongList queue;
    private FeedItemlistAdapter adapter;

    private boolean itemsLoaded = false;
    private boolean viewsCreated = false;

    private AtomicReference<Activity> activity = new AtomicReference<Activity>();

    private DownloadObserver downloadObserver;
    private List<Downloader> downloaderList;

    private Subscription subscription;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setRetainInstance(true);
        setHasOptionsMenu(true);
    }

    @Override
    public void onResume() {
        super.onResume();
        loadItems();
    }

    @Override
    public void onStart() {
        super.onStart();
        EventDistributor.getInstance().register(contentUpdate);
        EventBus.getDefault().register(this);
    }

    @Override
    public void onStop() {
        super.onStop();
        EventDistributor.getInstance().unregister(contentUpdate);
        EventBus.getDefault().unregister(this);
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
        activity.set(null);
    }

    @Override
    public void onAttach(Activity activity) {
        super.onAttach(activity);
        this.activity.set(activity);
        if (downloadObserver != null) {
            downloadObserver.setActivity(activity);
            downloadObserver.onResume();
        }
        if (viewsCreated && itemsLoaded) {
            onFragmentLoaded();
        }
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        adapter = null;
        viewsCreated = false;
        if (downloadObserver != null) {
            downloadObserver.onPause();
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

        viewsCreated = true;
        if (itemsLoaded) {
            onFragmentLoaded();
        }
    }

    @Override
    public void onListItemClick(ListView l, View v, int position, long id) {
        super.onListItemClick(l, v, position, id);
        FeedItem item = adapter.getItem(position - l.getHeaderViewsCount());
        if (item != null) {
            ((MainActivity) getActivity()).loadChildFragment(ItemFragment.newInstance(item.getId()));
        }
    }

    @Override
    public void onCreateOptionsMenu(Menu menu, MenuInflater inflater) {
        super.onCreateOptionsMenu(menu, inflater);
        if (itemsLoaded) {
            MenuItem clearHistory = menu.add(Menu.NONE, R.id.clear_history_item, Menu.CATEGORY_CONTAINER, R.string.clear_history_label);
            MenuItemCompat.setShowAsAction(clearHistory, MenuItemCompat.SHOW_AS_ACTION_IF_ROOM);
            TypedArray drawables = getActivity().obtainStyledAttributes(new int[]{R.attr.content_discard});
            clearHistory.setIcon(drawables.getDrawable(0));
            drawables.recycle();
        }
    }

    @Override
    public void onPrepareOptionsMenu(Menu menu) {
        super.onPrepareOptionsMenu(menu);
        if (itemsLoaded) {
            MenuItem menuItem = menu.findItem(R.id.clear_history_item);
            if (menuItem != null) {
                menuItem.setVisible(playbackHistory != null && !playbackHistory.isEmpty());
            }
        }
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (!super.onOptionsItemSelected(item)) {
            switch (item.getItemId()) {
                case R.id.clear_history_item:
                    DBWriter.clearPlaybackHistory();
                    return true;
                default:
                    return false;
            }
        } else {
            return true;
        }
    }

    public void onEvent(QueueEvent event) {
        Log.d(TAG, "onEvent(" + event + ")");
        loadItems();
    }

    private EventDistributor.EventListener contentUpdate = new EventDistributor.EventListener() {

        @Override
        public void update(EventDistributor eventDistributor, Integer arg) {
            if ((arg & EVENTS) != 0) {
                loadItems();
                getActivity().supportInvalidateOptionsMenu();
            }
        }
    };

    private void onFragmentLoaded() {
        if (adapter == null) {
            // played items shoudln't be transparent for this fragment since, *all* items
            // in this fragment will, by definition, be played. So it serves no purpose and can make
            // it harder to read.
            adapter = new FeedItemlistAdapter(getActivity(), itemAccess, new DefaultActionButtonCallback(activity.get()), true, false);
            setListAdapter(adapter);
            downloadObserver = new DownloadObserver(activity.get(), new Handler(), downloadObserverCallback);
            downloadObserver.onResume();
        }
        setListShown(true);
        adapter.notifyDataSetChanged();
        getActivity().supportInvalidateOptionsMenu();
    }

    private DownloadObserver.Callback downloadObserverCallback = new DownloadObserver.Callback() {
        @Override
        public void onContentChanged(List<Downloader> downloaderList) {
            PlaybackHistoryFragment.this.downloaderList = downloaderList;
            if (adapter != null) {
                adapter.notifyDataSetChanged();
            }
        }
    };

    private FeedItemlistAdapter.ItemAccess itemAccess = new FeedItemlistAdapter.ItemAccess() {
        @Override
        public boolean isInQueue(FeedItem item) {
            return (queue != null) ? queue.contains(item.getId()) : false;
        }

        @Override
        public int getItemDownloadProgressPercent(FeedItem item) {
            if (downloaderList != null) {
                for (Downloader downloader : downloaderList) {
                    if (downloader.getDownloadRequest().getFeedfileType() == FeedMedia.FEEDFILETYPE_FEEDMEDIA
                            && downloader.getDownloadRequest().getFeedfileId() == item.getMedia().getId()) {
                        return downloader.getDownloadRequest().getProgressPercent();
                    }
                }
            }
            return 0;
        }

        @Override
        public int getCount() {
            return (playbackHistory != null) ? playbackHistory.size() : 0;
        }

        @Override
        public FeedItem getItem(int position) {
            return (playbackHistory != null) ? playbackHistory.get(position) : null;
        }
    };

    private void loadItems() {
        if(subscription != null) {
            subscription.unsubscribe();
        }
        subscription = Observable.defer(() -> Observable.just(loadData()))
                .subscribeOn(Schedulers.newThread())
                .observeOn(AndroidSchedulers.mainThread())
                .subscribe(result -> {
                    if (result != null) {
                        playbackHistory = result.first;
                        queue = result.second;
                        itemsLoaded = true;
                        if (viewsCreated) {
                            onFragmentLoaded();
                        }
                    }
                }, error -> {
                    Log.e(TAG, Log.getStackTraceString(error));
                });
    }

    private Pair<List<FeedItem>, LongList> loadData() {
        List<FeedItem> history = DBReader.getPlaybackHistory();
        LongList queue = DBReader.getQueueIDList();
        DBReader.loadAdditionalFeedItemListData(history);
        return Pair.create(history, queue);
    }

}
