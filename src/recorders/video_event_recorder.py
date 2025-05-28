import collections
import threading
import time
import cv2
import os
import requests
import numpy as np
import wave
import subprocess
import uuid

class VideoEventRecorder:
    def __init__(self, resolution, backend_url, api_key, sound_generator, buffer_seconds=5, post_seconds=5):
        self.frame_width, self.frame_height = resolution
        self.backend_url = backend_url
        self.api_key = api_key
        self.sound_generator = sound_generator
        self.buffer_seconds = buffer_seconds
        self.post_seconds = post_seconds

        self.audio_frequency = sound_generator.sample_freq
        self.audio_samples_for_buffer = int(self.audio_frequency * self.buffer_seconds)

        self.pre_event_frames = collections.deque()
        self.pre_event_audio = collections.deque(maxlen=self.audio_samples_for_buffer)
        self.post_event_frames = []
        self.post_event_audio = []

        self.lock = threading.Lock()
        self.recording = False
        self.post_start_time = None

        self.stop_audio_event = threading.Event()
        self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.audio_thread.start()

    def update(self, frame, bf_map, event_threshold=2.0):

        now = time.time()
        if not self.recording:
            self.pre_event_frames.append((now, frame.copy()))
            self.prune_old_entries(now)

        if not self.recording and self.detect_sound_event(bf_map, event_threshold):
            self.start_post_event_capture()

        if self.recording:
            self.post_event_frames.append((now, frame.copy()))
            if self.post_start_time and (now - self.post_start_time > self.post_seconds): 
                threading.Thread(target=self._finalize_event, daemon=True).start()

    def _audio_loop(self):
        while not self.stop_audio_event.is_set():
            try:
                num_samples = 1000
                samples = next(self.sound_generator.result(num_samples)).copy()

                with self.lock:
                    if self.recording:
                        self.post_event_audio.append(samples)
                    else:
                        self.pre_event_audio.append(samples)
            except Exception as e:
                print(f"Error in audio loop: {e}")
      
    def prune_old_entries(self, now):
        cutoff = now - self.buffer_seconds
        while self.pre_event_frames and self.pre_event_frames[0][0] < cutoff:
            self.pre_event_frames.popleft()
                
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
            self.post_event_frames.clear()
            self.post_event_audio.clear()

    def _finalize_event(self):
        with self.lock:
            if not self.recording:
                return
            self.recording = False
            self.stop_audio_event.set()

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
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-ac', '2', 
                    '-movflags', 'faststart',
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

                self.post_start_time = None
                self.post_event_frames.clear()
                self.post_event_audio.clear()
                self.pre_event_frames.clear()
                self.pre_event_audio.clear()

                self.stop_audio_event = threading.Event()
                self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
                self.audio_thread.start()

    def save_video(self, filename):
        all_frames = list(self.pre_event_frames) + self.post_event_frames
        if not all_frames:
            print("No frames to save.")
            return
        avg_fps = self.calculate_average_fps(all_frames)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(script_dir, f"temp_frames_{uuid.uuid4().hex}")
        os.makedirs(folder, exist_ok=True)

        input_txt_path = os.path.join(folder, "frames.txt")
        with open(input_txt_path, 'w') as f:
            for i, (timestamp, frame) in enumerate(all_frames):
                frame_path = os.path.join(folder, f"frame_{i:04d}.png")
                success = cv2.imwrite(frame_path, frame)
                if not success:
                    print(f"Failed to write frame to {frame_path}")
                    continue
                f.write(f"file '{frame_path}'\n")
                if i > 0:
                    prev_timestamp = all_frames[i - 1][0]
                    duration = timestamp - prev_timestamp
                    f.write(f"duration {duration:.6f}\n")

            if len(all_frames) > 1:
                duration = all_frames[-1][0] - all_frames[-2][0]
                f.write(f"duration {duration:.6f}\n")

        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-r', str(round(avg_fps, 3)),
                '-f', 'concat', '-safe', '0',
                '-i', input_txt_path,
                '-fps_mode', 'vfr',
                '-pix_fmt', 'yuv420p',
                filename
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error while creating video: {e}")
        finally:
            import shutil
            shutil.rmtree(folder)

    def save_audio(self, filename):
        combined_audio = np.concatenate(list(self.pre_event_audio) + self.post_event_audio, axis=0)
        combined_audio = combined_audio.astype(np.int16)

        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.sound_generator.num_channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.audio_frequency)
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

    def calculate_average_fps(self, frames):
        timestamps = [ts for ts, _ in frames]
        if len(timestamps) < 2:
            return 5.0

        durations = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
        avg_duration = sum(durations) / len(durations)
        return 1.0 / avg_duration if avg_duration > 0 else 5.0
    
    def stop(self):
        self.stop_audio_event.set()
