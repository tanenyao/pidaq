from daqhats import mcc118, OptionFlags, HatIDs, HatError
from daqhats_utils import select_hat_device, enum_mask_to_string, \
chan_list_to_mask
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from scipy.fftpack import fft

import sys
import time


class AudioStream(object):
    def __init__(self):

        # pyqtgraph stuff
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title='Spectrum Analyzer')
        self.win.setWindowTitle('Spectrum Analyzer')
        self.win.setGeometry(5, 115, 1910, 1070)

        wf_xlabels = [(0, '0'), (2048, '2048'), (4096, '4096')]
        wf_xaxis = pg.AxisItem(orientation='bottom')
        wf_xaxis.setTicks([wf_xlabels])

        wf_ylabels = [(0, '0'), (127, '128'), (255, '255')]
        wf_yaxis = pg.AxisItem(orientation='left')
        wf_yaxis.setTicks([wf_ylabels])

        sp_xlabels = [
            (np.log10(10), '10'), (np.log10(100), '100'),
            (np.log10(1000), '1000'), (np.log10(22050), '22050')
        ]
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
	self.sample_size = 1000
	self.rate = 10000
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

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(30)
        self.start()


if __name__ == '__main__':

    audio_app = AudioStream()
    audio_app.animation()
