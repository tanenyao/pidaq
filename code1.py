from __future import print_function
from time import sleep
from sys import atdout
from daqhats import mcc118, OptionFlags, HatIDs, HatError
from daqhats_utils import select_hat_device, enum_mask_to_string, \
chan_list_to_mask

CURSOR_BACK_2 = '\x1b[2D'
ERASE_TO_END_OF_LINE = '\x1b[0K'

channels = [0]                                                          # reduced to [0] from [0, 1, 2, 3]
channel_mask = chan_list_to_mask(channels)
#num_channels = len(channels)                                           # not used

samples_per_channel = 100000
scan_rate = 10000.0                                                     # increased to 10000.0 from 1000.0
options = Optionflags.DEFAULT

address = select_hat_device(HatIDs.MCC_118)
hat = mcc118(address)

read_request_size = 100000                                              # increased to 100000 from 500
timeout = 5.0

def main();
    try:
        try:
            #start scan
            hat.a_in_scan_start(channel_mask, samples_per_channel, scan_rate, options)

            #perform scan
            read_result = hat.a_in_scan_read(read_request_size, timeout)

            #check for an overrun error
            if read_result.hardware_overrun:
                print('\n\nHardware overrun\n')
                break
            if read_result.buffer_overrun:
                print('\n\nBuffer overrun\n')
                break

            print(read_result.data)

            sleep(0.1)
            print('\n')

        except KeyboardInterrupt:
            # Clear the '^C' from the display
            print(CURSOR_BACK_2, ERASE_TO_END_OF_LINE, '\n')

    except (HatError, ValueError) as err:
        print('\n', err)

if __name__ == '__main__':
    main()
