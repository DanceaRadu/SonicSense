import numpy as np
from aiortc.contrib.media import MediaStreamTrack
import asyncio
from av import VideoFrame
import time
import fractions

class OpenCVVideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.frame = None
        self.start = time.time()
        self.timestamp = 0
        self.time_base = fractions.Fraction(1, 90000)  # 90kHz clock rate
        self.frame_interval = 1 / 30  # target ~30 fps

    async def recv(self):
        print(self.frame)

        if self.frame is None:
            await asyncio.sleep(self.frame_interval)
            return

        await asyncio.sleep(self.frame_interval)

        frame = VideoFrame.from_ndarray(self.frame, format="bgr24")

        self.timestamp += int(self.frame_interval * 90000)
        frame.pts = self.timestamp
        frame.time_base = self.time_base

        return frame


class DummyVideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.counter = 0
        self.start = time.time()
        self.timestamp = 0
        self.time_base = fractions.Fraction(1, 90000)

    async def recv(self):
        await asyncio.sleep(1 / 30)

        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:, :] = (self.counter % 255, 100, 100)
        self.counter += 1

        frame = VideoFrame.from_ndarray(img, format="bgr24")

        self.timestamp += 3000
        frame.pts = self.timestamp
        frame.time_base = self.time_base

        return frame
