from acoular import SoundDeviceSamplesGenerator
from collections import deque
import threading
import sounddevice as sd
from traits.api import HasPrivateTraits
import numpy as np

class SharedBufferSamplesGenerator(SoundDeviceSamplesGenerator, HasPrivateTraits):
    def __init__(self, *args, buffer_blocks=100, buffer_block_size=1024, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer = deque(maxlen=buffer_blocks)
        self._buffer_block_size = buffer_block_size

        self.stream = sd.InputStream(
            device=self.device,
            channels=self.num_channels,
            clip_off=True,
            samplerate=self.sample_freq,
            dtype=self.precision,
            blocksize=self._buffer_block_size,
        )
        self.stream.start()

        self._lock = threading.Lock()
        self._thread_running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def _stream_loop(self):
        try:
            while self._thread_running:
                data, overflow = self.stream.read(self._buffer_block_size)
                self.overflow = overflow
                with self._lock:
                    self._buffer.append(data.copy())
        except Exception as e:
            print(f"[Stream thread error] {e}")
        finally:
            self._thread_running = False

    def result(self, num):
        if num != self._buffer_block_size:
            raise ValueError(
                f"Requested block size ({num}) must match buffer_block_size ({self._buffer_block_size})"
            )

        self.running = True

        with self._lock:
            if self._buffer:
                yield self._buffer[-1].copy()
            else:
                yield np.zeros((num, self.num_channels), dtype=self.precision)

        self.running = False
