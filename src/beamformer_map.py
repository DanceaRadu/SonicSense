from acoular import (
    SoundDeviceSamplesGenerator, MicGeom, RectGrid,
    BeamformerBase, PowerSpectra, SteeringVector, RFFT, FFTSpectra
)
import numpy as np

class BeamformerMap:
    def __init__(self, mic_file='resources/array_16.xml', 
                 freq=1000, increment=0.02,
                 x_min=-0.5, x_max=0.5, y_min=-0.5, y_max=0.5,
                 z=0.5, bandwidth=3):
        
        self.freq = freq
        self.bandwidth = bandwidth

        self.mic_array = MicGeom(file=mic_file)
        self.mic_grid = RectGrid(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, z=z, increment=increment)

        self.x_vals = np.arange(self.mic_grid.x_min, self.mic_grid.x_max + self.mic_grid.increment, self.mic_grid.increment)
        self.y_vals = np.arange(self.mic_grid.y_min, self.mic_grid.y_max + self.mic_grid.increment, self.mic_grid.increment)

        self.steeringVector = SteeringVector(grid=self.mic_grid, mics=self.mic_array)


    def get_current_map(self):
        try:
            mch_generator = SoundDeviceSamplesGenerator(
                device=0,
                num_channels=16,
                sample_freq=48000,
                precision='int16',
                numsamples=1024
            )

            ps = PowerSpectra(source=mch_generator, block_size=1024, window='Hanning', cached=False)
            bf = BeamformerBase(freq_data=ps, steer=self.steeringVector, cached=False)

            bf_map = bf.synthetic(self.freq, self.bandwidth)
            return bf_map.reshape(len(self.y_vals), len(self.x_vals))

        except Exception as e:
            print(f"Beamformer error: {e}")
            return np.zeros((len(self.y_vals), len(self.x_vals)))
