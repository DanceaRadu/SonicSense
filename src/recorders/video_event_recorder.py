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
        self.buffer_frames = framerate * buffer_seconds
        self.post_event_duration = post_seconds
        self.frame_buffer = collections.deque(maxlen=self.buffer_frames)
        self.recording = False
        self.lock = threading.Lock()

    def update(self, frame, bf_map, event_threshold=2.0):
        self.frame_buffer.append(frame.copy())
        
        if not self.recording and self.detect_sound_event(bf_map, event_threshold=event_threshold):
            threading.Thread(target=self._start_recording, daemon=True).start()

    def detect_sound_event(self, bf_map, event_threshold=2.0):
        if bf_map is None:
            return False
        return np.max(bf_map) > event_threshold

    def _start_recording(self):
        with self.lock:
            if self.recording:
                return
            buffered_frames = list(self.frame_buffer)

            self.recording = True
            print("Sound event detected. Starting video recording...")

            timestamp = int(time.time())
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_filename = f"event_{timestamp}.mp4"
            out = cv2.VideoWriter(video_filename, fourcc, self.framerate, (self.frame_width, self.frame_height))

            # Write pre-buffer
            for frame in buffered_frames:
                out.write(frame)

            # Record post-event frames
            start_time = time.time()
            cap = cv2.VideoCapture("/dev/video10", cv2.CAP_V4L2)
            while time.time() - start_time < self.post_event_duration:
                ret, frame = cap.read()
                if ret:
                    out.write(frame)

            out.release()
            cap.release()
            print("Finished recording. Uploading to backend...")
            self.upload_video(video_filename)
            self.recording = False

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
            print("Cleaning up...")
            if os.path.exists(filepath):
                os.remove(filepath)
