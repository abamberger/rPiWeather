
import time, signal, sys

import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

import datetime
import psycopg2
import numpy as np
from math import pow

import secrets

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 1
chan1 = AnalogIn(ads, ADS.P1)
# Create single-ended input on channel 2
chan2 = AnalogIn(ads, ADS.P2)

valuesa = np.array([])
valuesb = np.array([])

insert = 0
now=datetime.datetime.now()

while True:
	try:
		while now.minute%10.0 != 0 or insert == 1:
			time.sleep(15)
			voltsa = chan1.voltage
			voltsb = chan2.voltage
			if voltsa < 0.3 and voltsb < 0.3:
				valuesa = np.append(valuesa,voltsa)
				valuesb = np.append(valuesb,voltsb)
			now=datetime.datetime.now()
			if insert == 1 and now.minute%10.0 != 0:
				insert = 0
		va = np.mean(valuesa)
		vb = np.mean(valuesb)
		con = psycopg2.connect(host=secrets.host, database=secrets.database, user=secrets.user, password=secrets.password)
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
