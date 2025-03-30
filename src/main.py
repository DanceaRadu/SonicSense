from acoular import (
    SoundDeviceSamplesGenerator, MicGeom, RectGrid,
    BeamformerBase, PowerSpectra, SteeringVector, TimeSamples
)
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

mch_generator = SoundDeviceSamplesGenerator(
    device=0,
    num_channels=16,
    sample_freq=48000,
    precision='int16'
)

mic_array =  MicGeom(file='resources/array_16.xml')
mic_grid = RectGrid(x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=0.3, increment=0.01)
ps = PowerSpectra(source=mch_generator, block_size=1024, window='Hanning', cached=True)
st = SteeringVector(grid=mic_grid, mics=mic_array)
bf = BeamformerBase(freq_data=ps, steer=st)

result = bf.synthetic(4125)  # Initialize the beamformer
print(result)

# # Grid info
# nx, ny = mic_grid.shape
# x_vals = np.linspace(mic_grid.x_min, mic_grid.x_max, nx)
# y_vals = np.linspace(mic_grid.y_min, mic_grid.y_max, ny)

# # Set up the plot
# fig, ax = plt.subplots()
# im = ax.imshow(np.zeros((ny, nx)), extent=(mic_grid.x_min, mic_grid.x_max, mic_grid.y_min, mic_grid.y_max),
#                origin='lower', cmap='inferno')
# ax.set_title("Real-time Sound Source Localization")
# ax.set_xlabel("X [m]")
# ax.set_ylabel("Y [m]")
# fig.colorbar(im, ax=ax)

# # Beamforming data generator
# def data_gen():
#     while True:
#         try:
#             bf_map = bf.synthetic(4125)
#             yield bf_map.reshape(ny, nx)
#         except Exception as e:
#             print("Beamforming error:", e)
#             yield np.zeros((ny, nx))  # Keep GUI alive

# data_stream = data_gen()

# # Update function
# def update(frame):
#     print(f"Frame: {frame}")
#     bf_reshaped = next(data_stream)
#     im.set_data(bf_reshaped)
#     im.set_clim(vmin=np.min(bf_reshaped), vmax=np.max(bf_reshaped))
#     return [im]

# # Start animation
# ani = FuncAnimation(fig, update, interval=200, blit=True, save_count=200)
# plt.show()
