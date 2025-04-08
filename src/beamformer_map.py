from acoular import (
    SoundDeviceSamplesGenerator, MicGeom, RectGrid,
    BeamformerBase, PowerSpectra, SteeringVector, RFFT, FFTSpectra, BeamformerCapon
)
from utils.helper_service import HelperService
import numpy as np

class BeamformerMap:
    def __init__(self, horizonatal_fov, vertical_fov, z,
                 mic_file='resources/array_16.xml', increment=0.01):

        self.mic_array = MicGeom(file=mic_file)
        self.mic_grid = HelperService.getRectGridBasedOnCameraFOV(
            horizontal_fov=horizonatal_fov, vertical_fov=vertical_fov,
            z=z,
            increment=increment
        )

        self.steeringVector = SteeringVector(grid=self.mic_grid, mics=self.mic_array)


    def get_current_map(self, threshold, frequency=1000, bandwidth=1):
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

            bf_map = bf.synthetic(frequency, bandwidth)
            bf_map[bf_map < threshold] = 0
            return bf_map.reshape(self.mic_grid.nxsteps, self.mic_grid.nysteps)

        except Exception as e:
            print(f"Beamformer error: {e}")
            return np.zeros((self.mic_grid.nxsteps, self.mic_grid.nysteps))
