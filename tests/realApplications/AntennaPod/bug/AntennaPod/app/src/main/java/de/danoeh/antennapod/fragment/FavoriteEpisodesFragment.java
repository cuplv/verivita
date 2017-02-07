package de.danoeh.antennapod.fragment;

import android.content.Context;
import android.os.Bundle;
import android.support.v4.util.Pair;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import java.util.List;

import de.danoeh.antennapod.R;
import de.danoeh.antennapod.core.event.FavoritesEvent;
import de.danoeh.antennapod.core.feed.FeedItem;
import de.danoeh.antennapod.core.storage.DBReader;
import de.danoeh.antennapod.core.storage.DBWriter;
import de.danoeh.antennapod.core.util.LongList;
import de.danoeh.antennapod.core.util.gui.FeedItemUndoToken;
import de.danoeh.antennapod.core.util.gui.UndoBarController;
import de.greenrobot.event.EventBus;


/**
 * Like 'EpisodesFragment' except that it only shows favorite episodes and
 * supports swiping to remove from favorites.
 */

public class FavoriteEpisodesFragment extends AllEpisodesFragment {

    public static final String TAG = "FavoriteEpisodesFrag";

    private static final String PREF_NAME = "PrefFavoriteEpisodesFragment";

    private UndoBarController undoBarController;

    public FavoriteEpisodesFragment() {
        super(false, PREF_NAME);
    }

    public void onEvent(FavoritesEvent event) {
        Log.d(TAG, "onEvent(" + event + ")");
        loadItems();
    }

    @Override
    public void onStart() {
        super.onStart();
        EventBus.getDefault().register(this);
    }

    @Override
    public void onStop() {
        super.onStop();
        EventBus.getDefault().unregister(this);
    }

    @Override
    protected void resetViewState() {
        super.resetViewState();
        undoBarController = null;
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View root = super.onCreateViewHelper(inflater, container, savedInstanceState,
                R.layout.episodes_fragment_with_undo);

        listView.setRemoveListener(which -> {
            Log.d(TAG, "remove(" + which + ")");
            if (subscription != null) {
                subscription.unsubscribe();
            }
            FeedItem item = (FeedItem) listView.getAdapter().getItem(which);

            DBWriter.removeFavoriteItem(item);

            undoBarController.showUndoBar(false,
                    getString(R.string.removed_item), new FeedItemUndoToken(item,
                            which)
            );
        });

        undoBarController = new UndoBarController<FeedItemUndoToken>(root.findViewById(R.id.undobar), new UndoBarController.UndoListener<FeedItemUndoToken>() {

            private final Context context = getActivity();

            @Override
            public void onUndo(FeedItemUndoToken token) {
                if (token != null) {
                    long itemId = token.getFeedItemId();
                    DBWriter.addFavoriteItemById(itemId);
                }
            }

            @Override
            public void onHide(FeedItemUndoToken token) {
                // nothing to do
            }
        });
        return root;
    }

    @Override
    protected Pair<List<FeedItem>,LongList> loadData() {
        List<FeedItem> items;
        items = DBReader.getFavoriteItemsList();
        LongList queuedIds = DBReader.getQueueIDList();
        return Pair.create(items, queuedIds);
    }
}
