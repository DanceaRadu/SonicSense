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

    async def recv(self):
        print(self.frame)
        print(f"\n---- SENDING WEBRTC FRAME -----\n")
        if(self.frame is None):
            return
        
        pts, time_base = await self.next_timestamp()

        frame = VideoFrame.from_ndarray(self.frame, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base

        # await asyncio.sleep(0.01)
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
