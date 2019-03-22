from __future__ import print_function
from time import sleep
from daqhats import mcc118, OptionFlags, HatIDs, HatError
from daqhats_utils import select_hat_device, enum_mask_to_string, \
chan_list_to_mask
from scipy import fftpack
import numpy as np

CURSOR_BACK_2 = '\x1b[2D'
ERASE_TO_END_OF_LINE = '\x1b[0K'

channels = [0]                                                          # reduced to [0] from [0, 1, 2, 3]
channel_mask = chan_list_to_mask(channels)
num_channels = len(channels)

samples_per_channel = 1000
scan_rate = 100000.0                                                    # increased to 10000.0 from 1000.0
options = OptionFlags.DEFAULT

address = select_hat_device(HatIDs.MCC_118)
hat = mcc118(address)

read_request_size = 1000 	                                      	# increased to 10000 from 500
timeout = 11.0								# increased to 11.0 from 5.0. 100k sample size /10k rate=10s. Plus 1s to buffer.

def main():
    try:
        try:
            #start scan
            hat.a_in_scan_start(channel_mask, samples_per_channel, scan_rate, options)

            #perform scan
            read_result = hat.a_in_scan_read(read_request_size, timeout)

            #check for an overrun error
            if read_result.hardware_overrun:
                print('\n\nHardware overrun\n')

            if read_result.buffer_overrun:
                print('\n\nBuffer overrun\n')

	    time_step = 1/scan_rate
	    sample_freq = fftpack.fftfreq(read_request_size, time_step)
	    sig_fft = fftpack.fft(read_result.data)


	    f = open("fftdata.txt", "w+")
	    for i in range(len(sig_fft)):
		f.write(str(read_result.data[i]) + "\r\n")
	    f.close()





	    '''f = open("datafile_100k_1000.txt", "w+")
	    for i in range(len(read_result.data)):
		f.write(str(read_result.data[i]) + "\r\n")
	    f.close()

            print(read_result.data)
	    print("\nNumber of data points: " + str(len(read_result.data)))
	    print("Actual scan rate: " + str(hat.a_in_scan_actual_rate(num_channels, scan_rate)))'''





            sleep(0.1)
            print('\n')

        except KeyboardInterrupt:
            # Clear the '^C' from the display
            print(CURSOR_BACK_2, ERASE_TO_END_OF_LINE, '\n')

    except (HatError, ValueError) as err:
        print('\n', err)

if __name__ == '__main__':
    main()
