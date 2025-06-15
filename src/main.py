from beamformer_map import BeamformerMap
from utils.helper_service import HelperService
import subprocess
import cv2
import time
import os
import signal
import customtkinter as ctk
from PIL import Image
import json
from components.settings_window import SettingsWindow
import threading
from webrtc_tracks import OpenCVVideoStreamTrack
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCIceCandidate
import websockets
from recorders.video_event_recorder import VideoEventRecorder
from background_map_calculator import BackgroundMapCalculator
from user_settings import UserSettings

class SonicSenseApp:
    def __init__(self, root):
        self.root = root
        self.settings = UserSettings("user_settings.json")

        self.frame_width = 960
        self.frame_height = 540
        self.displayed_frame_width = 960
        self.displayed_frame_height = 540
        self.framerate = 15
        self.signaling_url = "wss://sonic-sense-signaling.gonemesis.org"
        self.backend_url = "https://sonic-sense-backend.gonemesis.org"
        self.backend_api_key = ""
        self.set_root_attributes()

        HelperService.ensure_v4l2loopback_device_exists()

        # GUI elements
        self.video_label = ctk.CTkLabel(root, text="")
        self.video_label.pack(fill=ctk.BOTH, expand=True)
        self.settings_window = None
        self.settings_button = self.create_settings_button()
        self.settings_button.place(relx=0.98, rely=0.95, anchor="se")

        self.update_count = 1

        self.max_value_label = ctk.CTkLabel(self.root, text="Max: N/A", font=ctk.CTkFont(size=20))
        self.max_value_label.place(relx=0.96, rely=0.02, anchor="ne")

        self.fps_label = ctk.CTkLabel(self.root, text=f"FPS: N/A", font=ctk.CTkFont(size=20))
        self.fps_label.place(relx=0.96, rely=0.06, anchor="ne")
        self.fps_duration = 0

        self.frequency_label = ctk.CTkLabel(self.root, text=f"Freq: {int(self.settings.get('frequency'))} Hz", font=ctk.CTkFont(size=20))
        self.frequency_label.place(relx=0.01, rely=0.02, anchor="nw")

        pipeline_cmd = (
            f"libcamera-vid -t 0 --width 4608 --height 2592 --framerate {self.framerate} "
            f"--codec yuv420 --nopreview -o - | "
            f"ffmpeg -hide_banner -loglevel warning -f rawvideo -pix_fmt yuv420p -s 4608x2592 -i - "
            f"-vf scale={self.frame_width}:{self.frame_height} "
            f"-f v4l2 /dev/video10"
        )

        self.pipeline_process = subprocess.Popen(
            pipeline_cmd,
            shell=True,
            preexec_fn=os.setsid,
            stdout=subprocess.DEVNULL
        )

        # Camera warm-up time
        time.sleep(2)

        self.video_capture = cv2.VideoCapture("/dev/video10", cv2.CAP_V4L2)
        self.video_capture.set(cv2.CAP_PROP_FPS, self.framerate)
        if not self.video_capture.isOpened():
            print("❌ Could not open /dev/video10")
            self.cleanup()
            exit()

        self.beamformer = BeamformerMap(horizonatal_fov=66, vertical_fov=41, z=0.5, increment=0.05)
        self.event_recorder = VideoEventRecorder(
            resolution=(self.frame_width, self.frame_height),
            backend_url=self.backend_url,
            api_key=self.backend_api_key,
            sound_generator=self.beamformer.mch_generator,
        )
        self.background_map_calculator = BackgroundMapCalculator(
            beamformer=self.beamformer,
            user_settings=self.settings,
            frame_width=self.frame_width,
            frame_height=self.frame_height,
            update_interval=0.1
        )
        self.background_map_calculator.start()

        self.webrtc_track = OpenCVVideoStreamTrack(self)
        self.update_frame()
        threading.Thread(target=self.start_webrtc_loop, daemon=True).start()

    def create_settings_button(self):
        gear_img = Image.open("resources/icons/settings_icon.png")
        gear_img = gear_img.resize((60, 60), Image.Resampling.LANCZOS)
        gear_photo = ctk.CTkImage(light_image=gear_img, dark_image=gear_img, size=(40, 40))

        return ctk.CTkButton(
            self.root,
            image=gear_photo,
            command=self.open_settings_window,
            text="",
            width=60,
            height=60,
            corner_radius=5
        )

    def set_root_attributes(self):
        self.root.title("Sonic Sense")
        self.root.after(1000, lambda: self.root.wm_attributes('-fullscreen', 'true'))
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.root.update_idletasks()
        self.root.bind('<Alt-F4>', self.on_close)
        self.root.bind("<Escape>", self.on_close)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_frame(self):
        start_time = time.time()
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            bf_map, bf_map_unnormalized, bf_color, db_values = self.background_map_calculator.get_latest_map()
            if bf_map is not None and bf_color is not None:
                frame = cv2.addWeighted(frame, 0.7, bf_color, 0.3, 0)
                if(self.update_count % 3 == 0):
                    self.update_max_value_label(db_values)

            image = Image.fromarray(frame)
            ctk_image = ctk.CTkImage(light_image=image, size=(self.displayed_frame_width, self.displayed_frame_height))

            self.video_label.configure(image=ctk_image, text="")
            self.video_label.image = ctk_image

            if hasattr(self, 'webrtc_track'):
                self.webrtc_track.frame = frame.copy()
            self.event_recorder.update(frame, bf_map_unnormalized, event_threshold=self.settings.get("event_sound_threshold"))

            self.fps_duration += (time.time() - start_time) + 0.06
            if self.update_count % 10 == 0:
                fps = 10 / self.fps_duration
                self.fps_duration = 0
                self.fps_label.configure(text=f"FPS: {fps:.2f}")
                self.frequency_label.configure(text=f"Freq: {int(self.settings.get('frequency'))} Hz")
            
        self.update_count += 1
        self.root.after(60, self.update_frame)

    def open_settings_window(self):
        self.settings_window = SettingsWindow(self.root, self.settings)
        self.settings_window.after(300, lambda: self.settings_window.wm_attributes('-fullscreen', 'true'))

    def update_max_value_label(self, bf_map_unnormalized):
        max_loc = cv2.minMaxLoc(bf_map_unnormalized)[3]
        max_val = bf_map_unnormalized[max_loc[1], max_loc[0]]
        map_h, map_w = bf_map_unnormalized.shape
        scaled_x = int(max_loc[0] * self.displayed_frame_width / map_w)
        scaled_y = int(max_loc[1] * self.displayed_frame_height / map_h)

        if max_val == -350.0:
            max_val = 0.0
        else:
            max_val = max(0.0, max_val - 20.0)

        self.max_value_label.configure(text=f"Max: {max_val:.2f} dB @ ({scaled_x}, {scaled_y})")

    def on_close(self):
        self.cleanup()
        self.root.destroy()

    def cleanup(self):
        print("Cleaning up...")
        self.background_map_calculator.stop()
        if self.video_capture:
            self.video_capture.release()
        os.killpg(os.getpgid(self.pipeline_process.pid), signal.SIGTERM)

    def start_webrtc_loop(self):
        asyncio.run(self.run_webrtc())

    async def run_webrtc(self):
        self.pc = self.create_peer_connection()

        async with websockets.connect(self.signaling_url) as websocket:
            print(f"\n---- CONNECTED TO SIGNALING SERVER -----\n")

            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)

            await websocket.send(json.dumps({
                "type": "offer",
                "sdp": self.pc.localDescription.sdp,
                "sdpType": self.pc.localDescription.type
            }))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_rtc_message(data, websocket)
                except Exception as e:
                    print(f"Error processing message: {e}")

    async def handle_rtc_message(self, data, websocket):
        if data["type"] == "answer":
            print(f"\n---- RECEIVED SDP ANSWER -----\n")
            answer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            await self.pc.setRemoteDescription(answer)

        elif data["type"] == "request-offer":
            print(f"\n---- RECEIVED OFFER REQUEST -----\n")
            await self.pc.close()
            self.pc = self.create_peer_connection()
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            await websocket.send(json.dumps({
                "type": "offer",
                "sdp": self.pc.localDescription.sdp,
                "sdpType": self.pc.localDescription.type
            }))

        elif data["type"] == "candidate":
            candidate_dict = data["candidate"]
            candidate = self.dict_to_candidate(candidate_dict)
            if candidate.ip:
                print(f"\n---- RECEIVED CANDIDATE -----\n")
                await self.pc.addIceCandidate(candidate)
                print(data)

    def dict_to_candidate(self, data):
        return RTCIceCandidate(
            component=data["component"],
            foundation=data["foundation"],
            ip=data["ip"],
            port=data["port"],
            priority=data["priority"],
            protocol=data["protocol"],
            type=data["type"],
            relatedAddress=data.get("relatedAddress"),
            relatedPort=data.get("relatedPort"),
            sdpMid=data["sdpMid"],      
            sdpMLineIndex=data["sdpMLineIndex"],
            tcpType=data.get("tcpType"),
        )
    
    def create_peer_connection(self):
        config = RTCConfiguration([
            RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun1.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun2.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun3.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun4.l.google.com:19302"]),
        ])
        pc = RTCPeerConnection(configuration=config)
        pc.addTrack(self.webrtc_track)
        return pc

if __name__ == "__main__":
    root = ctk.CTk()
    app = SonicSenseApp(root)
    root.mainloop()
