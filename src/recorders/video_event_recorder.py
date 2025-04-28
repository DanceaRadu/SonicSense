import collections
import threading
import time
import cv2
import os
import requests
import numpy as np
import wave
import subprocess

class VideoEventRecorder:
    def __init__(self, framerate, resolution, backend_url, api_key, sound_generator, buffer_seconds=10, post_seconds=10):
        self.framerate = framerate
        self.frame_width, self.frame_height = resolution
        self.backend_url = backend_url
        self.api_key = api_key

        self.sound_generator = sound_generator
        self.audio_samples_per_frame = int(sound_generator.sample_freq / self.framerate)

        self.pre_event_frames = collections.deque(maxlen=framerate * buffer_seconds)
        self.pre_event_audio = collections.deque(maxlen=self.audio_samples_per_frame * framerate * buffer_seconds)
        self.post_event_frames = []
        self.post_event_audio = []
        self.post_event_frames_number = post_seconds * framerate

        self.lock = threading.Lock()
        self.recording = False
        self.post_start_time = None

    def update(self, frame, bf_map, event_threshold=2.0):
        if not self.recording:
            self.pre_event_frames.append(frame.copy())
            self.pre_event_audio.append(next(self.sound_generator.result(self.audio_samples_per_frame)).copy())

        if not self.recording and self.detect_sound_event(bf_map, event_threshold):
            self.start_post_event_capture()

        if self.recording:
            self.post_event_frames.append(frame.copy())
            self.pre_event_audio.append(next(self.sound_generator.result(self.audio_samples_per_frame)).copy())
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
            self.post_event_audio = []

    def _finalize_event(self):
        with self.lock:
            if not self.recording:
                return

            timestamp = int(time.time())
            video_filename = f"temp_video_{timestamp}.mp4"
            audio_filename = f"temp_audio_{timestamp}.wav"
            final_filename = f"event_{timestamp}.mp4"

            self.save_video(video_filename)
            self.save_audio(audio_filename)

            try:
                subprocess.run([
                    'ffmpeg', '-y', 
                    '-i', video_filename,
                    '-i', audio_filename,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    final_filename
                ], check=True)

                print("Uploading video...")
                self.upload_video(final_filename)

            except subprocess.CalledProcessError as e:
                print(f"FFmpeg error when combining event audio and video: {e}")

            finally:
                if os.path.exists(video_filename):
                    os.remove(video_filename)
                if os.path.exists(audio_filename):
                    os.remove(audio_filename)
                if os.path.exists(final_filename):
                    os.remove(final_filename)

                self.recording = False
                self.post_event_frames.clear()
                self.post_event_audio.clear()

    def save_video(self, filename):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, self.framerate, (self.frame_width, self.frame_height))

        for frame in list(self.pre_event_frames) + self.post_event_frames:
            out.write(frame)
        out.release()

    def save_audio(self, filename):
        combined_audio = np.concatenate(list(self.pre_event_audio) + self.post_event_audio, axis=0)
        combined_audio = combined_audio.astype(np.int16)

        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.sound_generator.num_channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sound_generator.sample_freq)
            wav_file.writeframes(combined_audio.tobytes())

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
