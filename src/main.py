from acoular import (
    SoundDeviceSamplesGenerator, MicGeom, RectGrid,
    BeamformerBase, PowerSpectra, SteeringVector, RFFT, FFTSpectra
)
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

mic_array =  MicGeom(file='resources/array_16.xml')
mic_grid = RectGrid(x_min=-0.25, x_max=0.25, y_min=-0.25, y_max=0.25, z=0.3, increment=0.01)

# Manually create x and y axis based on grid config
x_vals = np.arange(mic_grid.x_min, mic_grid.x_max + mic_grid.increment, mic_grid.increment)
y_vals = np.arange(mic_grid.y_min, mic_grid.y_max + mic_grid.increment, mic_grid.increment)
x_mesh, y_mesh = np.meshgrid(x_vals, y_vals)

# Set up live plot
fig, ax = plt.subplots()
initial_data = np.zeros_like(x_mesh)
img = ax.imshow(initial_data, extent=[x_vals[0], x_vals[-1], y_vals[0], y_vals[-1]],
                origin='lower', vmin=0, vmax=1, aspect='auto')
cbar = plt.colorbar(img, ax=ax)
cbar.set_label("Beamformer Output")
ax.set_title("Live Sound Source Localization")
ax.set_xlabel("X [m]")
ax.set_ylabel("Y [m]")

# Update function for animation
def update(frame):
    global prev_map
    try:
        mch_generator = SoundDeviceSamplesGenerator(
            device=0,
            num_channels=16,
            sample_freq=48000,
            precision='int16',
            numsamples=1024
        )
        ps = PowerSpectra(source=mch_generator, block_size=1024, window='Hanning', cached=False)
        st = SteeringVector(grid=mic_grid, mics=mic_array)
        bf = BeamformerBase(freq_data=ps, steer=st, cached=False)
        bf_map = bf.synthetic(500, 3)
        bf_map = bf_map.reshape(len(y_vals), len(x_vals))
   
        img.set_data(bf_map)
        img.set_clim(vmin=np.min(bf_map), vmax=np.max(bf_map))
    except Exception as e:
        print(f"Update error: {e}")

# Run animation
ani = FuncAnimation(fig, update, interval=20, blit=False, cache_frame_data=False, repeat=False)
plt.show()
