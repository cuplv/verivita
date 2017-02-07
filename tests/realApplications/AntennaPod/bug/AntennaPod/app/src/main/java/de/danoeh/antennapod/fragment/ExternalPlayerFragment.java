package de.danoeh.antennapod.fragment;

import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;

import com.bumptech.glide.Glide;
import com.bumptech.glide.load.engine.DiskCacheStrategy;

import de.danoeh.antennapod.R;
import de.danoeh.antennapod.core.glide.ApGlideSettings;
import de.danoeh.antennapod.core.service.playback.PlaybackService;
import de.danoeh.antennapod.core.util.Converter;
import de.danoeh.antennapod.core.util.playback.Playable;
import de.danoeh.antennapod.core.util.playback.PlaybackController;

/**
 * Fragment which is supposed to be displayed outside of the MediaplayerActivity
 * if the PlaybackService is running
 */
public class ExternalPlayerFragment extends Fragment {
    public static final String TAG = "ExternalPlayerFragment";

    private ViewGroup fragmentLayout;
    private ImageView imgvCover;
    private ViewGroup layoutInfo;
    private TextView txtvTitle;
    private ImageButton butPlay;

    private PlaybackController controller;

    public ExternalPlayerFragment() {
        super();
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View root = inflater.inflate(R.layout.external_player_fragment,
                container, false);
        fragmentLayout = (ViewGroup) root.findViewById(R.id.fragmentLayout);
        imgvCover = (ImageView) root.findViewById(R.id.imgvCover);
        layoutInfo = (ViewGroup) root.findViewById(R.id.layoutInfo);
        txtvTitle = (TextView) root.findViewById(R.id.txtvTitle);
        butPlay = (ImageButton) root.findViewById(R.id.butPlay);

        layoutInfo.setOnClickListener(new OnClickListener() {

            @Override
            public void onClick(View v) {
                Log.d(TAG, "layoutInfo was clicked");

                if (controller != null && controller.getMedia() != null) {
                    startActivity(PlaybackService.getPlayerActivityIntent(
                            getActivity(), controller.getMedia()));
                }
            }
        });
        return root;
    }

    @Override
    public void onActivityCreated(Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
        controller = setupPlaybackController();
        butPlay.setOnClickListener(controller.newOnPlayButtonClickListener());
    }

    private PlaybackController setupPlaybackController() {
        return new PlaybackController(getActivity(), true) {

            @Override
            public void setupGUI() {
            }

            @Override
            public void onPositionObserverUpdate() {
            }

            @Override
            public void onReloadNotification(int code) {
            }

            @Override
            public void onBufferStart() {
            }

            @Override
            public void onBufferEnd() {
            }

            @Override
            public void onBufferUpdate(float progress) {
            }

            @Override
            public void onSleepTimerUpdate() {
            }

            @Override
            public void handleError(int code) {
            }

            @Override
            public ImageButton getPlayButton() {
                return butPlay;
            }

            @Override
            public void postStatusMsg(int msg) {
            }

            @Override
            public void clearStatusMsg() {
            }

            @Override
            public boolean loadMediaInfo() {
                ExternalPlayerFragment fragment = ExternalPlayerFragment.this;
                if (fragment != null) {
                    return fragment.loadMediaInfo();
                } else {
                    return false;
                }
            }

            @Override
            public void onAwaitingVideoSurface() {
            }

            @Override
            public void onServiceQueried() {
            }

            @Override
            public void onShutdownNotification() {
                playbackDone();
            }

            @Override
            public void onPlaybackEnd() {
                playbackDone();
            }

            @Override
            public void onPlaybackSpeedChange() {
            }
        };
    }

    @Override
    public void onResume() {
        super.onResume();
        controller.init();
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "Fragment is about to be destroyed");
        if (controller != null) {
            controller.release();
        }
    }

    @Override
    public void onPause() {
        super.onPause();
        if (controller != null) {
            controller.pause();
        }
    }

    private void playbackDone() {
        if (fragmentLayout != null) {
            fragmentLayout.setVisibility(View.GONE);
        }
        if (controller != null) {
            controller.release();
        }
        controller = setupPlaybackController();
        if (butPlay != null) {
            butPlay.setOnClickListener(controller
                    .newOnPlayButtonClickListener());
        }
        controller.init();
    }

    private boolean loadMediaInfo() {
        Log.d(TAG, "Loading media info");
        if (controller != null && controller.serviceAvailable()) {
            Playable media = controller.getMedia();
            if (media != null) {
                txtvTitle.setText(media.getEpisodeTitle());

                Glide.with(getActivity())
                        .load(media.getImageUri())
                        .placeholder(R.color.light_gray)
                        .error(R.color.light_gray)
                        .diskCacheStrategy(ApGlideSettings.AP_DISK_CACHE_STRATEGY)
                        .fitCenter()
                        .dontAnimate()
                        .into(imgvCover);

                fragmentLayout.setVisibility(View.VISIBLE);
                if (controller.isPlayingVideo()) {
                    butPlay.setVisibility(View.GONE);
                } else {
                    butPlay.setVisibility(View.VISIBLE);
                }
                return true;
            } else {
                Log.w(TAG,  "loadMediaInfo was called while the media object of playbackService was null!");
                return false;
            }
        } else {
            Log.w(TAG, "loadMediaInfo was called while playbackService was null!");
            return false;
        }
    }

    private String getPositionString(int position, int duration) {
        return Converter.getDurationStringLong(position) + " / "
                + Converter.getDurationStringLong(duration);
    }

    public PlaybackController getPlaybackControllerTestingOnly() {
        return controller;
    }
}
