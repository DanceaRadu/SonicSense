from beamformer_map import BeamformerMap
from utils.helper_service import HelperService
import subprocess
import cv2
import time
import os
import signal
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from matplotlib import cm

class PiCamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SonicSense")
        HelperService.ensure_v4l2loopback_device()

        # Create GUI components
        self.video_label = tk.Label(root)
        self.video_label.pack()
        self.sound_threshold = 1.0

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

        self.cap = cv2.VideoCapture("/dev/video10", cv2.CAP_V4L2)
        if not self.cap.isOpened():
            print("❌ Could not open /dev/video10")
            self.cleanup()
            exit()

        self.beamformer = BeamformerMap(horizonatal_fov=66, vertical_fov=41, z=0.5, increment=0.02, bandwidth=1)
        self.frame_count = 0
        self.bf_map = None

        self.update_frame()
        self.root.bind('<Alt-F4>', self.on_close)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Update beamformer every N frames (to reduce load)
            if self.frame_count % 3 == 0:
                self.bf_map = self.beamformer.get_current_map(self.sound_threshold)

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
                print(bf_color.shape)
                print(frame.shape)
                print(bf_color.shape)

                # Overlay beamformer heatmap onto video frame
                frame = cv2.addWeighted(frame, 0.7, bf_color, 0.3, 0)

            # Show in Tkinter
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=image)
            self.video_label.imgtk = photo
            self.video_label.configure(image=photo)

        self.root.after(30, self.update_frame)

    def on_close(self):
        self.cleanup()
        self.root.destroy()

    def cleanup(self):
        print("Cleaning up...")
        if self.cap:
            self.cap.release()
        os.killpg(os.getpgid(self.pipeline_process.pid), signal.SIGTERM)

if __name__ == "__main__":
    root = tk.Tk()
    app = PiCamApp(root)
    root.mainloop()
