
import time, signal, sys
from Adafruit_ADS1x15 import ADS1x15
import datetime
import psycopg2
import numpy as np
from math import pow

#con = psycopg2.connect(database='weather', user='alex')
#cur = con.cursor()

ADS1015 = 0x00  # 12-bit ADC

# Select the gain
# gain = 61    # +/- 6.144V
#gain = 4096  # +/- 4.096V
# gain = 2048  # +/- 2.048V
gain = 1024  # +/- 1.024V
#gain = 512   # +/- 0.512V
# gain = 256   # +/- 0.256V

# Select the sample rate
sps = 8    # 8 samples per second
# sps = 16   # 16 samples per second
# sps = 32   # 32 samples per second
# sps = 64   # 64 samples per second
# sps = 128  # 128 samples per second
# sps = 250  # 250 samples per second
# sps = 475  # 475 samples per second
# sps = 860  # 860 samples per second

# Initialise the ADC using the default mode (use default I2C address)
# Set this to ADS1015 or ADS1115 depending on the ADC you are using!
adc = ADS1x15(ic=ADS1015)

# Read channel 0 in single-ended mode using the settings above
voltsa = adc.readADCSingleEnded(1, gain, sps) / 1000
voltsb = adc.readADCSingleEnded(2, gain, sps) / 1000

valuesa = np.array([])
valuesb = np.array([])

insert = 0
now=datetime.datetime.now()

while True:
	try:
		while now.minute%10.0 <> 0 or insert == 1:
			time.sleep(15)
			voltsa = adc.readADCSingleEnded(1, gain, sps) / 1000
			voltsb = adc.readADCSingleEnded(2, gain, sps) / 1000
			if voltsa < 0.3 and voltsb < 0.3:
				valuesa = np.append(valuesa,voltsa)
				valuesb = np.append(valuesb,voltsb)
			now=datetime.datetime.now()
			if insert == 1 and now.minute%10.0 <> 0:
				insert = 0
		va = np.mean(valuesa)
		vb = np.mean(valuesb)
		con = psycopg2.connect(host='10.0.0.247', database='weather', user='met', password='metp@ss')
		cur = con.cursor()
		cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 14, %s)' % (35066*pow(va,3)-6050.6*pow(va,2)+4189.6*va))
		cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 15, %s)' % (20816*pow(va,3)-9318.2*pow(va,2)+5359.4*va))
		#cur.execute('insert into stationdata values (round_10min(localtimestamp + interval \'1 second\'), 16, %s)' % (va))
		#cur.execute('insert into stationdata values (round_10min(localtimestamp + interval \'1 second\'), 17, %s)' % (vb))
		con.commit()
		con.close()
		valuesa = np.array([])
		valuesb = np.array([])
		insert = 1
		now=datetime.datetime.now()
	except KeyboardInterrupt:
		raise
