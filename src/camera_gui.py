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

        # Start the libcamera-vid + ffmpeg pipeline
        self.pipeline_cmd = (
            "libcamera-vid -t 0 --width 1536 --height 864 --framerate 30 "
            "--codec yuv420 --nopreview -o - | "
            "ffmpeg -f rawvideo -pix_fmt yuv420p -s 1536x864 -i - "
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

        self.beamformer = BeamformerMap(horizonatal_fov=66, vertical_fov=41, z=0.3, increment=0.02)
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
                self.bf_map = self.beamformer.get_current_map()

            self.frame_count += 1

            if self.bf_map is not None:
                # Normalize and apply colormap
                bf_map = self.bf_map
                bf_map = np.rot90(bf_map, k=1)
                bf_map = (bf_map - bf_map.min()) / (bf_map.max() - bf_map.min() + 1e-6)
                bf_color = cm.jet(bf_map)[:, :, :3]
                bf_color = (bf_color * 255).astype(np.uint8)
                bf_color = cv2.resize(bf_color, (frame.shape[1], frame.shape[0]))

                # Overlay beamformer heatmap onto video frame
                frame = cv2.addWeighted(frame, 0.6, bf_color, 0.4, 0)

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
