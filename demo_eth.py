
delay = 0.01

while True:

	try:

		# start time
		import time
		t = time.time()

		'''-------------------------------------------------------M C C 1 1 8   S C A N-----------------------------------------------------'''

		from daqhats import mcc118, OptionFlags, HatIDs, HatError
		from daqhats_utils import select_hat_device, chan_list_to_mask

		address = select_hat_device(HatIDs.MCC_118)
		hat = mcc118(address)

		channels = [0]
		channel_mask = chan_list_to_mask(channels)
		sample_size = 2048
		rate = 10000
		options = OptionFlags.DEFAULT

		request = sample_size
		timeout = 3

		hat.a_in_scan_start(channel_mask, sample_size, rate, options)
		raw = hat.a_in_scan_read(request, timeout)
		hat.a_in_scan_cleanup()

		if len(raw.data) == sample_size:

			'''----------------------------------------------F F T /  F F T   P E A K S-------------------------------------------------'''

			import numpy as np
			import peakutils
			from scipy.fftpack import fft

		        raw = np.array(raw.data)

			fft_data = fft(raw)
			fft_data = np.abs(fft_data[0:sample_size]) * 2 / (0.6 * sample_size)
			fft_data = fft_data[:len(fft_data)/2]

			peak_index = peakutils.indexes(fft_data, thres=0.02 / max(fft_data), min_dist=20)
			peak_index = np.array(peak_index)

			'''---------------------------------------R M S , M A X , M I N , P E A K   V A L S------------------------------------------'''

			ratio = 0.03

			rms_val = round(np.sqrt(np.mean(raw**2)), 2)
			max_val = round(max(raw), 2)
			min_val = round(min(raw), 2)

			peak_x, peak_y, peak_range = [], [], []

			for i in peak_index:
				peak = i.item() / float(sample_size) * rate
				peak_x.append(peak)
				peak_y.append(round(fft_data[i],2))
				peak_range.append(round(peak-peak*ratio,2))
				peak_range.append(round(peak+peak*ratio,2))

			'''---------------------------------------------------------F T P------------------------------------------------------------'''

			import csv
			import ftplib

			def csv_add(filename, list):
				csv_file = open(filename, 'w')
				for e in list:
					writer = csv.writer(csv_file)
					writer.writerow(e)
				csv_file.close()

			def ftp_upload(server_ip, user, passwd, filename):
				session = ftplib.FTP(server_ip, user, passwd)
				file = open(filename, 'rb')
				session.storbinary("STOR " + filename, file)
				file.close()
				session.quit()

			filename = 'demo.csv'
			features = [[rms_val], [max_val], [min_val], peak_x, peak_y, peak_range]
			csv_add(filename, features)

			ip_addr = '169.254.111.227'
			usr = 'watts'
			passwd = 'Parzival'
			ftp_upload(ip_addr, usr, passwd, filename)

			'''---------------------------------------------------------M Q T T--------------------------------------------------------------

			import paho.mqtt.publish as publish

			localhost = "localhost"
			topic = "Sensors/RaspberryPi02/GRAS/40PH"

			placeholder = [rms_val, max_val, min_val, peak_x, peak_y, peak_range]
			placeholder = tuple([str(e) for e in placeholder])
			payload = '{"RMS": "%s", "Max": "%s", "Min": "%s", "Peak X": "%s", "Peak Y": "%s", "Peak Range": "%s"}' % placeholder

			publish.single(topic, payload, qos=2, hostname=localhost)

			------------------------------------------------------------------------------------------------------------------------------'''

			# end time
			elapsed = time.time() - t
			print 'Elapsed time: ' + str(round(elapsed,3)) + 's' + '\n'

		time.sleep(delay)

	except Exception, e:
		print '*Error*  ' + str(e) + '\n'

		time.sleep(delay)

	except KeyboardInterrupt:
		hat.a_in_scan_cleanup()

		# clears ^C from display
		CURSOR_BACK_2 = '\x1b[2D'
		ERASE_TO_END_OF_LINE = '\x1b[0K'
		print CURSOR_BACK_2 + ERASE_TO_END_OF_LINE + 'Interrupted'

		break
