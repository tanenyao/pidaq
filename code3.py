from daqhats import mcc118, OptionFlags, HatIDs, HatError
from daqhats_utils import select_hat_device, enum_mask_to_string, \
chan_list_to_mask
import numpy as np
import matplotlib.pyplot as plt
import time
from scipy.fftpack import fft
from Tkinter import TclError

# constants
channels = [0]
channel_mask = chan_list_to_mask(channels)
sample_size = 1000
rate = 100000
options = OptionFlags.DEFAULT

request = sample_size
timeout = 11

# mcc118 class instance
address = select_hat_device(HatIDs.MCC_118)
hat = mcc118(address)

# create matplotlib figure
fig, (ax, ax2) = plt.subplots(2, figsize=(15, 8))

# variable for plotting
x = np.arange(0, sample_size)
x_fft = np.linspace(0, rate, sample_size)

# create line object with random data
line, = ax.plot(x, np.random.rand(sample_size))
line_fft, = ax2.plot(x_fft, np.random.rand(sample_size))

# basic formatting for the axes
ax.set_label('AUDIO WAVEFORM')
ax.set_xlabel('samples')
ax.set_ylabel('voltage')
ax.set_ylim(1.4, 2)
ax.set_xlim(0, sample_size)

ax2.set_xlim(20, rate)

# for measuring frame rate
frame_count = 0
start_time = time.time()

while True:
	hat.a_in_scan_start(channel_mask, sample_size, rate, options)
	read_result = hat.a_in_scan_read(request, timeout)
	hat.a_in_scan_cleanup()
	data = np.array(read_result.data)
	line.set_ydata(data)
	y_fft = fft(data)
	line_fft.set_ydata(np.abs(y_fft[:sample_size] * 2 / (0.6 * sample_size)))

	try:
		fig.canvas.draw()
		fig.canvas.flush_events()
		fig.show()

	except TclError:
		frame_rate = frame_count / (time.time() - start_time)
		print('average frame rate = {:.0f} FPS'.format(frame_rate))
