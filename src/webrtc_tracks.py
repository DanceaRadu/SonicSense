from aiortc.contrib.media import MediaStreamTrack
import asyncio
from av import VideoFrame

class OpenCVVideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.frame = None

    async def recv(self):
        print("heeeeeeeeeeeeeeeeeeeeeeeellllllllllllllllllllllllo222")
        print(self.frame)
        if(self.frame is None):
            return
        
        pts, time_base = await self.next_timestamp()
        print("")
        print("")
        print("")
        print("heeeeeeeeeeeeeeeeeeeeeeeellllllllllllllllllllllllo")
        print("")
        print("")
        print("")

        print("-Sending WebRTC frame-")
        frame = VideoFrame.from_ndarray(self.frame, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base
        await asyncio.sleep(0.01)
        return frame

import numpy as np
from aiortc.contrib.media import MediaStreamTrack
from av import VideoFrame
import asyncio

class DummyVideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.counter = 0

    async def recv(self):
        print("heeeeeeeeeeeeeeeeeeeeeeeellllllllllllllllllllllllo")
        pts, time_base = await self.next_timestamp()

        # Create a dummy moving pattern
        height, width = 480, 640
        frame_data = np.zeros((height, width, 3), dtype=np.uint8)
        color = (self.counter % 255, (self.counter * 2) % 255, (self.counter * 3) % 255)
        frame_data[:] = color
        self.counter += 1

        # Create video frame
        frame = VideoFrame.from_ndarray(frame_data, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base

        await asyncio.sleep(1 / 30)  # Simulate 30fps
        return frame
