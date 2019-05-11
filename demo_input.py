# ensure variable name is  'peak + number' e.g. 'peak1', and range more than 100
# e.g.
# peak1, 500, 600
# peak2, 800, 900

# fftpack.helper.next_fast_len() has little effect

import ftplib
import csv

from daqhats import mcc118, OptionFlags, HatIDs, HatError
from daqhats_utils import select_hat_device, chan_list_to_mask
import numpy as np
from scipy import fftpack

from datetime import datetime
import time

def ftp_in(filename, ip_addr, user, passwd):
	ftp = ftplib.FTP(ip_addr, user, passwd)
	file = open(filename, 'wb')
	ftp.retrbinary('RETR ' + filename, file.write)
	file.close
	ftp.quit()

def dftp_in(filename, ip_addr, port, dir):
	session = ftplib.FTP()
	session.connect(ip_addr, port)
	session.login()
	session.cwd(dir)
	file = open(filename, 'wb')
	session.retrbinary('RETR ' + filename, file.write)
	file.close()
	session.quit()

def readfile(filename):
	reader = csv.reader(open(filename, 'r'))
	return [l for l in reader]

def single_channel_scan(channel=0):
	global size
	global rate

	address = select_hat_device(HatIDs.MCC_118)
	hat = mcc118(address)

	channels = [channel]
	channel_mask = chan_list_to_mask(channels)
	options = OptionFlags.DEFAULT

	hat.a_in_scan_start(channel_mask, size, rate, options)					# size, rate
	raw = hat.a_in_scan_read(size, size/rate+1)						# size, rate
	hat.a_in_scan_cleanup()

	raw_data = np.array(raw.data)
	fft_data = fftpack.fft(raw_data)
	fft_data = np.abs(fft_data[0:size]) * 2 / (0.6 * size)
	fft_data = fft_data[:len(fft_data)/2]

	return raw_data, fft_data

def indexof(hz):
	global size
	global rate

	return hz * size / rate									# size, rate

def format(val, code):
	global list
	global machine

	dt = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
	list.append([dt, machine, code, str(val)])

def output(input):
	global raw_data
	global fft_data

	if input[0] == 'rms':
		format(round(np.sqrt(np.mean(raw_data**2)), 4), '100')					# raw_data
	if input[0] == 'max':
		format(round(max(raw_data)), '101')							# raw_data
	if input[0] == 'min':
		format(round(min(raw_data)), '102')							# raw_data

	for i in range(1,11):
		if input[0] == 'peak' + str(i):
			if i < 10:
				format(round(max(fft_data[indexof(int(input[1])):indexof(int(input[2]))]), 4), '10'+str(i+2))	# fft_data
			else:
				format(round(max(fft_data[indexof(int(input[1])):indexof(int(input[2]))]), 4), '1'+str(i+2))	# fft_data


def writefile(filename, input):
	file = open(filename, 'w')
	for e in input:
		write = csv.writer(file)
		write.writerow(e)
	file.close()

def ftp_out(filename, ip_addr, user, passwd):
	ftp = ftplib.FTP(ip_addr, user, passwd)
	file = open(filename, 'rb')
	ftp.storbinary('STOR ' + filename, file)
	file.close
	ftp.quit()

def dftp_out(filename, ip_addr, port, dir):
	session = ftplib.FTP()
	session.connect(ip_addr, port)
	session.login()
	session.cwd(dir)
	file = open(filename, 'rb')
	session.storbinary('STOR ' + filename, file)
	file.close()
	session.quit()

start = time.time()

# get config file (local)
ftp_in('config.csv', '192.168.1.2', 'watts', 'Parzival')

# get config file (demo)
#dftp_in('config.csv', '192.168.1.101', '2121', 'mic-data')

# get parameters
params = readfile('config.csv')

# perform scan
size, rate = int(params[0][0]), int(params[1][0])
raw_data, fft_data = single_channel_scan()

machine = 'Machine 1'
list = []

# format output list
for i in range(2, len(params)):
	output(params[i])

# convert list to csv
writefile('output.csv', list)

# upload output file (local)
ftp_out('output.csv', '192.168.1.2', 'watts', 'Parzival')

# upload output file (demo)
#dftp_out('output.csv', '192.168.1.101', '2121', 'mic-data')

print('Scan Completed in ' + str(time.time() - start) + 's')
