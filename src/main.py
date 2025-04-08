from beamformer_map import BeamformerMap
from utils.helper_service import HelperService
import subprocess
import cv2
import time
import os
import signal
import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np
from matplotlib import cm
import json

class PiCamApp:
    def __init__(self, root):
        self.root = root
        self.settings_path = "user_settings.json"
        self.set_configuration_from_user_settings()

        self.root.title("SonicSense")
        self.root.attributes('-fullscreen', True)
        # self.root.overrideredirect(True)
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.root.update_idletasks()

        HelperService.ensure_v4l2loopback_device_exists()

        # Create GUI components
        self.video_label = ctk.CTkLabel(root, text="")
        self.video_label.pack(fill=ctk.BOTH, expand=True)

        gear_img = Image.open("resources/icons/settings_icon.png")
        gear_img = gear_img.resize((40, 40), Image.Resampling.LANCZOS)
        self.gear_photo = ctk.CTkImage(light_image=gear_img, dark_image=gear_img, size=(40, 40))

        self.settings_button = ctk.CTkButton(
            self.root,
            image=self.gear_photo,
            command=self.open_settings_window,
            text="",
            width=40,
            height=40,
            corner_radius=0
        )
        self.settings_button.place(relx=0.98, rely=0.95, anchor="se")

        # Start the libcamera-vid + ffmpeg pipeline
        self.pipeline_cmd = (
            "libcamera-vid -t 0 --width 4608 --height 2592 --framerate 15 "
            "--codec yuv420 --nopreview -o - | "
            "ffmpeg -f rawvideo -pix_fmt yuv420p -s 4608x2592 -i - "
            "-vf scale=960:540 "
            "-f v4l2 /dev/video10"
        )

        self.pipeline_process = subprocess.Popen(
            self.pipeline_cmd,
            shell=True,
            preexec_fn=os.setsid
        )

        # Give the camera a second to warm up
        time.sleep(2)

        self.video_capture = cv2.VideoCapture("/dev/video10", cv2.CAP_V4L2)
        if not self.video_capture.isOpened():
            print("❌ Could not open /dev/video10")
            self.cleanup()
            exit()

        self.beamformer = BeamformerMap(horizonatal_fov=66, vertical_fov=41, z=0.5, increment=0.02)
        self.frame_count = 0
        self.bf_map = None

        self.update_frame()
        self.root.bind('<Alt-F4>', self.on_close)
        self.root.bind("<Escape>", self.on_close)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_configuration_from_user_settings(self):
        default_config = {
            "sound_threshold": 1.0,
            "frequency": 1000,
            "bandwidth": 1
        }

        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    user_config = json.load(f)
            else:
                user_config = {}

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading user settings: {e}")
            user_config = {}

        self.sound_threshold = user_config.get("sound_threshold", default_config["sound_threshold"])
        self.frequency = user_config.get("frequency", default_config["frequency"])
        self.bandwidth = user_config.get("bandwidth", default_config["bandwidth"])

        merged_config = {
            "sound_threshold": self.sound_threshold,
            "frequency": self.frequency,
            "bandwidth": self.bandwidth
        }
        self.set_user_settings(merged_config)

    def set_user_settings(self, user_settings):
        try:
            with open(self.settings_path, "w") as f:
                json.dump(user_settings, f, indent=4)
        except IOError as e:
            print(f"Failed to save user settings: {e}")

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Update beamformer every N frames (to reduce load)
            if self.frame_count % 3 == 0:
                self.bf_map = self.beamformer.get_current_map(
                    self.sound_threshold, 
                    frequency=self.frequency, 
                    bandwidth=self.bandwidth
                )

            self.frame_count += 1

            if self.bf_map is not None:
                # Normalize and apply colormap
                bf_map = self.bf_map
                bf_map = np.rot90(bf_map, k=-1)
                bf_map = np.fliplr(bf_map)
                bf_map = np.flipud(bf_map)
                bf_map = (bf_map - bf_map.min()) / (bf_map.max() - bf_map.min() + 1e-6)
                bf_map = cv2.resize(bf_map, (frame.shape[1], frame.shape[0]))
                bf_color = cm.jet(bf_map)[:, :, :3]
                bf_color = (bf_color * 255).astype(np.uint8)

                frame = cv2.addWeighted(frame, 0.7, bf_color, 0.3, 0)

            window_width = self.root.winfo_width()
            if window_width <= 1:
                window_width = 800 

            orig_height, orig_width, _ = frame.shape

            aspect_ratio = orig_height / orig_width
            new_width = window_width
            new_height = int(window_width * aspect_ratio)

            resized_frame = cv2.resize(frame, (new_width-2, new_height-2))
            image = Image.fromarray(resized_frame)
            ctk_image = ctk.CTkImage(light_image=image, size=(new_width, new_height))
            self.video_label.configure(image=ctk_image, text="")
            self.video_label.image = ctk_image 

        self.root.after(30, self.update_frame)

    def open_settings_window(self):
        print("Opening settings window...")

    def on_close(self):
        self.cleanup()
        self.root.destroy()

    def cleanup(self):
        print("Cleaning up...")
        if self.video_capture:
            self.video_capture.release()
        os.killpg(os.getpgid(self.pipeline_process.pid), signal.SIGTERM)

if __name__ == "__main__":
    root = ctk.CTk()
    app = PiCamApp(root)
    root.mainloop()
