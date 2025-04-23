import collections
import threading
import time
import cv2
import os
import requests
import numpy as np

class VideoEventRecorder:
    def __init__(self, framerate, resolution, backend_url, api_key, buffer_seconds=10, post_seconds=10):
        self.framerate = framerate
        self.frame_width, self.frame_height = resolution
        self.backend_url = backend_url
        self.api_key = api_key

        self.pre_event_frames = collections.deque(maxlen=framerate * buffer_seconds)
        self.post_event_frames = []
        self.post_event_frames_number = post_seconds * framerate

        self.lock = threading.Lock()
        self.recording = False
        self.post_start_time = None

    def update(self, frame, bf_map, event_threshold=2.0):
        if not self.recording:
            self.pre_event_frames.append(frame.copy())

        if not self.recording and self.detect_sound_event(bf_map, event_threshold):
            self.start_post_event_capture()

        if self.recording:
            self.post_event_frames.append(frame.copy())
            if len(self.post_event_frames) > self.post_event_frames_number:
                threading.Thread(target=self._finalize_event, daemon=True).start()
                
    def detect_sound_event(self, bf_map, event_threshold=2.0):
        if bf_map is None:
            return False
        return np.max(bf_map) > event_threshold

    def start_post_event_capture(self):
        with self.lock:
            if self.recording:
                return
            self.recording = True
            self.post_start_time = time.time()
            self.post_event_frames = []

    def _finalize_event(self):
        with self.lock:
            if not self.recording:
                return

            timestamp = int(time.time())
            filename = f"event_{timestamp}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(filename, fourcc, self.framerate, (self.frame_width, self.frame_height))

            for frame in list(self.pre_event_frames) + self.post_event_frames:
                out.write(frame)
            out.release()

            print("Uploading video...")
            self.upload_video(filename)

            self.recording = False
            self.post_event_frames.clear()

    def upload_video(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                files = {'video': f}
                headers = {'X-API-KEY': self.api_key}
                response = requests.post(f"{self.backend_url}/api/sound-events/upload", files=files, headers=headers)

            if response.status_code == 200:
                print("✅ Video uploaded successfully.")
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception during upload: {e}")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
