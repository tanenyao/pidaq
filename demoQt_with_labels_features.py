from daqhats import mcc118, OptionFlags, HatIDs, HatError
from daqhats_utils import select_hat_device, enum_mask_to_string, \
chan_list_to_mask
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from scipy.fftpack import fft

import sys
import time
import peakutils

class AudioStream(object):
    def __init__(self):

	self.sample_size = 1024
	self.wf_upp_ylim = 2
	self.wf_low_ylim = 0

	self.rate = 10000

        # pyqtgraph stuff
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title='Spectrum Analyzer')
        self.win.setWindowTitle('Spectrum Analyzer')
        self.win.setGeometry(5, 115, 1910, 1070)

        wf_xlabels = [(0, '0'), (self.sample_size/2, str(self.sample_size/2)), (self.sample_size, str(self.sample_size))]
        wf_xaxis = pg.AxisItem(orientation='bottom')
        wf_xaxis.setTicks([wf_xlabels])

        wf_ylabels = [(0, '0'), (self.wf_upp_ylim, str(self.wf_upp_ylim)), (self.wf_low_ylim, str(self.wf_low_ylim))]
        wf_yaxis = pg.AxisItem(orientation='left')
        wf_yaxis.setTicks([wf_ylabels])

        #sp_xlabels = [
        #    (np.log10(10), '10'), (np.log10(100), '100'),
        #    (np.log10(1000), '1000'), (np.log10(22050), '22050')
        #]
        sp_xlabels = [(0, '0'), (self.rate/4, str(self.rate/4)), (self.rate/2, str(self.rate/2))]
        sp_xaxis = pg.AxisItem(orientation='bottom')
        sp_xaxis.setTicks([sp_xlabels])

        self.waveform = self.win.addPlot(
            title='WAVEFORM', row=1, col=1, axisItems={'bottom': wf_xaxis, 'left': wf_yaxis},
        )
        self.spectrum = self.win.addPlot(
            title='SPECTRUM', row=2, col=1, axisItems={'bottom': sp_xaxis},
        )

        # pyaudio stuff
        #self.FORMAT = pyaudio.paInt16
        #self.CHANNELS = 1
        #self.RATE = 44100
        #self.CHUNK = 1024 * 2
	self.channels = [0]
	self.channel_mask = chan_list_to_mask(self.channels)
	self.options = OptionFlags.DEFAULT

	self.request = self.sample_size
	self.timeout = 11

        #self.p = pyaudio.PyAudio()
        #self.stream = self.p.open(
        #    format=self.FORMAT,
        #    channels=self.CHANNELS,
        #    rate=self.RATE,
        #    input=True,
        #    output=True,
        #    frames_per_buffer=self.CHUNK,
        #)
        # waveform and spectrum x points
	self.address = select_hat_device(HatIDs.MCC_118)
	self.hat = mcc118(self.address)

	#self.x = np.arange(0, 2 * self.CHUNK, 2)
        #self.f = np.linspace(0, self.RATE / 2, self.CHUNK / 2)
	self.x = np.arange(0, self.sample_size)
        self.f = np.linspace(0, self.rate, self.sample_size)

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                self.traces[name] = self.waveform.plot(pen='c', width=3)
                self.waveform.setYRange(-2, 2, padding=0)
                self.waveform.setXRange(0, self.sample_size, padding=0.005)
            if name == 'spectrum':
                self.traces[name] = self.spectrum.plot(pen='m', width=3)
                #self.spectrum.setLogMode(x=True, y=True)
                self.spectrum.setYRange(0, 1, padding=0)
                #self.spectrum.setXRange(
                #    np.log10(20), np.log10(self.RATE / 2), padding=0.005)
                self.spectrum.setXRange(0, self.rate / 2, padding=0.005)

    def update(self):
	self.hat.a_in_scan_start(self.channel_mask, self.sample_size, self.rate, self.options)
        wf_data = self.hat.a_in_scan_read(self.request, self.timeout)
	self.hat.a_in_scan_cleanup()

	# eliminates error whereby len(wf_data.data)=0 probably due to the high refresh rate
	if len(wf_data.data) == self.sample_size:
	        wf_data = np.array(wf_data.data)
	        self.set_plotdata(name='waveform', data_x=self.x, data_y=wf_data)

	        sp_data = fft(np.array(wf_data))
	        sp_data = np.abs(sp_data[0:self.sample_size]
	                         ) * 2 / (0.6 * self.sample_size)
	        self.set_plotdata(name='spectrum', data_x=self.f, data_y=sp_data)

		indexes = peakutils.indexes(sp_data, thres = 0.02/max(sp_data), min_dist= 100)
		indexes = np.array(indexes)

		# calculates waveform rms
		rms = round(np.sqrt(np.mean(wf_data**2)), 2)

		# calculates waveform max, min
		max_value = round(max(wf_data), 2)
		min_value = round(min(wf_data), 2)

		print("Number of data points: " + str(wf_data.size))
		print("RMS: " + str(rms) + "V")
		print("Max: " + str(max_value) + "V")
		print("Min: " + str(min_value) + "V")

		# calculates spectrum peak frequencies
		#l = []
		#f_range = 10
		#if len(indexes) != 0:
		#	for i in indexes:
		#		t = ((),)
		#		x = i.item() / float(self.sample_size) * self.rate
		#		t = (round(x - f_range,2), round(x + f_range, 2))
		#		l.append(t)
		#	print("Frequencies: {}".format(l[:len(l)/2]))

		# calculates spectrum peak frequencies
		fl = []
		f_range = 10
		pl = []
		xl = []
		yl = []
		if len(indexes) != 0:
			for i in indexes:
				f_val = ((),)
				x = i.item() / float(self.sample_size) * self.rate
				f_val = (round(x - f_range,2), round(x + f_range, 2))
				fl.append(f_val)
				pl.append(self.p_range(x, 0.03))
				xl.append(x)
				yl.append(sp_data[i])
			print("Peak frequencies in     % range: {}".format(pl[:len(pl)/2]))
			print("Peak frequencies in fixed range: {}".format(fl[:len(fl)/2]))
			print("Peak frequencies               : {}".format(xl[:len(xl)/2]))
			print("Peak frequencies y coordinates:: {}".format(yl[:len(yl)/2]))

		else:
			print("Peak frequencies in     % range: None")
			print("Peak frequencies in fixed range: None")
			print("Peak frequencies               : None")
			print("Peak frequencies y coordinates:: None")

		print("\n")

    def p_range(self, x, y):
	return (round(x-x*y,2), round(x+x*y,2))

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(30)
        self.start()


if __name__ == '__main__':

    audio_app = AudioStream()
    audio_app.animation()
