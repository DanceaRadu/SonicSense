import threading
import time
import numpy as np
from matplotlib import cm
import cv2

class BackgroundMapCalculator:
    def __init__(self, beamformer, user_settings, frame_width, frame_height, update_interval=0.5):

        self.beamformer = beamformer
        self.user_settings = user_settings
        self.update_interval = update_interval
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.bf_map = None
        self.bf_map_unnormalized = None
        self.bf_color = None
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def _run(self):
        while self.running:
            try:
                bf_map = self.beamformer.get_current_map(
                    self.user_settings.get("sound_threshold"),
                    frequency=self.user_settings.get("frequency"),
                    bandwidth=self.user_settings.get("bandwidth")
                )
                unnormalized_bf_map = bf_map.copy()
                bf_map = np.rot90(bf_map, k=-1)
                bf_map = np.flipud(bf_map)
                bf_map = (bf_map - bf_map.min()) / (bf_map.max() - bf_map.min() + 1e-6)
                bf_map = cv2.resize(bf_map, (self.frame_width, self.frame_height))
                bf_color = cm.jet(bf_map)[:, :, :3]
                bf_color = (bf_color * 255).astype(np.uint8)

                with self.lock:
                    self.bf_map = bf_map
                    self.bf_color = bf_color
                    self.bf_map_unnormalized = unnormalized_bf_map
            except Exception as e:
                print(f"[MapCalculator] Error: {e}")

            time.sleep(self.update_interval)

    def get_latest_map(self):
        with self.lock:
            if self.bf_map is not None and self.bf_color is not None:
                return self.bf_map.copy(), self.bf_map_unnormalized.copy(), self.bf_color.copy()
            else:
                return None, None, None
